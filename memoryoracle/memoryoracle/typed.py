#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""

import tracked
import gdb
import mongoengine

class TypeDetectionError(Exception):
    pass


"""
Class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""
class Typed(tracked.Tracked):

    _typeHandlerCode = gdb.TYPE_CODE_ERROR

    @property
    def type(self):
        if self._type is None:
            self._type = Typed._type_lookup(self.gdb_type.code)
        return self._type

    @property
    def type_code(self):
        raise NotImplementedError("Abstract class Typed has no type code")

    # @property
    # def gdb_type(self):
    #     return self.object.type
