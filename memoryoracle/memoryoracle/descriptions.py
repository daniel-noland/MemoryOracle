#!/usr/bin/env python
# -*- encoding UTF-8 -*-


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

    def __init__(self, name, **kwargs):
        self._name = name
        self._address = kwargs.get("address")
        self._parent = kwargs.get("parent")
        self._parentClass = kwargs.get("parent_class")
        self._frame = Frame(kwargs.get("frame", gdb.selected_frame()))

        if self.parent is not None and self.parent_class is None:
            raise ValueError("Parent supplied but no parent class!")
        elif self.parent is None and self.parent_class is not None:
            raise ValueError("parent_class supplied but no parent!")

        with FrameSelector(self.frame):
            self._object = gdb.parse_and_eval(self.name)

    @property
    def address(self):
        return self._address

    @property
    def parent(self):
        return self._parent

    @property
    def parent_class(self):
        return self._parentClass

    @property
    def object(self):
        return self._object

    @property
    def frame(self):
        return self.frame
