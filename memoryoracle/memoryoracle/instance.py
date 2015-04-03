#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing all classes representing memory addressable
objects in the debugged program.
"""

import gdb
import typed
import tracked
import templatable
import frame
from copy import deepcopy
import re
import descriptions
import weakref
import traceback
import json
from uuid import uuid4 as uuid


class Instance(typed.Typed):
    """
    *Abstract* class representing an instance of an object with a type.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    _addressFixer = re.compile(r" .*")
    _updatedNames = set()

    def _init(self, description):
        self._id = str(uuid())
        self._address = None
        self._description =  description
        self._name = description.name
        self._object = self.description.object
        self._type = self._object.type

        if self.parent is not None and self.parent_class is None:
            raise ValueError("Parent supplied but no parent class!")
        elif self.parent is None and self.parent_class is not None:
            raise ValueError("parent_class supplied but no parent!")

    @property
    def symbol(self):
        return self._description.symbol

    @property
    def id(self):
        return self._id

    @property
    def object(self):
        return self._object

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return str(self.address)

    def _basic_track(self):
        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)
            if self.index not in self.repository:
                self.repository[self.index] = dict()
            self.repository[self.index][self.name] = self.description.dict
            self.repository[self.index][self.name]["id"] = self.id
            return True
        else:
            return False

    def track(self):
        if self._basic_track():
            self._track()
            self._watchers[self.index] = InstanceWatcher(self)
        # else:
        #     if self.parent:
        #         repo = self.repository.get(self.index, dict()).get(self.name)
        #         if repo:
        #             repo["parents"][self.parent_class][self.parent] = None

    def update(self):
        self._clear_updated()
        self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.address)

    @property
    def watchers(self):
        return self._watchers

    @property
    def address(self):
        if self._address is None:
            self._address = self._compute_address()
        return self._address

    def _compute_address(self):
        if self.object.address:
            return self._addressFixer.sub("", str(self.object.address))
        else:
            return self.description.address

    @property
    def description(self):
        return self._description

    @property
    def parent(self):
        return self.description.parent

    @property
    def parent_class(self):
        return self.description.parent_class

    @property
    def frame(self):
        return self.description.frame

    def __init__(self, description):
        raise NotImplementedError(
                "Attempt to init abstract class Instance")


class Call(Instance):
    """
    *Concrete* class representing a particaular call to a function.

    This includes class / struct member functions, but does not
    include gdb Xmethods or similar.
    """
    repository = dict()
    _typeHandlerCode = gdb.TYPE_CODE_FUNC
    _updateTracker = set()
    _watchers = dict()

    def __init__(self, decription):
        self._init(decription)

    def _track(self):
        pass


typed.register_type_handler(Call)


