#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import descriptions
import registry
import models
import typed
import frame
import traceback
from copy import deepcopy

"""
Classes and functions relating to extracting (pulling) data from the debugee
"""

class Pull(typed.Typed):

    _stdLibChecker = re.compile("^std::.*")
    _updateTracker = set()
    _updatedNames = set()
    _watchers = dict()

    _execution = models.Execution()
    _execution.save()

    @property
    def description(self):
        return self._description

    @property
    def object(self):
        return self._object

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    @property
    def children(self):
        return self._children

    @property
    def range(self):
        return self._range

    @property
    def target_type(self):
        return self._target_type

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    @property
    def execution(self):
        return self._execution

    @property
    def dynamic_type(self):
        return self._dynamic_type

    @property
    def unaliased_type(self):
        return self._unaliased_type

    def __init__(self, description):
        self._description = description
        # self._object = self.description.object
        self._index = None
        self._name = self.description.name
        self._children = []
        self._range = (0, 1)
        self._target_type = None
        self._value = None
        self._frame = None
        self._execution = Pull._execution
        self._type = None
        self._dynamic_type = None
        self._unaliased_type = None
        self._relativeName = None
        self._frame = None

    @classmethod
    def get_true_type_name(cls, t, nameDecorators = ""):
        if t.code == gdb.TYPE_CODE_PTR:
            return cls.get_true_type_name(t.target(), nameDecorators + "*")
        elif t.code == gdb.TYPE_CODE_ARRAY:
            length = str(t.range()[1] - t.range()[0] + 1)
            return cls.get_true_type_name(t.target(), nameDecorators + "[" + length + "]")
        else:
            if isinstance(t.name, str):
                return t.name + nameDecorators
            else:
                return "<## unknown type ##>"

    def extract_extra_type_info(self):
        strip = self.object.type.strip_typedefs()
        return (strip.name, self.object.dynamic_type)

    def pull(self):
        if self._basic_pull():
            self._pull()
            ## TODO: enable memory watchers
            # self._watchers[self.index] = MemoryWatcher(self)

    def save(self, update=True):
        if update:
            self.pull()

        for child in self.children:
            child.save(update=update)

        doc = models.Memory(
            address=str(self.index),
            name=str(self.name),
            frame=str(self.frame),
            execution=self.execution,
            type=str(self.type),
            dynamic_type=str(self.dynamic_type),
            unaliased_type=str(self.unaliased_type),
            range_start=int(self.range[0]),
            range_end=int(self.range[1]),
            children=self.children
        )
        doc.save()


    def _basic_pull(self):
        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if (self.index is None) or (self.index == "?"):
            return False

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)
            return True
        else:
            return False

    # def update(self):
    #     self._clear_updated()
    #     self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.address)

    @staticmethod
    def factory(description):
        s = description.object
        standardLib = Pull._stdLibChecker.match(
            Pull.get_true_type_name(s.type))
        # TODO: Find a way to avoid modifing the description.
        # This should not be needed at all!
        # description._address = str(s.address)
        handler = registry.handler_lookup(s.type.strip_typedefs().code)
        # TODO: make StandardDecorator work here
        # if standardLib:
        #     return tracked.StandardDecorator(
        #             handler.factory(description), toTrack = False)
        return handler.factory(description)


class AddressedPull(Pull):

    _addressFixer = re.compile(r" .*")

    def __init__(self, description):
        super(AddressedPull, self).__init__(description)

        self._relativeName = str(description.relative_name)
        self._frame = str(description.frame)

        with frame.Selector(self.frame) as fs:
            sym = self.description.symbol
            if sym is not None:
                typ = sym.type
                if typ.code in {
                        gdb.TYPE_CODE_PTR,
                        gdb.TYPE_CODE_ARRAY,
                        gdb.TYPE_CODE_STRUCT,
                        gdb.TYPE_CODE_INT,
                        gdb.TYPE_CODE_FUNC,
                        }:
                    try:
                        self._object = sym.value(fs.frame.frame)
                    except TypeError:
                        self._object = None
                else:
                    self._object = None
            else:
                try:
                    self._object = gdb.parse_and_eval(self.name)
                except gdb.error as e:
                    traceback.print_exc()
                    self._object = None

        if self.description.symbol and self.description.symbol.type:
            self._type_name = str(self.description.symbol.type)
        elif isinstance(self.object, gdb.Value):
            self._type_name = Pull.get_true_type_name(self.object.type)
        else:
            # TODO: This is for dev.  Remove in production code.
            self._type_name = "void"
            # raise Exception("Untyped memory", self)

        if self.index is None:
            if self.object is None:
                self._index = "?"
            else:
                self._index = str(self.object.address)
            print(self._index)

        # if self.object is not None:
        #     self._dynamic_type, self._stripped_type = \
        #             self.extract_extra_type_info()
        # else:
        #     self._dynamic_type = "?"
        #     self._stripped_type = "?"

    @property
    def dict(self):
        return { "name": self.name, "address": self.address,
                 "frame": str(self.frame), "type": self.type_name}
                 # "dynamic_type": self.dynamic_type.name,
                 # "stripped_type": self.stripped_type.name}

    @property
    def relative_name(self):
        return self._relativeName

    @property
    def type_name(self):
        return self._type_name

    @property
    def address(self):
        return self._address

    @property
    def object(self):
        return self._object

    @property
    def frame(self):
        return self._frame

    @property
    def execution(self):
        return self._execution

    @property
    def stripped_type(self):
        return self._stripped_type

    @property
    def dynamic_type(self):
        return self._dynamic_type


