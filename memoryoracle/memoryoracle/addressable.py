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


class Addressable(typed.Typed):
    """
    *Abstract* class representing memory addressable objects.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    _addressFixer = re.compile(r" .*")
    _updatedNames = set()

    def _init(self, addressableDescription):
        self._address = None
        self._description =  addressableDescription
        self._name = addressableDescription.name
        self._object = self.description.object
        self._type = self._object.type

    @property
    def object(self):
        return self._object

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self.address

    @staticmethod
    def factory(addressableDescription):
        raise NotImplementedError("Factory not yet implimented")

    def _basic_track(self):

        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)
            v = self.object
            v.fetch_lazy()
            if self.index not in self.repository:
                self.repository[self.index] = dict()
            self.repository[self.index][self.name] = self.description.dict
            return True
        else:
            return False

    def track(self):
        if self._basic_track():
            self._track()
            # TODO: Make sure the range on the watcher is correct
            self._watchers[self.index] = AddressableWatcher(self)
        else:
            if self.parent:
                repo = self.repository[self.index][self.name]
                repo["parents"][self.parent_class].add(self.parent)

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

    def __init__(self, addressableDescription):
        raise NotImplementedError(
                "Attempt to init abstract class Addressable")


class Function(Addressable, templatable.Templatable):
    """
    *Concrete* class representing a memory addressable function.

    This includes class / struct member functions, but does not
    include gdb Xmethods or similar.
    """
    pass


class Structure(Addressable, templatable.Templatable):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """

    repository = dict()
    _type_handler_code = gdb.TYPE_CODE_STRUCT
    _updateTracker = set()
    _watchers = dict()

    def __init__(self, structureDescription):
        self._init(structureDescription)

    def _track(self):
        for f in self.object.type.fields():
            desc = descriptions.AddressableDescription(self.name + "." + f.name,
                    parent = self.index,
                    parent_class = "struct")
            # childObj = MemberDecorator(addressable_factory(desc))
            # TODO: Use member decorator
            childObj = addressable_factory(desc)
            childObj.track()


typed.register_type_handler(Structure)


class VolatileDecorator(Addressable):
    """
    *Decorator* class to indicate an addressable is volatile.
    """
    pass


class RegisterDecorator(Addressable):
    """
    *Decorator* class to decorate an addressable as being marked register.
    """
    pass


class ExternDecorator(Addressable):
    """
    *Decorator* class to decorate an addressable as being marked extern.
    """
    pass


class MemberDecorator(Addressable):
    """
    *Decorator* class to decorate an addressable as being a member value
    of another class.
    """
    pass


class Array(Addressable):
    """
    *Concrete* class to represent an array in the debugge.
    """

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _type_handler_code = gdb.TYPE_CODE_ARRAY

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
        for i in range(*repo["range"]):
            childName = self.name + "[" + str(i) + "]"
            childDesc = descriptions.AddressableDescription(
                        childName,
                        parent = self.index,
                        parent_class = "array")

            childObj = addressable_factory(childDesc)
            childObj.track()


# Register the Array class with the type handler
typed.register_type_handler(Array)


class Primitive(Addressable):
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

    """
    Get the printed value of a primitive object
    """
    def val_string(self):
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

    _type_handler_code = gdb.TYPE_CODE_PTR

    def __init__(self, pointerDescription):
        self._init(pointerDescription)

    def _track(self):
        # TODO: Build names using arrow op
        val = self.val_string()
        self.repository[self.index][self.name]["value"] = self.val_string()
        desc = descriptions.AddressableDescription("(*" + self.name + ")",
                parent = self.index,
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

    def __init__(self, intDescription):
        self._init(intDescription)

    _arrayFinder = re.compile(r"(.*) ((?:\[\d*\])+)")
    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _spaceFixer = re.compile(r" ")
    _type_handler_code = gdb.TYPE_CODE_INT

    def _true_type(self):
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
        hidden_typ = self._true_type()
        if isinstance(hidden_typ, gdb.Type):
            # NOTE: I know this is a hack, but nothing I can do.
            # The problem is that sometimes gdb thinks pointers
            # and arrays are ints.
            self.description._object = self.object.cast(hidden_typ)
            obj = addressable_factory(self.description)
            obj.track()
        else:
            Int.repository[self.index][self.name]["value"] = self.val_string()


typed.register_type_handler(Int)


class Float(Primitive):
    """
    *Concrete* class to represent floating point primitivies.
    """
    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _type_handler_code = gdb.TYPE_CODE_FLT

    def __init__(self, floatDescription):
        self._init(floatDescription)


typed.register_type_handler(Float)


class CharString(Pointer):
    """
    *Concrete* class to represent an old style null terminated C string.
    """
    pass


class ConstDecorator(Addressable):
    """
    *Decorator* class to decorate an addressable as being marked const.
    """
    pass


class StaticDecorator(Addressable):
    """
    *Decorator* class to decorate an addressable as being marked static.
    """
    pass



class AddressableWatcher(gdb.Breakpoint):

    def __init__(self, addressable):
        self._addressable = weakref.ref(addressable)()
        self._type_name = type_name(addressable.type)
        addr = addressable.address
        expression = "(" + self._type_name + ") *" + addr
        super(AddressableWatcher, self).__init__(
                expression,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True

    def stop(self):
        try:
            if self.addressable:
                print("updating addressable!")
                self.addressable.update()
            else:
                print("addressable is gone!")
        except Exception as e:
            traceback.print_exc()
        return False

    @property
    def addressable(self):
        return self._addressable

def addressable_factory(description):
    _stdLibChecker = re.compile("^std::.*")
    print(description.name)
    s = description.object
    print(type_name(s.type))
    standardLib = _stdLibChecker.match(type_name(s.type))
    description._address = s.address
    print("Looking for " + typed.Typed.lookup[s.type.strip_typedefs().code])
    print(s.type.strip_typedefs())
    print(s.address)
    handler = typed.type_lookup(s.type.strip_typedefs().code)
    print(handler)
    if standardLib:
        return tracked.StandardDecorator(handler(description), toTrack = False)
    return handler(description)

def get_local_vars(frm = None):
    with frame.FrameSelector(frm) as fs:
        f = fs.frame
        if f.is_valid():
            return { str(sym) for sym in f.block() }
        else:
            raise Exception("Frame no longer valid")

def serialize_locals(frm = None):
    Addressable._updatedNames.clear()
    for k in get_local_vars(frm = frm):
        desc = descriptions.AddressableDescription(k)
        obj = addressable_factory(desc)
        obj.track()

def type_name(t, nameDecorators = ""):
    if t.code == gdb.TYPE_CODE_PTR:
        return type_name(t.target(), nameDecorators + "*")
    elif t.code == gdb.TYPE_CODE_ARRAY:
        length = str(t.range()[1] - t.range()[0] + 1)
        return type_name(t.target(), nameDecorators + "[" + length + "]")
    else:
        return t.name + nameDecorators

def target_type_name(t):
    if t.code == gdb.TYPE_CODE_PTR or t.code == gdb.TYPE_CODE_ARRAY:
        return target_type_name(t.target())
    return t.name
