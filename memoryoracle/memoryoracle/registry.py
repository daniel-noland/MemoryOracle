#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb

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

    @property
    def lookup(self):
        return self._lookup

    def register_type_handler(self, cls):

        if not issubclass(cls, Typed):
            raise ValueError("Type handler must be a Typed object")

        if Typed.lookup[cls._typeHandlerCode] is None:
            Typed._typeCodeMap[cls._typeHandlerCode] = cls
            print("Registered type code handler " + str(cls))
        else:
            error = "\nType code already in use!\n"
            error += "code: " + str(cls._typeHandlerCode)
            error += "\nhandler: " + str(cls) + "\n"
            raise KeyError(error)

    @staticmethod
    def type_handler():
        return Typed._type_lookup(Typed._typeHandlerCode)


