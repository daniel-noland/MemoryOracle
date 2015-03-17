#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
from .TrackedObject import TrackedObject
from .TrackedObject import TrackAfter


class TrackedFrame(TrackedObject):

    _instances = dict()

    @TrackAfter(update = True)
    def __init__(self, gdbFrame = None):
        self.frame = gdbFrame if gdbFrame is not None else gdb.selected_frame()

    @property
    def identifier(self):
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
        return TrackedFrame(self.frame.older())

    def newer(self):
        return TrackedFrame(self.frame.newer())

    def find_sal(self):
        return self.frame.find_sal()

    def read_register(self, register):
        return self.frame.read_register()

    def read_var(self, variable, block = None):
        return self.frame.read_var(variable, block)

    def select(self):
        self.frame.select()

