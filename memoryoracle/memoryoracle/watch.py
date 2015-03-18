#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb

import traceback
import weakref


class FrameFinish(gdb.FinishBreakpoint):

    def __init__(self, frame):
        super(StateFinish, self).__init__(frame, internal = True)
        self.frameName = str(frame)
        self.silent = True

    def stop(self):
        state = State._instances.get(self.frameName, None)
        if not state:
            print("Frame name not found " + self.frameName)
            return False
        for wp in state.watchers.values():
            wp.delete()
        State._instances.pop(self.frameName)
        return False


class AddressableWatcher(gdb.Breakpoint):

    def __init__(self, ):
        super(StateWatcher, self).__init__("*" + addr,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True
        self.name = name

    def stop(self):
        frameName = str(gdb.selected_frame())
        addr = self.expression[1:]
        state = State._instances.get(frameName, None)

        if not state:
            state = State()
            c = state.serialize_locals()
            if not c:
                return False

        try:
            val = state.name_to_val(self.name)
            names = state.get_serial(val = val).keys()
            for name in names:
                state.update(val, name)

        except Exception as e:
            traceback.print_exc()
            state.serialize(self.name, address = addr)
            print("ERROR: could not find address " + addr)
        return False

class StateCatch(gdb.Breakpoint):

    trackedFrames = dict()

    def __init__(self, breakCond, frame = None):
        super(StateCatch, self).__init__(breakCond, internal=True)
        self.silent = True
        self.frame = str(frame) if frame else str(gdb.selected_frame())

    def stop(self):
        s = State()
        s.serialize_locals()
