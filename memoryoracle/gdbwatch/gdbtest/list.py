#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import ast
import pickle
import json
import pprint

gdb.execute("start", False, False)

class MemoryState(object):

    def __init__(self):
        self._pp = pprint.PrettyPrinter(indent=3)
        self._valueDict = dict()
        self._structDict = dict()
        self._arrayDict = dict()

    @staticmethod
    def struct_to_dict(s):
        if s.type.code == gdb.TYPE_CODE_STRUCT:
            return { f.name: MemoryState.struct_to_dict(s[f.name]) for f in s.type.fields() }
        else:
            return s

    def _get_local_vars(self):
        localString = gdb.execute("info locals", False, True)
        transform = re.sub(r'([a-zA-Z_][0-9a-zA-Z_:]*) \= .*\n', r"'\1', ", localString)
        if transform[-2:] is ", ":
            transform = transform[:-2]
        transform = "(" + transform + ")"
        localVars = ast.literal_eval(transform)
        self.gdbVars = { v: gdb.parse_and_eval(v) for v in localVars }

    def _serialize_value(self, s, name):
        addr = str(s.address)
        if addr not in self._valueDict:
            s.fetch_lazy()
            self._valueDict[addr] = {
                "name": name,
                "is_optomized_out": s.is_optimized_out,
                "type": s.type.name,
                "stripped_type": s.type.strip_typedefs().name,
                "dynamic_type": s.dynamic_type.name,
            }
            if s.type.code == gdb.TYPE_CODE_STRUCT:
                self._structDict[addr] = self._valueDict.pop(addr)
                for f in s.type.fields():
                    self._serialize_value(s[f.name], name + "." + f.name)
                self._valueDict[addr]["value"] = str(s.address)
            elif s.type.code == gdb.TYPE_CODE_ARRAY:
                self._arrayDict[addr] = self._valueDict.pop(addr)
                self._arrayDict[addr]["range"] = s.type.range()
                self._arrayDict[addr]["target_type"] = s.type.target().name
                for i in range(s.type.range()[1] + 1):
                    self._serialize_value(s[i], name + "[" + str(i) + "]" )
            elif s.type.code == gdb.TYPE_CODE_PTR:
                try:
                    self._valueDict[addr]["value"] = str(s)
                    self._serialize_value(s.dereference(), "(*" + name + ")")
                except gdb.MemoryError as e:
                    if str(s) == "0x0":
                        self._valueDict[addr]["value"] = "nullptr"
                    else:
                        self._valueDict[addr]["value"] = str(e)
            else:
                self._valueDict[addr]["value"] = str(s)


    def serialize_locals(self):
        self._get_local_vars()
        for k, v in self.gdbVars.items():
            self._serialize_value(v, k)

        return (self._valueDict, self._structDict, self._arrayDict)

    def __str__(self):
        self._pp.pprint(self.serialize_locals())

# pp.pprint(serialize_locals())
m = MemoryState()
state = m.serialize_locals()
m._pp.pprint(state)

