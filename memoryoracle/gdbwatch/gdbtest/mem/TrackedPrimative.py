#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
from .TrackedByAddress import TrackedByAddress
from .TrackAfter import TrackAfter
from .TrackedFrame import TrackedFrame
from .FrameSelector import FrameSelector


class TrackedPrimative(TrackedByAddress):

    _instances = dict()
    _updateTracker = set()

    @TrackAfter(update = True)
    def __init__(self, *args, **kwargs):

        super(TrackedPrimative, self).__init__(self, *args, **kwargs)

        val = self.value_string(name)
        self._instances[addr][name]["value"] = val

        strip = s.type.strip_typedefs()
        if strip != s.type:
            self._instances[addr][name]["stripped_type"] = strip.name

        dynamic = s.dynamic_type
        if dynamic != s.type:
            self._instances[addr][name]["dynamic_type"] = dynamic.name
