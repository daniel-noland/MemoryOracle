#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb

from .Exceptions import AbstractClassInitializationError
from .TrackedObject import TrackedAfter


class TrackAddressAfter(TrackAfter):

    def __init__(self, update = False)
        super(TrackAddress, self).__init__(self, update = update)

    def __call__(self, method):

        super_method = super(TrackAddressAfter, self).__call__(self, method)

        def wrapped_method(*args, **kwargs):
            args[0].address = kwargs["address"]
            super_method(*args, **kwargs)

        return wrapped_method
