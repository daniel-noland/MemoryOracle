#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import traceback
from copy import deepcopy
from uuid import uuid4 as uuid
import mongoengine
import frame
import registry
import tracked


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
    def id(self):
        return self._id

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


class MemoryDescription(Description):
    """
    *Concrete* MemoryDescription class.

    A description of a memory addressable object.
    """

    # _parent_classifications = \
    #         { "array": dict(), "struct": dict(), "pointer": dict() }

    def __init__(self, name, **kwargs):
        self._name = name
        # self._parent = kwargs.get("parent")
        self._symbol = kwargs.get("symbol")
        self._execution = kwargs.get("execution")
        self._relativeName = kwargs.get("relativeName")
        self._frame = kwargs.get("frame", gdb.selected_frame())
        print("Type of _address: ", type(kwargs.get("address")))
        self._address = kwargs.get("address")

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

    @property
    def symbol(self):
        return self._symbol

