#!/usr/bin/env python
# -*- encoding UTF-8 -*-


import gdb
import tracked


class Frame(tracked.Tracked):
    """
    *Concrete* class to track a frame in the debugee

    TODO: Use finish points to automatically clean up.
    """

    _instances = dict()

    def __init__(self, gdbFrame = None):
        self.frame = gdbFrame if gdbFrame is not None else gdb.selected_frame()
        # self.track()

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


class FrameSelector(object):

    def __init__(self, f = None):
        if f is None:
            self._frame = Frame(gdb.newest_frame())
        elif isinstance(f, gdb.Frame):
            self._frame = Frame(f)
        elif isinstance(f, Frame):
            self._frame = f
        else:
            print("Frame param of invalid type!")
            raise ValueError("frame param of invalid type: " + str(type(f)))

        # self.frame.track()

    def __enter__(self):
        self.oldFrame = gdb.selected_frame()
        self.frame.select()
        return self

    def __exit__(self, type, value, tb):
        self.oldFrame.select()

    @property
    def frame(self):
        return self._frame
