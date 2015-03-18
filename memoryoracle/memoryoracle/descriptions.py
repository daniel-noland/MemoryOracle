#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import frame
import gdb
from copy import deepcopy

class Description(object):
    """
    *Abstract* Description class.

    This is the superclass of all the different kinds of
    descriptions used by the subclasses of Tracked.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
                "Attempt to instiante abstract class");


    @property
    def name(self):
        return self._name

    @property
    def dict(self):
        raise NotImplementedError(
                "Can not transform abstract class Description to dict")


class BlackBoxDecorator(Description):
    """
    *Decorator* BlackBoxDecorator class.

    A decorator to mark a description as refering to a
    piece of information which should not be intrusively
    explored by MemoryOracle.
    """

    def __init__(self, description):
        self._description = description


    @property
    def description(self):
        return "---black box---"


    @property
    def name(self):
        return self._description.name


class ExternalDescriptionDecorator(Description):
    """
    *Decorator* ExternalDescriptionDecorator class.

    A decorator to mark another description as refering to an
    external piece of information, such as a standard library
    header file or a library file which is external to your
    project.
    """

    def __init__(self, description):
        self._description = description


    @property
    def description(self):
        return { "external": self._description }


    @property
    def name(self):
        return self._description.name


class StandardDescriptionDecorator(Description):
    """
    *Decorator* StandardDescriptionDecorator class.

    A decorator to mark another description as pertaining to a
    piece of the language's standard library.
    """

    def __init__(self, description):
        self._description = description


    @property
    def description(self):
        return { "standard": self._description }


    @property
    def name(self):
        return self._description.name


class FileDescription(Description):
    """
    *Abstract* FileDescription class.

    A description of a file object.
    """
    pass


class SourceFileDescription(FileDescription):
    """
    *Concrete* SourceFileDescription class.

    An description of a program source code file.
    """
    pass


class ObjectFileDescription(FileDescription):
    """
    *Concrete* ObjectFileDescription class.

    An description of a program's compiled object file.
    """
    pass


class AddressableDescription(Description):
    """
    *Concrete* AddressableDescription class.

    A description of a memory addressable object.
    """

    _parent_classifications = \
            { "array": set(), "struct": set(), "pointer": set() }

    def __init__(self, name, **kwargs):
        self._name = name
        self._address = kwargs.get("address")
        self._parent = kwargs.get("parent")
        self._parents = \
                deepcopy(AddressableDescription._parent_classifications)
        self._parentClass = kwargs.get("parent_class")
        self._parents[self.parent_class] = self.parent
        self._frame = frame.Frame(kwargs.get("frame", gdb.selected_frame()))

        if self.parent is not None and self.parent_class is None:
            raise ValueError("Parent supplied but no parent class!")
        # elif self.parent is None and self.parent_class is not None:
        #     raise ValueError("parent_class supplied but no parent!")

        with frame.FrameSelector(self.frame):
            self._object = gdb.parse_and_eval(self.name)

        self._type_name = type_name(self.object.type)

    @property
    def dict(self):
        d = deepcopy(AddressableDescription._parent_classifications)
        d[self.parent_class] = set([self.parent])
        return { "name": self.name, "parents": d,
                "frame": str(self.frame) }

    @property
    def type_name(self):
        return self._type_name

    @property
    def address(self):
        return self._address

    @property
    def parent(self):
        return self._parent

    @property
    def parents(self):
        return self._parents

    @property
    def parent_class(self):
        return self._parentClass

    @property
    def object(self):
        return self._object

    @property
    def frame(self):
        return self._frame

def type_name(t, nameDecorators = ""):
    if t.code == gdb.TYPE_CODE_PTR:
        return type_name(t.target(), nameDecorators + "*")
    elif t.code == gdb.TYPE_CODE_ARRAY:
        length = str(t.range()[1] - t.range()[0] + 1)
        return type_name(t.target(), nameDecorators + "[" + length + "]")
    else:
        return t.name + nameDecorators