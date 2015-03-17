#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import addressable

class Container(addressable.Structure):
    """
    *Abstract* class to represent a C++ container.

    This is mostly intended to help correct rendering for
    standard library containers, but should be helpful for
    user defined containers as well.
    """
    pass


class SLContainer(Container):
    """
    *Abstract* class to represent a C++ standard library
    container.
    """
    pass


class SLForwardList(SLContainer):
    pass


class SLList(SLContainer):
    pass


class SLMap(SLContainer):
    pass


class SLQueue(SLContainer):
    pass


class SLSet(SLContainer):
    pass


class SLStack(SLContainer):
    pass


class SLUnorderedMap(SLContainer):
    pass


class SLUnorderedSet(SLContainer):
    pass


class SLVector(SLContainer):
    pass


class SLArray(SLContainer):
    pass


class SLBitset(SLContainer):
    pass


class SLDeque(SLContainer):
    pass
