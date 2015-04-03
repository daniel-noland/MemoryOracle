#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""

import gdb
import tracked

class TypeDetectionError(Exception):
    pass

"""
Class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""
class Typed(tracked.Tracked):

    _typeCodeMap = {
            gdb.TYPE_CODE_ERROR: TypeDetectionError,
            }

    _typeHandlerCode = gdb.TYPE_CODE_ERROR

    @property
    def type(self):
        if self._type is None:
            self._type = Typed._type_lookup(self.gdb_type.code)
        return self._type

    @staticmethod
    def type_handler():
        return Typed._type_lookup(Typed._typeHandlerCode)

    @property
    def type_code(self):
        raise NotImplementedError("Abstract class Typed has no type code")

    @property
    def gdb_type(self):
        return self.object.type

    lookup = {
        gdb.TYPE_CODE_PTR: "Pointer",
        gdb.TYPE_CODE_ARRAY: "Array",
        gdb.TYPE_CODE_STRUCT: "Struct",
        gdb.TYPE_CODE_UNION: "Union",
        gdb.TYPE_CODE_ENUM: "Enum",
        gdb.TYPE_CODE_FUNC: "Function",
        gdb.TYPE_CODE_INT: "Int",
        gdb.TYPE_CODE_FLT: "Float",
        gdb.TYPE_CODE_VOID: "Void",
        gdb.TYPE_CODE_STRING: "String",
        gdb.TYPE_CODE_ERROR: "TypeDetectionError",
        gdb.TYPE_CODE_METHOD: "Method",
        gdb.TYPE_CODE_METHODPTR: "MethodPointer",
        gdb.TYPE_CODE_MEMBERPTR: "MemberPointer",
        gdb.TYPE_CODE_REF: "Reference",
        gdb.TYPE_CODE_CHAR: "Character",
        gdb.TYPE_CODE_BOOL: "Bool",
        gdb.TYPE_CODE_COMPLEX: "ComplexFloat",
        gdb.TYPE_CODE_TYPEDEF: "AliasedAddressable",
        gdb.TYPE_CODE_NAMESPACE: "Namespace",
        gdb.TYPE_CODE_INTERNAL_FUNCTION: "DebuggerFunction",
    }


def type_lookup(code):
    return Typed._typeCodeMap.get(code)

def register_type_handler(cls):

    if not issubclass(cls, Typed):
        raise ValueError("Type handler must be a Typed object")

    if type_lookup(cls._typeHandlerCode) is None:
        Typed._typeCodeMap[cls._typeHandlerCode] = cls
        print("Registered type code handler " + str(cls))
    else:
        error = "\nType code already in use!\n"
        error += "code: " + str(cls._typeHandlerCode)
        error += "\nhandler: " + str(cls) + "\n"
        raise KeyError(error)


class ErrorType(Typed):
    """
    *Concrete* class to track a gdb type error
    """
    pass