class StructureInstance(Instance):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """

    repository = dict()
    _typeHandlerCode = gdb.TYPE_CODE_STRUCT
    _updateTracker = set()
    _watchers = dict()

    def __init__(self, structureDescription):
        self._init(structureDescription)

    def _track(self):
        # if self.name[0] == "*":
        #     name = "(" + self.name + ")"
        # else:
        name = deepcopy(self.name)
        if name[0] == "*":
            name = name[1:]
            marker = "->"
        else:
            marker = "."
        name += marker
        for f in self.object.type.fields():
            desc = descriptions.InstanceDescription(
                    name + f.name,
                    relativeName = (marker, f.name),
                    parent = self.id,
                    parent_class = "struct")
            # childObj = MemberDecorator(addressable_factory(desc))
            # TODO: Use member decorator
            childObj = addressable_factory(desc)
            childObj.track()


typed.register_type_handler(StructureInstance)


class VolatileDecorator(Instance):
    """
    *Decorator* class to indicate an addressable is volatile.
    """
    pass


class RegisterDecorator(Instance):
    """
    *Decorator* class to decorate an addressable as being marked register.
    """
    pass


class ExternDecorator(Instance):
    """
    *Decorator* class to decorate an addressable as being marked extern.
    """
    pass


class MemberDecorator(Instance):
    """
    *Decorator* class to decorate an addressable as being a member value
    of another class.
    """
    pass


class Array(Instance):
    """
    *Concrete* class to represent an array in the debugge.
    """

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_ARRAY

    def __init__(self, pointerDescription):
        self._init(pointerDescription)

    def _track(self):
        # convenience vars:
        s = self.object
        repo = self.repository[self.index][self.name]

        # compute range of array in C sizeof(type) units
        repo["range"] = self.object.type.range()

        # compute the type of data the array contains
        # e.g. for float[2] the answer is float
        # for float[3][2][7] the answer is float
        repo["target_type"] = target_type_name(self.type)

        # compute the immediate type of data the array
        # contains.  e.g. for float[2] the answer is float.
        # for float[3][2][7] the answer is float[3][2]
        immediateTarget = s.type.target()

        # if the immediateTarget is an array type, then
        # it will have the same address as the current
        # array.  Still, we want to treat it as as different
        # creature, so we remove the current address
        # from the updateTracker.

        # CONCERN: if the first element of the array
        # is a pointer back to the array, this may
        # cause an infinite loop.  *This algorithm
        # needs torture testing.*
        if immediateTarget.code == gdb.TYPE_CODE_ARRAY:
            self._updateTracker.remove(self.index)

        # Compute the total length of the array.

        # CONCERN: This should always be correct, but I
        # can't think of a time when the first value of
        # range would be non zero.  Still, this costs
        # very little, and if we support some "1 indexed"
        # langauge, then the algorithm should still work.
        for i in range(repo["range"][0], repo["range"][1] + 1):
            childName = self.name + "[" + str(i) + "]"
            childDesc = descriptions.InstanceDescription(
                        childName,
                        relativeName = "[" + str(i) + "]",
                        parent = self.id,
                        parent_class = "array")

            childObj = addressable_factory(childDesc)
            childObj.track()


# Register the Array class with the type handler
typed.register_type_handler(Array)


class Primitive(Instance):
    """
    *Abstract* class to represent a primitive data type in the debugge.

    Primitive data types are directly printable types such as int and double.
    """

    # repository = dict()
    # _updateTracker = dict()

    def _track(self):
        # convenience vars
        s = self.object
        repo = self.repository[self.index][self.name]

        repo["value"] = self.val_string()

        # If the type is aliased, remove those aliases
        # and store that type
        strip = s.type.strip_typedefs()
        if strip != s.type:
            self.values[addr][name]["unaliased_type"] = strip.name

        # If the type is dynamic, detect this and store
        # accordingly

        # TODO: Determine if the gdb python api needs this in the
        # pointer _track or here
        dynamic = s.dynamic_type
        if dynamic != s.type:
            self.values[addr][name]["dynamic_type"] = dynamic.name

    def val_string(self):
        """
        Get the printed value of a primitive object
        """
        with frame.FrameSelector(self.frame):
            gdbPrint = gdb.execute("print " + self.name, False, True)
            ansSections = gdbPrint[:-1].split(" = ")[1:]
            return " ".join(ansSections)


class Pointer(Primitive):
    """
    *Concrete* class to represent a pointer in the debugge.
    """

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_PTR

    def __init__(self, pointerDescription):
        self._init(pointerDescription)

    def _track(self):
        val = self.val_string()
        self.repository[self.index][self.name]["value"] = self.val_string()
        desc = descriptions.InstanceDescription("*" + self.name,
                relativeName = ("*", None),
                parent = self.id,
                parent_class = "pointer")
        try:
            target = addressable_factory(desc)
            target.track()
        except gdb.MemoryError as e:
            # TODO: Decorate target as invalid in this case.
            pass


# Register the Pointer class with the type handler
typed.register_type_handler(Pointer)


class Int(Primitive):
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

    def __init__(self, intDescription):
        self._init(intDescription)

    def _find_hidden_type(self):
        v = self.object
        atyp = Int._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            dims = map(int, atyp.group(2)[1:-1].split("]["))
            t = gdb.lookup_type(typ)
            for dim in dims:
                t = t.array(dim - 1)
            return t

        valString = self.val_string()
        ptyp = Int._pointerFinder.match(valString)
        if ptyp:
            typ = Int._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return gdb.lookup_type(typ).pointer()

        return False

    def _track(self):
        # NOTE: I know this is a hack, but nothing I can do.
        # The problem is that sometimes gdb thinks pointers
        # and arrays are ints.
        hidden_typ = self._find_hidden_type()
        if isinstance(hidden_typ, gdb.Type):
            self.description._object = self.object.cast(hidden_typ)
            obj = addressable_factory(self.description)
            obj.track()
        else:
            Int.repository[self.index][self.name]["value"] = self.val_string()
            Int.repository[self.index][self.name]["type"] = descriptions.type_name(self.object.type)


typed.register_type_handler(Int)


class Float(Primitive):
    """
    *Concrete* class to represent floating point primitivies.
    """
    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_FLT

    def __init__(self, floatDescription):
        self._init(floatDescription)


typed.register_type_handler(Float)


class CharString(Pointer):
    """
    *Concrete* class to represent an old style null terminated C string.
    """
    pass


class ConstDecorator(Instance):
    """
    *Decorator* class to decorate an addressable as being marked const.
    """
    pass


class StaticDecorator(Instance):
    """
    *Decorator* class to decorate an addressable as being marked static.
    """
    pass


class Void(Instance):
    """
    *Concrete* class to describe an object of the type void
    """
    pass


class InstanceWatcher(gdb.Breakpoint):

    def __init__(self, instance):
        self._instance = instance
        self._type_name = descriptions.type_name(instance.type)
        addr = instance.address
        expression = self._instance.name
        super(InstanceWatcher, self).__init__(
                expression,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True

    def stop(self):
        try:
            if self.addressable:
                self.addressable.update()
            else:
                print("Instance gone!")
        except Exception as e:
            traceback.print_exc()
        return False

    @property
    def addressable(self):
        return self._addressable

def addressable_factory(description):
    _stdLibChecker = re.compile("^std::.*")
    s = description.object
    if s is not None:
        standardLib = _stdLibChecker.match(descriptions.type_name(s.type))
        description._address = s.address
        handler = typed.type_lookup(s.type.strip_typedefs().code)
        if standardLib:
            return tracked.StandardDecorator(handler(description), toTrack = False)
        return handler(description)
    else:
        return Untracked()


def get_frame_symbols(frm = None):
    with frame.FrameSelector(frm) as fs:
        f = fs.frame
        if f.is_valid():
            return { str(sym) for sym in f.block() }
        else:
            raise Exception("Frame no longer valid")

def serialize_frame_globals(frm = None):
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
    Instance._updatedNames.clear()
    block = blk if blk is not None else gdb.selected_frame().block()
    for sym in block:
        if sym.is_constant:
            continue
        desc = descriptions.InstanceDescription(sym.name, symbol = sym)
        if isinstance(desc.object, gdb.Symbol):
            continue
        obj = addressable_factory(desc)
        obj.track()

def serialize_frame_locals(frm = None):
    Instance._updatedNames.clear()
    for k in get_frame_symbols(frm = frm):
        desc = descriptions.InstanceDescription(k)
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

class StateSerializer(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return { "set": list(obj) }
        return json.JSONEncoder.default(self, StateSerializer.equal_fix(obj))

def stopped(event):
    arrayData = [ v2 for k, v in Array.repository.items() for k2, v2 in v.items() ]

    with open("arrays.json", "w") as outfile:
        json.dump(arrayData, outfile, cls=StateSerializer)
    with open("pointers.json", "w") as outfile:
        json.dump(Pointer.repository, outfile, cls=StateSerializer)
    with open("structs.json", "w") as outfile:
        json.dump(StructureInstance.repository, outfile, cls=StateSerializer)
    with open("values.json", "w") as outfile:
        json.dump(Int.repository, outfile, cls=StateSerializer)
    with open("functions.json", "w") as outfile:
        json.dump(Call.repository, outfile, cls=StateSerializer)

gdb.events.stop.connect(stopped)
