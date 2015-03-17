#!/usr/bin/env python
# -*- encoding UTF-8 -*-


class TrackedType(TrackedObject):

    _structs = dict()
    _pointers = dict()
    _arrays = dict()

    @staticmethod
    def extract_class(typ, nameDecorators = ""):

        if isinstance(typ, TrackedType):
            t = typ.gdb_type
        else:
            t = typ

        if t.code == gdb.TYPE_CODE_PTR:
            return TrackedByAddress.extract_class(t.target(), nameDecorators + "*")

        elif t.code == gdb.TYPE_CODE_ARRAY:
            length = str(t.range()[1] - t.range()[0] + 1)
            return TrackedByAddress.extract_class(t.target(), nameDecorators + "[" + length + "]")

        else:
            return t.name + nameDecorators

