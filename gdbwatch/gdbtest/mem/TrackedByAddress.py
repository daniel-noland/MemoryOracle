#!/usr/bin/env python
# -*- encoding UTF-8 -*-


from copy import deepcopy

from .TrackedObject import TrackedObject
from .TrackedType import TrackedType
from .Exceptions import AbstractClassInitializationError

class TrackedByAddress(TrackedObject):

    def __init__(self, *args, **kwargs):
        raise AbstractClassInitializationError(
                "Can not initialize abstract class TrackedByAddress")

    @property
    def identifier(self):
        return self.address

    @property
    def address(self):
        return self._address

    @property
    def index(self):
        return self.address