class StructurePull(AddressedPull):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """

    _typeHandlerCode = gdb.TYPE_CODE_STRUCT
    _updateTracker = set()
    _watchers = dict()


    def _pull(self):
        name = deepcopy(str(self.name))
        if name[0] == "*":
            name = name[1:]
            marker = "->"
        else:
            marker = "."
        name += marker
        for f in self.object.type.fields():
            desc = descriptions.MemoryDescription(
                name + f.name,
                relativeName=marker)
            # TODO: Use member decorator
            # childObj = MemberDecorator(Pull.factory(desc))
            childObj = Pull.factory(desc)
            childObj.pull()
            self._children.append(childObj)


class ArrayPull(AddressedPull):

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_ARRAY

    def _pull(self):
        s = self.object

        # compute range of array in C sizeof(type) units
        self.range = s.type.range()

        # compute the type of data the array contains e.g. for float[2] the
        # answer is float for float[3][2][7] the answer is float
        print(self.type, type(self.type))
        self.target_type = target_type_name(s.type)

        # compute the immediate type of data the array contains.  e.g. for
        # float[2] the answer is float.  for float[3][2][7] the answer is
        # float[3][2]
        immediateTarget = s.type.target()

        # if the immediateTarget is an array type, then its first element will
        # have the same address as the current array.  Still, we want to treat
        # it as as different creature, so we remove the current address from
        # the updateTracker.

        # TODO: if the first element of the array is a pointer back to the
        # array, this may cause an infinite loop.  *This algorithm needs
        # torture testing.*
        if immediateTarget.code == gdb.TYPE_CODE_ARRAY:
            self._updateTracker.remove(self.index)

        # CONCERN: This should always be correct, but I
        # can't think of a time when the first value of
        # range would be non zero.  Still, this costs
        # very little, and if we support some "1 indexed"
        # langauge, then the algorithm should still work.
        children = []
        for i in range(self.range[0], self.range[1] + 1):
            relativeName = "[" + str(i) + "]"
            childName = self.name + relativeName
            childDesc = descriptions.MemoryDescription(
                childName,
                relativeName=relativeName)
            self._children.append(Pull.factory(childDesc))

class PrimitivePull(AddressedPull):
    """
    *Abstract* class to represent a primitive data type in the debugge.

    NOTE: Primitive data types are directly printable types such as int and
    double.
    """

    # def __init__(self):
    #     super(PrimitivePull, self).__init__()
    #     self.value = self.val_string()

    def val_string(self):
        """
        Get the printed value of a primitive object
        """
        with frame.Selector(self.frame) as s:
            ## TODO: Find a way to print values without messing with the $# vars
            # in the gdb interface.
            gdbPrint = gdb.execute("print " + self.name, False, True)
            ## TODO: If we can't fix the $# var, we may as well use it.
            ## this is free information we may as well store for the user's use.
            ansSections = gdbPrint[:-1].split(" = ")[1:]
            return " ".join(ansSections)


class PointerPull(PrimitivePull):
    """
    *Concrete* class to represent a pointer in the debugge.
    """
    _updateTracker = set()
    _watchers = dict()
    _typeHandlerCode = gdb.TYPE_CODE_PTR

    def _pull(self):
        super(PointerPull, self)._pull()
        relativeName = "*"
        targetName = relativeName + self.name
        desc = descriptions.MemoryDescription(
            targetName,
            relativeName=relativeName)
        target = Pull.factory(desc)

        try:
            target.pull()
            self._children = [target]
        except gdb.MemoryError as e:
            # TODO: Decorate target as invalid in this case.
            print(e)
            pass


class IntPull(PrimitivePull):
    """
    *Concrete* class to represent integral types.
    """

    _updateTracker = set()
    repository = dict()
    _watchers = dict()
    _arrayFinder = re.compile(r"(.*) ((?:\[\d*\])+)")
    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _spaceFixer = re.compile(r" ")
    _typeHandlerCode = gdb.TYPE_CODE_INT

    def _find_hidden_type(self):
        v = self.object
        atyp = IntPull._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            dims = map(int, atyp.group(2)[1:-1].split("]["))
            t = gdb.lookup_type(typ)
            for dim in dims:
                t = t.array(dim - 1)
            return t

        valString = self.val_string()
        ptyp = IntPull._pointerFinder.match(valString)
        if ptyp:
            typ = IntPull._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return gdb.lookup_type(typ).pointer()

        return False

    def _pull(self):
        # NOTE: I know this is a hack, but nothing I can do.
        # The problem is that sometimes gdb thinks pointers
        # and arrays are ints.
        hidden_typ = self._find_hidden_type()
        if isinstance(hidden_typ, gdb.Type):
            print("DEBUG: Found hidden type!") ## DEBUG
            self._description._object = self.object.cast(hidden_typ)
            Pull.factory(self.description).pull()
        else:
            self._value = self.val_string()
            typ = self.object.type
            self._type = Pull.get_true_type_name(typ)


class FloatPull(PrimitivePull):
    """
    *Concrete* class to represent floating point primitivies.
    """
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_FLT

# registry.TypeRegistration(CallPull)
registry.TypeRegistration(StructurePull)
registry.TypeRegistration(ArrayPull)
registry.TypeRegistration(PointerPull)
registry.TypeRegistration(IntPull)
registry.TypeRegistration(FloatPull)

# TODO: Refactor this to live in the main memory class.
# That way memories own their watchers, rather than the reverse.
# This has the advantage that it should stop complaints from gdb
# when objects go out of scope.
class MemoryWatcher(gdb.Breakpoint):

    def __init__(self, memory):
        self._memory = memory
        self._type_name = descriptions.type_name(memory.type)
        addr = memory.address
        expression = self._memory.name
        super(MemoryWatcher, self).__init__(
                expression,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True

    def stop(self):
        try:
            if self.memory:
                self.memory.update()
            else:
                print("Memory gone!")
        except Exception as e:
            traceback.print_exc()
        return False

    @property
    def memory(self):
        return self._memory


def get_frame_symbols(frm=None):
    with frame.Selector(frm) as fs:
        f = fs.frame
        if f.is_valid():
            return { str(sym) for sym in f.block() }
        else:
            raise Exception("Frame no longer valid")

def serialize_frame_globals(frm=None):
    frame = frm if frm is not None else gdb.selected_frame()
    block = frame.block().global_block
    serialize_block_locals(block)

def serialize_upward(baseBlock = None):
    if baseBlock is None:
        f = gdb.newest_frame()

    while f is not None:
        serialize_frame_locals(f)
        f = f.older()

def serialize_block_locals(blk = None):
    Memory._updatedNames.clear()
    block = blk if blk is not None else gdb.selected_frame().block()
    for sym in block:
        if sym.is_constant:
            continue
        desc = descriptions.MemoryDescription(sym.name, symbol = sym)
        if isinstance(desc.object, gdb.Symbol):
            continue
        obj = addressable_factory(desc)
        obj.track()

def serialize_frame_locals(frm = None):
    Memory._updatedNames.clear()
    for k in get_frame_symbols(frm = frm):
        desc = descriptions.MemoryDescription(k)
        obj = addressable_factory(desc)
        obj.track()

# def type_name(t, nameDecorators = ""):
#     if t.code == gdb.TYPE_CODE_PTR:
#         return type_name(t.target(), nameDecorators + "*")
#     elif t.code == gdb.TYPE_CODE_ARRAY:
#         length = str(t.range()[1] - t.range()[0] + 1)
#         return type_name(t.target(), nameDecorators + "[" + length + "]")
#     else:
#         return t.name + nameDecorators

def target_type_name(t):
    if t.code == gdb.TYPE_CODE_PTR or t.code == gdb.TYPE_CODE_ARRAY:
        return target_type_name(t.target())
    return t.name

# class StateSerializer(json.JSONEncoder):

#     def default(self, obj):
#         if isinstance(obj, set):
#             return {"set": list(obj)}
#         return json.JSONEncoder.default(self, StateSerializer.equal_fix(obj))

# def stopped(event):
#     arrayData = [ v2 for k, v in Array.repository.items() for k2, v2 in v.items() ]

#     with open("arrays.json", "w") as outfile:
#         json.dump(arrayData, outfile, cls=StateSerializer)

#     with open("pointers.json", "w") as outfile:
#         json.dump(Pointer.repository, outfile, cls=StateSerializer)

#     with open("structs.json", "w") as outfile:
#         json.dump(Structure.repository, outfile, cls=StateSerializer)

#     with open("values.json", "w") as outfile:
#         json.dump(Int.repository, outfile, cls=StateSerializer)

#     # with open("functions.json", "w") as outfile:
#     #     json.dump(Call.repository, outfile, cls=StateSerializer)

# gdb.events.stop.connect(stopped)

frameDescription = descriptions.MemoryDescription("yourframe")
f = frame.Frame(gdb.selected_frame())
e = models.Execution()
e.save()
d = descriptions.MemoryDescription("aa", address="1", execution=e)
x = IntPull(d)
x.save()


dStruct = descriptions.MemoryDescription("exx", address="2", execution=e)
xStruct = StructurePull(dStruct)
xStruct.track()

dArray = descriptions.MemoryDescription("b", address="3", execution=e)
xArray = Array.factory(descript=dArray)
xArray.track()

print(tracked.Tracked.objects().all())
