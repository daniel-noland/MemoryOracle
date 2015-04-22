#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the abstract Tracked class.
"""

# import gdb

import pymongo

import mongoengine

import execution

# NOTE: The read_preference should not be needed.  This is a workaround for a
# bug in pymongo.  (http://goo.gl/Somoeu)
mongoengine.connect('memoryoracle',
                    read_preference=\
                            pymongo.read_preferences.ReadPreference.PRIMARY)


class Tracked(mongoengine.Document):
    """
    *Abstract* class to represent a piece of information from the debugee
    to track.
    """

    execution = mongoengine.ReferenceField(execution.Execution)

    # def _init(self, description):
    #     self._description = description

    # def __init__(self, *args, **kwargs):
    #     raise NotImplementedError(
    #             "Attempted to instantiate abstract class Tracked")

    # @property
    # def description(self):
    #     return self._description

    # @property
    # def name(self):
    #     return self._name

    def track(self):
        raise NotImplementedError(
                "Attempted to track abstract class")


class Owner(Tracked):
    """
    *Abstract* class representing an object which owns another object.

    The Owner may both be owned, and contin objects which own other objects
    """
    children = mongoengine.ListField(mongoengine.ReferenceField(Tracked))


class Reference(Tracked):
    """
    *Abstract* class representing an object which is a reference to another
    object.
    """
    target = mongoengine.ReferenceField(Tracked)


class ProgramFile(Tracked):
    """
    *Abstract* class to track a file belonging to the debugee
    """
    pass


class ObjectFile(ProgramFile):
    """
    *Concrete* class to track a compiled object file in the debugee
    """
    source_file = mongoengine.ReferenceField("SourceFile")
    pass


class SourceFile(ProgramFile):
    """
    *Abstract* class to track a source code file belonging to the debugee.
    """
    object_file = mongoengine.ReferenceField(ObjectFile)
    pass


class UntrackedDecorator(Tracked):
    """
    *Decorator* anti-class to essentially turn off the behavior of the parent.

    Use this class when an object would normally be tracked, but you do not
    wish it to be.
    """

    def __init__(self, *args, **kwargs):
        pass

    def track(self):
        pass


