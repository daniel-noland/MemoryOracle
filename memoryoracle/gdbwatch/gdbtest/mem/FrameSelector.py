#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
from .TrackedFrame import TrackedFrame

class FrameSelector(object):

    def __init__(self, frame = None):
        if isinstance(frame, gdb.Frame):
            self._frame = TrackedFrame(frame)
        elif isinstance(frame, TrackedFrame):
            self._frame = frame
        elif frame is None:
            self._frame = TrackedFrame(gdb.newest_frame())
        else:
            raise ValueError("frame param of invalid type: " + str(type(frame)))

    def __enter__(self):
        self.oldFrame = gdb.selected_frame()
        self.frame.select()

    def __exit__(self, type, value, tb):
        self.oldFrame.select()

    @property
    def frame(self):
        return self._frame
