#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import ast
import pickle
import json
import pprint

gdb.execute("start", False, False)

def struct_to_dict(s):
    if s.type.code == gdb.TYPE_CODE_STRUCT:
        return { f.name: struct_to_dict(s[f.name]) for f in s.type.fields() }
    else:
        return s

def get_local_vars():
    localString = gdb.execute("info locals", False, True)
    transform = re.sub(r'([a-zA-Z_][0-9a-zA-Z_:]*) \= .*\n', r"'\1', ", localString)
    transform = "(" + transform[:-2] + ")"
    localVars = ast.literal_eval(transform)
    gdbVars = { v: gdb.parse_and_eval(v) for v in localVars }
    return gdbVars

def serialize_value(s):
    s.fetch_lazy()
    if s.type.code == gdb.TYPE_CODE_STRUCT:
        serialized = { "address": str(s.address),
                      "is_optomized_out": s.is_optimized_out,
                      "type": s.type.name,
                      "stripped_type": s.type.strip_typedefs().name,
                      "dynamic_type": s.dynamic_type.name,
                      "value": { f.name: serialize_value(s[f.name]) for f in s.type.fields() }
                }
        return serialized
    elif s.type.code == gdb.TYPE_CODE_PTR:
        try:
            return serialize_value(s.dereference())
        except gdb.MemoryError as e:
            print(e) #DEBUG
            if str(s) == "0x0":
                return "nullptr"
            else:
                return "invalid"
    else:
        return str(s)

def serialize_locals():
    return { k: serialize_value(v) for k,v in get_local_vars().items() }

pp = pprint.PrettyPrinter(indent=3)
pp.pprint(serialize_locals())
