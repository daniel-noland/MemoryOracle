#!/usr/bin/env python# -*- encoding UTF-8 -*-
"""
File containing all classes representing memory addressable
objects in the debugged program.
"""

import gdb
import tracked
import typed
import registry
# import templatable
# import frame
from copy import deepcopy
import re
import descriptions
# import weakref
import traceback
import json
# from uuid import uuid4 as uuid

import pymongo
# import frame

import mongoengine

# NOTE: The read_preference should not be needed.  This is a workaround for a
# bug in pymongo.  (http://goo.gl/Somoeu)
connection = mongoengine.connect('memoryoracle',
                    read_preference=\
                            pymongo.read_preferences.ReadPreference.PRIMARY)

db = connection.memoryoracle


class Memory(typed.Typed):
    """
    *Abstract* class representing a instance of an object with a type.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    _addressFixer = re.compile(r" .*")
    _updatedNames = set()

    address = mongoengine.LongField()
    name = mongoengine.StringField()
    # description = mongoengine.ReferenceField(descriptions.Description)
    type = mongoengine.StringField()
    parent_class = mongoengine.ReferenceField('Memory')

    _watchers = dict()

    _execution = None

    class DuplicateMemory(Exception):
        pass

    @property
    def index(self):
        return long(self.address)


    @classmethod
    def _fetch(cls, address=None, execution=None, frame=None):
        if execution is not None:
            if frame is not None:
                if address is not None:
                    memories = cls.objects(
                        execution=execution,
                        frame=frame,
                        address=address
                    )
                    if len(memories) > 1:
                        raise DuplicateMemory("Duplicate address for memory!")
                    elif len(memories) == 0:
                        return False
                    return memories[0]
                raise Exception("Address must be specified in _fetch call!")
            raise Exception("Frame must be specified in _fetch call")
        raise Exception("Execution must be specified in _fetch call!")


    @staticmethod
    def _set_execution(execution):
        Memory._execution = execution

    @classmethod
    def factory(cls, *args, **kwargs):
        # TODO: Make this raise exceptions correctly
        if "address" in kwargs in kwargs and "frame" in kwargs:

            if "execution" in kwargs:
                Memory._set_execution(kwargs["execution"])


            fetchedVal = cls._fetch(
                address=kwargs["address"],
                frame=kwargs["frame"],
                execution=kwargs["execution"]
            )

            if fetchedVal != False:
                return fetchedVal

        return cls(*args, **kwargs)

    def _basic_track(self):
        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)

            # query = db[self.__class__.__name__].find({
            query = self.find({
                "execution": self.execution,
                "address": self.index
            })
            if query.count() > 1:
                # TODO: This is bugged.  It will throw errors on address recycle.
                raise Exception("Duplicate of same object with same address!")
            elif query.count() == 0:

                self.save()

            self.repository[self.index][self.name] = self.description.dict
            self.repository[self.index][self.name]["id"] = self.id
            return True
        else:
            return False

    def track(self):
        if self._basic_track():
            self._track()
            self._watchers[self.index] = MemoryWatcher(self)
            print(self.to_json()) ## DEBUG

    def update(self):
        self._clear_updated()
        self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.address)

    @property
    def watchers(self):
        return self._watchers

    meta = {
        'indexes': [
            'address',
        ]
    }


class Call(Memory):
    """
    *Concrete* class representing a particaular call to a function.

    This includes class / struct member functions, but does not
    include gdb Xmethods or similar.
    """
    repository = dict()
    _typeHandlerCode = gdb.TYPE_CODE_FUNC
    _updateTracker = set()
    _watchers = dict()


registry.TypeRegistration(Call)


class Structure(Memory):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """

    children = mongoengine.ListField(mongoengine.ReferenceField(tracked.Tracked))

    repository = dict()
    _typeHandlerCode = gdb.TYPE_CODE_STRUCT
    _updateTracker = set()
    _watchers = dict()


    def _track(self):
        name = deepcopy(str(self.name))
        if name[0] == "*":
            name = name[1:]
            marker = "->"
        else:
            marker = "."
        name += marker
        children = []
        for f in self.object.type.fields():
            desc = descriptions.MemoryDescription(
                    name + f.name,
                    relativeName=(marker, f.name),
                    parent=self,
                    parent_class="struct")
            # TODO: Use member decorator
            # childObj = MemberDecorator(addressable_factory(desc))
            childObj = addressable_factory(desc)
            childObj.track()
            children.append(childObj)
        self.children = children


registry.TypeRegistration(Structure)


class VolatileDecorator(Memory):
    """
    *Decorator* class to indicate an addressable is volatile.
    """
    pass


class RegisterDecorator(Memory):
    """
    *Decorator* class to decorate an addressable as being marked register.
    """
    pass


class ExternDecorator(Memory):
    """
    *Decorator* class to decorate an addressable as being marked extern.
    """
    pass


class MemberDecorator(Memory):
    """
    *Decorator* class to decorate an addressable as being a member value
    of another class.
    """
    pass


class Array(Memory):
    """
    *Concrete* class to represent an array in the debugge.
    """

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_ARRAY

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

        # TODO: if the first element of the array
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
            childDesc = descriptions.MemoryDescription(
                        childName,
                        relativeName = "[" + str(i) + "]",
                        parent = self.id,
                        parent_class = "array")

            childObj = addressable_factory(childDesc)
            childObj.track()


# Register the Array class with the type handler
registry.TypeRegistration(Array)


class Primitive(Memory):
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
        desc = descriptions.MemoryDescription("*" + self.name,
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
registry.TypeRegistration(Pointer)


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


registry.TypeRegistration(Int)


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


registry.TypeRegistration(Float)


class CharString(Pointer):
    """
    *Concrete* class to represent an old style null terminated C string.
    """
    pass


class ConstDecorator(Memory):
    """
    *Decorator* class to decorate an addressable as being marked const.
    """
    pass


class StaticDecorator(Memory):
    """
    *Decorator* class to decorate an addressable as being marked static.
    """
    pass


class Void(Memory):
    """
    *Concrete* class to describe an object of the type void
    """
    pass


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

class StateSerializer(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return {"set": list(obj)}
        return json.JSONEncoder.default(self, StateSerializer.equal_fix(obj))

def stopped(event):
    arrayData = [ v2 for k, v in Array.repository.items() for k2, v2 in v.items() ]

    with open("arrays.json", "w") as outfile:
        json.dump(arrayData, outfile, cls=StateSerializer)

    with open("pointers.json", "w") as outfile:
        json.dump(Pointer.repository, outfile, cls=StateSerializer)

    with open("structs.json", "w") as outfile:
        json.dump(Structure.repository, outfile, cls=StateSerializer)

    with open("values.json", "w") as outfile:
        json.dump(Int.repository, outfile, cls=StateSerializer)

    # with open("functions.json", "w") as outfile:
    #     json.dump(Call.repository, outfile, cls=StateSerializer)

gdb.events.stop.connect(stopped)
