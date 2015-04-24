#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import traceback
from copy import deepcopy
from uuid import uuid4 as uuid
import mongoengine
import frame


class Description(object):
    """
    *Abstract* Description class.

    This is the superclass of all the different kinds of
    descriptions used by the subclasses of Tracked.
    """

    def _init(self):
        self._id = str(uuid())

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
        self._init()
        self._name = name
        # self._parent = kwargs.get("parent")
        self._symbol = kwargs.get("symbol")
        self._execution = kwargs.get("execution")
        self._relativeName = kwargs.get("relativeName")
        self._frame = kwargs.get("frame", gdb.selected_frame())
        print("Type of _address: ", type(kwargs.get("address")))
        self._address = kwargs.get("address")

        with frame.Selector(self.frame) as fs:
            sym = self._symbol
            if sym is not None:
                typ = sym.type
                print(sym.name, str(sym.type))
                if typ.code in {
                        gdb.TYPE_CODE_PTR,
                        gdb.TYPE_CODE_ARRAY,
                        gdb.TYPE_CODE_STRUCT,
                        gdb.TYPE_CODE_INT,
                        gdb.TYPE_CODE_FUNC,
                        }:
                    try:
                        self._object = sym.value(fs.frame.frame)
                    except TypeError:
                        self._object = None
                else:
                    self._object = None
            else:
                try:
                    self._object = gdb.parse_and_eval(self.name)
                except gdb.error as e:
                    # traceback.print_exc()
                    self._object = None

        if self._symbol and self._symbol.type:
            self._type_name = str(self._symbol.type)
        elif isinstance(self.object, gdb.Value):
            self._type_name = MemoryDescription.find_true_type_name(self.object.type)
        else:
            # TODO: This is for dev.  Remove in production code.
            self._type_name = "void"
            # raise Exception("Untyped memory", self)

        if self._address is None:
            if self.object is None:
                self._address = "?"
            else:
                self._address = str(self.object.address)
            print(self._address)

    @property
    def dict(self):
        return { "name": self.name, "address": self.address,
                "frame": str(self.frame), "type": self.type_name }

    @property
    def relative_name(self):
        return self._relativeName

    @property
    def type_name(self):
        return self._type_name

    @property
    def address(self):
        return self._address

    # @property
    # def parent(self):
    #     return self._parent

    # @property
    # def parents(self):
    #     return self._parents

    # @property
    # def parent_class(self):
    #     return self._parentClass

    @property
    def object(self):
        return self._object

    @property
    def frame(self):
        return self._frame

    @property
    def execution(self):
        return self._execution

    @classmethod
    def find_true_type_name(cls, t, nameDecorators = ""):
        if t.code == gdb.TYPE_CODE_PTR:
            return cls.find_true_type_name(t.target(), nameDecorators + "*")
        elif t.code == gdb.TYPE_CODE_ARRAY:
            length = str(t.range()[1] - t.range()[0] + 1)
            return cls.find_true_type_name(t.target(), nameDecorators + "[" + length + "]")
        else:
            if isinstance(t.name, str):
                return t.name + nameDecorators
            else:
                return "<## unknown type ##>"
