#!/usr/bin/env python# -*- encoding UTF-8 -*-
"""
File containing all classes representing memory addressable
objects in the debugged program.
"""

import gdb
import tracked
import typed
import execution
import registry
import frame
# import templatable
from copy import deepcopy
import re
import descriptions
# import weakref
import traceback
import json
# from uuid import uuid4 as uuid

import pymongo

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

    address = mongoengine.StringField()
    name = mongoengine.StringField()
    frame = mongoengine.StringField()
    execution = mongoengine.ReferenceField(execution.Execution)
    # description = mongoengine.ReferenceField(descriptions.Description)
    type = mongoengine.StringField()
    dynamic_type = mongoengine.StringField()
    unaliased_type = mongoengine.StringField()
    children = mongoengine.ListField(mongoengine.ReferenceField('Memory'))

    _watchers = dict()

    _execution = None

    _updateTracker = set()

    class DuplicateAddress(Exception):
        pass

    def __init__(self, *args, **kwargs):
        self._description = kwargs["descript"]
        self._object = kwargs["descript"].object
        super(Memory, self).__init__(*args, **(kwargs["descript"].dict))

    @property
    def index(self):
        return str(self.address)

    @classmethod
    def _fetch(cls, description):
        if description is None:
            raise Exception("Description required to fetch object!")

        execution = description.execution
        frameDescription = descriptions.MemoryDescription("myframe", address=str(gdb.selected_frame()))

        # TODO: replace selected_frame call with something more flexible
        frm = frame.Frame(gdb.selected_frame())
        address = description.address
        memories = cls.objects(
            execution=execution,
            frame=str(frm),
            address=address
        )
        if len(memories) > 1:
            raise DuplicateAddress("Duplicate address for memory!")
        elif len(memories) == 0:
            return False
        return memories[0]

    @staticmethod
    def _set_execution(execution):
        Memory._execution = execution

    @classmethod
    def factory(cls, descript=None):
        """
        build an object based on a description, or fetch that object
        from the database if it already exists.
        """

        if descript.execution is not None:
            Memory._set_execution(descript.execution)
        else:
            descript._execution = Memory._execution

        fetchedVal = cls._fetch(descript)

        if fetchedVal != False:
            return fetchedVal

        return cls(descript=descript)

    def _basic_track(self):
        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if (self.address is None) or (self.address == "?"):
            return False

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)
            self.extract_dynamic_type()
            return True
        else:
            return False

    def track(self):
        if self._basic_track():
            self._track()
            ## TODO: enable memory watchers
            # self._watchers[self.index] = MemoryWatcher(self)
            print("Address: ", self.object.address, type(self.object.address), self.address, type(self.address))
            self.save()

    def update(self):
        self._clear_updated()
        self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.address)

    @property
    def watchers(self):
        return self._watchers

    def extract_dynamic_type(self):
        s = self.description.object
        # If the type is aliased, remove those aliases
        # and store that type
        strip = s.type.strip_typedefs()
        if strip != s.type:
            self.unaliased_type = strip.name

        # If the type is dynamic, detect this and store
        # accordingly
        dynamic = s.dynamic_type
        if dynamic != s.type:
            self.dynamic_type = dynamic.name

    meta = {
        'indexes': [
            'address',
            'frame'
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
                relativeName=marker)
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

    range = mongoengine.ListField()
    target_type = mongoengine.StringField() ## TODO: upgrade this to ref field

    def _track(self):
        # convenience vars:
        s = self.object

        # compute range of array in C sizeof(type) units
        arrayRange = self.object.type.range()
        self.range = arrayRange

        # compute the type of data the array contains
        # e.g. for float[2] the answer is float
        # for float[3][2][7] the answer is float
        print(self.type, type(self.type))
        self.target_type = target_type_name(self.object.type)

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
        children = []
        for i in range(arrayRange[0], arrayRange[1] + 1):
            relativeName = "[" + str(i) + "]"
            print(self.name, relativeName)
            childName = self.name + relativeName
            childDesc = descriptions.MemoryDescription(
                childName,
                relativeName=relativeName)

            childObj = addressable_factory(childDesc)
            childObj.track()
            children.append(childObj)
        self.children = children


# Register the Array class with the type handler
registry.TypeRegistration(Array)


class Primitive(Memory):
    """
    *Abstract* class to represent a primitive data type in the debugge.

    Primitive data types are directly printable types such as int and double.
    """

    # repository = dict()
    # _updateTracker = dict()

    value = mongoengine.StringField()

    def _track(self):
        self.value = self.val_string()

    def val_string(self):
        """
        Get the printed value of a primitive object
        """
        with frame.Selector(self.frame) as s:
            ## TODO: Find a way to print values without messing with the $# var
            # in the gdb interface.
            gdbPrint = gdb.execute("print " + self.name, False, True)
            ## TODO: If we can't fix the $# var, we may as well use it.
            ## this is free information we may as well store for the user's use.
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

    def _track(self):
        super(Pointer, self)._track()
        relativeName = "*"
        targetName = relativeName + self.name
        desc = descriptions.MemoryDescription(
            targetName,
            relativeName=relativeName)
        target = addressable_factory(desc)

        try:
            target.track()
            self.children = [target]
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
            print("Found hidden type!") ## DEBUG
            self._description._object = self.object.cast(hidden_typ)
            addressable_factory(self.description).track()
        else:
            self.value = self.val_string()
            typ = self.object.type
            self.type = descriptions.MemoryDescription.find_true_type_name(typ)


registry.TypeRegistration(Int)


class Float(Primitive):
    """
    *Concrete* class to represent floating point primitivies.
    """
    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_FLT

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
        standardLib = _stdLibChecker.match(
            descriptions.MemoryDescription.find_true_type_name(s.type))
        description._address = str(s.address)
        handler = registry.handler_lookup(s.type.strip_typedefs().code)
        if standardLib:
            return tracked.StandardDecorator(handler(descript=description), toTrack = False)
        return handler(descript=description)
    else:
        return Untracked()


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

frameDescription = descriptions.MemoryDescription("yourframe")
f = frame.Frame(gdb.selected_frame())
e = execution.Execution()
e.save()
d = descriptions.MemoryDescription("a", address="1", execution=e)
x = Float.factory(descript=d)
if x:
    x.save()
x.track()

dStruct = descriptions.MemoryDescription("exx", address="2", execution=e)
xStruct = Structure.factory(descript=dStruct)
xStruct.track()

dArray = descriptions.MemoryDescription("b", address="3", execution=e)
xArray = Array.factory(descript=dArray)
xArray.track()


