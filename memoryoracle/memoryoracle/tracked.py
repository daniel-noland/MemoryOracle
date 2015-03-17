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

    track = True

    def __init__(self, tracked, toTrack = False):
        """
        Ctor for ExternalDecorator.
        """
        self.tracked = tracked
        self.toTrack = toTrack

    def track(self):
        """
        Track an external object
        """
        if track or self._toTrack:
            entry = tracked.track()
            entry["standard_library"] = True


class Frame(Tracked):
    """
    *Concrete* class to track a frame in the debugee

    TODO: Use finish points to automatically clean up.
    """
    pass

    _instances = dict()

    def __init__(self, gdbFrame = None):
        self.frame = gdbFrame if gdbFrame is not None else gdb.selected_frame()
        self.track()

    @property
    def index(self):
        return str(self.frame)

    def is_valid(self):
        return self.frame.is_valid()

    def name(self):
        return self.frame.name()

    def architecture(self):
        return self.frame.architecture()

    def type(self):
        return self.frame.type()

    def unwind_stop_reason(self):
        return self.frame.unwind_stop_reason()

    def pc(self):
        return self.frame.pc()

    def block(self):
        return self.frame.block()

    def function(self):
        return self.frame.function()

    def older(self):
        return Frame(self.frame.older())

    def newer(self):
        return Frame(self.frame.newer())

    def find_sal(self):
        return self.frame.find_sal()

    def read_register(self, register):
        return self.frame.read_register()

    def read_var(self, variable, block = None):
        return self.frame.read_var(variable, block)

    def select(self):
        self.frame.select()


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
