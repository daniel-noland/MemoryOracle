#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import typed


class TypeDetectionError(Exception):
    pass


class TypeRegistration(object):
    """
    *Concrete* class to register discovered debugee types for lookup.
    """

    _typeCodeMap = {gdb.TYPE_CODE_ERROR: TypeDetectionError}

    _lookup = {
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

    def __init__(self, handler):
        self.register_handler(handler)

    @property
    def lookup(self):
        return self._lookup

    @classmethod
    def register_handler(cls, handler):

        if not issubclass(handler, typed.Typed):
            raise ValueError("Type handler must be a Typed object")

        if not cls._typeCodeMap.get(handler._typeHandlerCode):
            cls._typeCodeMap[handler._typeHandlerCode] = handler
            print("Registered type code handler " + str(handler))
        else:
            error = "Type code already in use: "
            error += "code: " + str(handler._typeHandlerCode)
            error += ", handler: " + str(handler) + "\n"
            raise KeyError(error)

    # @staticmethod
    # def type_handler():
    #     return Typed._type_lookup(Typed._typeHandlerCode)


