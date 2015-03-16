#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing all classes representing memory addressable
objects in the debugged program.
"""

from ..tracked import Tracked
from ..templateable. import Templateable


class Addressable(Tracked):
    """
    *Abstract* class representing memory addressable objects.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    def __init__(self, obj, address = None):
        self.address = None


class Function(Addressable, Templateable):
    """
    *Concrete* class representing a memory addressable function.

    This includes class / struct member functions, but does not
    include gdb Xmethods or similar.
    """
    pass


class Structure(Addressable, Templateable):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """
    pass


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
    pass


class Array(Addressable):
    """
    *Concrete* class to represent an array in the debugge.
    """
    pass


class Primative(Addressable):
    """
    *Concrete* class to represent a primative data type in the debugge.

    Primative data types are directly printable types such as int and double.
    """
    pass


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
