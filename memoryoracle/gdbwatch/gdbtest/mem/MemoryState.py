#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import ast
import pickle
import json
import pprint
import exceptions

class MemoryState(object):

    values = dict()
    structs = dict()
    arrays = dict()
    gdbVars = dict()
    _pp = pprint.PrettyPrinter(indent=3)

    def __init__(self):
        pass

    @staticmethod
    def struct_to_dict(s):
        if s.type.code == gdb.TYPE_CODE_STRUCT:
            return { f.name: MemoryState.struct_to_dict(s[f.name]) for f in s.type.fields() }
        else:
            return s

    @staticmethod
    def get_local_vars(self):
        localString = gdb.execute("info locals", False, True)
        transform = re.sub(r'([a-zA-Z_][0-9a-zA-Z_:]*) \= .*\n', r"'\1', ", localString)
        if transform[-2:] is ", ":
            transform = transform[:-2]
        transform = "(" + transform + ")"
        localVars = ast.literal_eval(transform)
        MemoryState.gdbVars = \
            { v: gdb.parse_and_eval(v) for v in localVars }

    @staticmethod
    def serialize_value(s, name):
        addr = str(s.address)
        if addr not in self.values:
            s.fetch_lazy()
            MemoryState.values[addr] = {
                "name": name,
                "is_optimized_out": s.is_optimized_out,
                "type": s.type.name,
                "stripped_type": s.type.strip_typedefs().name,
                "dynamic_type": s.dynamic_type.name,
            }
            if s.type.code == gdb.TYPE_CODE_STRUCT:
                MemoryState.structs[addr] = MemoryState.values.pop(addr)
                for f in s.type.fields():
                    MemoryState.serialize_value(s[f.name], name + "." + f.name)
                MemoryState.values[addr]["value"] = str(s.address)
            elif s.type.code == gdb.TYPE_CODE_ARRAY:
                MemoryState.arrays[addr] = MemoryState.values.pop(addr)
                MemoryState.arrays[addr]["range"] = s.type.range()
                MemoryState.arrays[addr]["target_type"] = s.type.target().name
                for i in range(s.type.range()[1] + 1):
                    MemoryState.serialize_value(s[i], name + "[" + str(i) + "]" )
            elif s.type.code == gdb.TYPE_CODE_PTR:
                try:
                    MemoryState.values[addr]["value"] = \
                            MemoryState.val_to_string(name)
                    MemoryState.serialize_value(s.dereference(), "(*" + name + ")")
                except gdb.MemoryError as e:
                    if str(s) == "0x0":
                        MemoryState.values[addr]["value"] = "nullptr"
                    else:
                        MemoryState.values[addr]["value"] = \
                                MemoryState.val_to_string(name)
            else:
                MemoryState.values[addr]["value"] = \
                        MemoryState.val_to_string(name)

    @staticmethod
    def update(s = None, name = None):
        addr = str(s.address)
        if s is not None and name is not None:
            if s.type.code == gdb.TYPE_CODE_STRUCT:
                MemoryState.structs.pop(addr)
                for f in s.type.fields():
                    MemoryState.update(s[f.name], name + "." + f.name)


        elif s is not None
            raise Exception("Can not update without variable name")

        else:
            # back up the old dicts
            oldValues = MemoryState.values
            oldArrays = MemoryState.arrays
            oldStructs = MemoryState.structs

            # clear the dicts
            MemoryState.values = dict()
            MemoryState.arrays = dict()
            MemoryState.structs = dict()

            # refill the dicts
            MemoryState.serialize_locals()

            # update
            oldValues.update(MemoryState.values)
            oldArrays.update(MemoryState.arrays)
            oldStructs.update(MemoryState.structs)

            # restore
            MemoryState.values = oldValues
            MemoryState.arrays = oldArrays
            MemoryState.structs = oldStructs


    @staticmethod
    def val_to_string(name):
        v = gdb.parse_and_eval(name)
        # get gdb to print the value
        gdbPrint = gdb.execute("print " + name, False, True)
        # strip off noise at the start
        ansSections = gdbPrint[:-1].split(" = ")[1:]
        return " ".join(ansSections)

    @staticmethod
    def __getitem__(key):
        if key in MemoryState.arrays:
            return MemoryState.arrays[key]
        if key in MemoryState.structs:
            return MemoryState.structs[key]
        return MemoryState.values[key]

    @staticmethod
    def serialize_locals():
        MemoryState._get_local_vars()
        for k, v in MemoryState.gdbVars.items():
            MemoryState.serialize_value(v, k)

    @staticmethod
    def watch_locals():
        MemoryState.serialize_locals()

    @staticmethod
    def display():
        print("Structs:")
        MemoryState._pp.pprint(MemoryState.structs)
        print("Arrays:")
        MemoryState._pp.pprint(MemoryState.values)
        print("Values:")
        MemoryState._pp.pprint(MemoryState.values)
