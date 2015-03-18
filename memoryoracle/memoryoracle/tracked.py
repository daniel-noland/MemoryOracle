#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the abstract Tracked class.
"""


"""
*Abstract* class to represent a piece of information from the debugee
to track.
"""
class Tracked(object):

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
                "Attempted to instantiate abstract class Tracked")


    @property
    def index(self):
        raise NotImplementedError(
                "Attempted to get index of abstract class")


    def track(self):
        raise NotImplementedError(
                "Attempted to track abstract class")


class ExternalDecorator(Tracked):
    """
    *Decorator* class to decorate a tracked object as being external
    to your work.
    """

    track = True

    def __init__(self, tracked, toTrack = False):
        """
        Ctor for ExternalDecorator.
        """
        self.tracked = tracked
        self._toTrack = toTrack

    def track(self):
        """
        Track an external object
        """
        if track or self._toTrack:
            entry = self.tracked.track()
            entry["external"] = True


class StandardDecorator(Tracked):
    """
    *Decorator* class to decorate a tracked object as belonging to
    the languages standard library.
    """

    def __init__(self, tracked, toTrack = False):
        """
        Ctor for StandardDecorator.
        """
        self.tracked = tracked
        self._toTrack = toTrack

    def track(self):
        """
        Track a standard object
        """
        if self._toTrack:
            self.tracked.track()


class Symbol(Tracked):
    """
    *Concrete* class to track a symbol in the debugee
    """
    pass


class ProgramFile(Tracked):
    """
    *Abstract* class to track a file belonging to the debugee
    """
    pass


class ObjectFile(ProgramFile):
    """
    *Concrete* class to track a compiled object file in the debugee
    """
    pass


class SourceFile(ProgramFile):
    """
    *Abstract* class to track a source code file belonging to the debugee.
    """
    pass


class Namespace(Tracked):
    """
    *Concrete* class to track a namespace defined in the debugee.
    """
    pass
