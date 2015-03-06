#!/usr/bin/env python
# -*- encoding UTF-8 -*-
import gdb
from .MemoryState import MemoryState

class MemoryWatcher(gdb.Breakpoint):

    MemoryState.update()
    instances = dict()

    def __init__(self, addr):
        super(MemoryWatcher, self).__init__(
                "*" + addr,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False
        )
        try:
            if " " not in addr:
                MemoryWatcher.instances[addr] = self
        except gdb.error as e:
            # TODO: figure out a better way to watch the other addresses
            print(e)

    def stop(self):
        global m
        addr = self.expression
        val = gdb.parse_and_eval(addr)
        toUpdate = MemoryWatcher.m._valueDict.pop(addr[1:])["name"]
        MemoryWatcher.m._serialize_value(val, toUpdate)
        # TODO: make this send to web socket instead of screen
        print(MemoryWatcher.m._valueDict[str(val.address)])
        return False

    @staticmethod
    def reexamine_state():
        MemoryWatcher.m = MemoryState()
        MemoryWatcher.state = m.serialize_locals()
