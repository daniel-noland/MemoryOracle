#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing all classes representing memory addressable
objects in the debugged program.
"""

import typed
import templatable


class AddressableInit(object):

    def __init__(self, method):
        self.method = method

    def __call__(self, *args):
        obj = args[0]
        description = args[1]
        obj._init(description)
        method(*args)
        # obj.track()


class Addressable(typed.Typed):
    """
    *Abstract* class representing memory addressable objects.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    updatedNames = set()

    def _init(self, addressableDescription):
        self._address = None
        self._description =  addressableDescription

    @property
    def index(self):
        return self.address

    @staticmethod
    def factory(addressableDescription):
        raise NotImplementedError("Factory not yet implimented")

    def _basic_track(self):

        if self.name in self.updatedNames:
            return False
        else:
            self.updatedNames.add(self.name)

        if self.index not in self.updateTracker:
            self.updateTracker.add(self.index)
            v = self.object
            v.fetch_lazy()
            typeName = Addressable.extract_type_name(v.type)
            if self.index not in self.repository:
                self.repository[self.index] = dict()

            self.repository[self.index][self.name] = self.description
            self.repository[self.index][self.name]["type"] = typeName
            return True

        else:
            return False

    def track(self):
        if self._basic_track():
            self._track()
            # TODO: Make sure the range on the watcher is correct
            self._watchers[self.index] = Watcher(self)
        else:
            if self.parent:
                self.repository[self.index][self.name]["parents"]\
                        [self.parent_class].add(self.parent)

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

    @AddressableInit
    def __init__(self, structureDescription):
        pass

    def _track(self):
        if self.index not in self.repository:
            self.basic_track()
            # self.repository[self.index][self.name]["children"] = \
            #     { f.name: self.get_address(s[f.name]) for f in s.type.fields() }
            for f in self.object.type.fields():
                desc = AddressableDescription(name + "." + f.name,
                        parent = self.index,
                        parent_class = "struct")
                childObj = MemberDecorator(Addressable.factory(desc))
                childObj.track()


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


class Pointer(Addressable):
    """
    *Concrete* class to represent a pointer in the debugge.
    """

    repository = dict()
    updateTracker = dict()

    _type_handler_code = gdb.TYPE_CODE_PTR

    @AddressableInit
    def __init__(self, pointerDescription):
        pass

    def _track(self):
        val = self.valstring()
        self.repository[self.index][self.name]["value"] = self.valstring()
        desc = AddressableDescription("(*" + self.name + ")",
                parent = self.index,
                parent_class = "pointer")
        try:
            target = Addressable.factory(desc)
            target.track()
        except gdb.MemoryError as e:
            # TODO: Decorate target as invalid in this case.
            pass


# Register the Pointer class with the type handler
Typed._register_type_handler(Pointer)


class Array(Addressable):
    """
    *Concrete* class to represent an array in the debugge.
    """

    repository = dict()
    updateTracker = dict()

    _type_handler_code = gdb.TYPE_CODE_ARRAY

    @AddressableInit
    def __init__(self, pointerDescription):
        pass

    def _track(self):
        # convenience vars:
        s = self.object
        repo = self.repository[self.index][self.name]

        # compute range of array in C sizeof(type) units
        repo["range"] = self.object.type.range()

        # compute the type of data the array contains
        # e.g. for float[2] the answer is float
        # for float[3][2][7] the answer is float
        repo["target_type"] = self.target_type_name()

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
            self.updateTracker.remove(self.index)

        # Compute the total length of the array.

        # CONCERN: This should always be correct, but I
        # can't think of a time when the first value of
        # range would be non zero.  Still, this costs
        # very little, and if we support some "1 indexed"
        # langauge, then the algorithm should still work.
        for i in range(*repo["range"]):
            childName = self.name + "[" + str(i) + "]"
            childDesc = AddressableDescription(
                        childName,
                        parent = self.index,
                        parent_class = "array")

            childObj = Addressable.factory(childDesc)
            childObj.track()


# Register the Array class with the type handler
Typed._register_type_handler(Array)


class Primative(Addressable):
    """
    *Abstract* class to represent a primative data type in the debugge.

    Primative data types are directly printable types such as int and double.
    """

    # repository = dict()
    # updateTracker = dict()

    # @AddressableInit
    # def __init__(self, pointerDescription):
    #     pass

    def _track(self):
        # convenience vars
        s = self.object
        repo = self.repository[self.index][self.name]

        repo["value"] = self.valstring()

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


class CharString(Primative):
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


def addressable_factory(description):
    s = description.object
    handler = Typed._type_lookup(s.type.code)
    return handler(description)

Addressable.factory = addressable_factory
