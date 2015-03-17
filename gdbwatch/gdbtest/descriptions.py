#!/usr/bin/env python
# -*- encoding UTF-8 -*-


class Description(object):
    """
    *Abstract* Description class.

    This is the superclass of all the different kinds of
    descriptions used by the subclasses of Tracked.
    """
    pass


class BlackBoxDecorator(Description):
    """
    *Decorator* BlackBoxDecorator class.

    A decorator to mark a description as refering to a
    piece of information which should not be intrusively
    explored by MemoryOracle.
    """
    pass


class ExternalDescriptionDecorator(Description):
    """
    *Decorator* ExternalDescriptionDecorator class.

    A decorator to mark another description as refering to an
    external piece of information, such as a standard library
    header file or a library file which is external to your
    project.
    """
    pass


class StandardDescriptionDecorator(Description):
    """
    *Decorator* StandardDescriptionDecorator class.

    A decorator to mark another description as pertaining to a
    piece of the language's standard library.
    """
    pass


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
    pass


