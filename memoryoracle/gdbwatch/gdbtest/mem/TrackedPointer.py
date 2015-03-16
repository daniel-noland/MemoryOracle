#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
from .TrackedByAddress import TrackedByAddress
from .TrackAfter import TrackAfter
from .TrackedFrame import TrackedFrame
from .FrameSelector import FrameSelector


class TrackedPointer(TrackedByAddress):

    _instances = dict()
    _updateTracker = set()

    @TrackAfter(update = True)
    def __init__(self, name, *args, **kwargs):

        name = args[0]

        super(TrackedPointer, self).__init__(self, *args, **kwargs)

        addr = self.address
        name = self.name

        if addr not in self._updatedPointers:

            c = self._basic_serialize()

            self._updatedPointers.add(addr)
            try:
                val = State._addressFixer.sub("", self.value_string())
                self._instances[addr][name]["value"] = val
                Tracked("(*" + name + ")", frame = self.frame,
                        parent = addr,
                        parentClassification = "pointer")
            except gdb.MemoryError as e:
                pass
        else:
            if parent:
                self._instances[addr][name]["parents"][parentClassification].add(
                        parent)
