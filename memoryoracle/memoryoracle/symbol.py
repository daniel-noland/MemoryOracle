#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import typed


class Symbol(typed.Typed):
    """
    *Abstract* class to track a symbol in the debugee
    """
    pass


class Variable(Symbol):
    """
    *Concrete* class to track a variale in the debugee.
    """
    pass


class Function(Symbol):
    """
    *Concrete* class to track a function symbol in the debugee.
    """
    pass


class Alias(Symbol):
    pass


class Type(Symbol):
    pass


class Union(Type):
    pass


class TemplateDecorator(Symbol):
    pass


class TemplatedDecorator(TemplateDecorator):
    pass


class Typedef(Alias):
    pass


class Enum(Type):
    pass


class SimpleType(Type):
    """
    *Concrete* class to track a simple type in the debugee.

    Examples of simple types include int, float, double, int* and so on.
    """
    pass


class Structure(Type):
    """
    *Concrete* class to track the def of a structure or class in C++.
    """
    pass


class StronglyTypedEnum(Structure):
    pass


class Namespace(Symbol):
    """
    *Concrete* class to track a namespace defined in the debugee.
    """
    pass
