#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import ast
import pickle
import json
import pprint
import exceptions

class StateWatcher(gdb.Breakpoint):

    def __init__(self, addr):
        super(StateWatcher, self).__init__("*" + addr,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True

    def stop(self):
        addr = self.expression
        val = gdb.parse_and_eval(addr)
        name = State.values[addr[1:]]["name"]
        State.update(val, name)
        return False

class State(object):

    values = dict()
    structs = dict()
    arrays = dict()
    gdbVars = dict()
    watchers = dict()
    sources = dict()
    pointers = dict()

    _pp = pprint.PrettyPrinter(indent=3)
    _addressFixer = re.compile(r" <.*>")
    _classExtractor = re.compile(r"(\(.*\))")

    @staticmethod
    def get_address(s):
        return State._addressFixer.sub("", str(s.address))

    @staticmethod
    def _extract_class(t, nameDecorators = ""):
        if t.code == gdb.TYPE_CODE_PTR:
            return State._extract_class(t.target(), nameDecorators + "*")
        elif t.code == gdb.TYPE_CODE_ARRAY:
            length = str(t.range()[1] - t.range()[0] + 1)
            return State._extract_class(t.target(), nameDecorators + "[" + length + "]")
        else:
            return t.name + nameDecorators

    @staticmethod
    def struct_to_dict(s):
        if s.type.code == gdb.TYPE_CODE_STRUCT:
            return { f.name: State.struct_to_dict(s[f.name]) for f in s.type.fields() }
        else:
            return s

    @staticmethod
    def get_local_vars():
        localString = gdb.execute("info locals", False, True)
        transform = re.sub(r'([a-zA-Z_][0-9a-zA-Z_:]*) \= .*\n', r"'\1', ", localString)
        if transform[-2:] is ", ":
            transform = transform[:-2]
        transform = "(" + transform + ")"
        localVars = ast.literal_eval(transform)
        State.gdbVars = \
            { v: gdb.parse_and_eval(v) for v in localVars }


    @staticmethod
    def _serialize_struct(s, name, addr):
        State.structs[addr] = State.values.pop(addr)
        State.structs[addr]["children"] = \
                [ State.get_address(s[f.name])
                        for f in s.type.fields() ]
        for f in s.type.fields():
            State.serialize_value(s[f.name], name + "." + f.name)
        State.structs[addr]["value"] = addr

    @staticmethod
    def _serialize_array(s, name, addr):
        print("Array found")
        State.arrays[addr] = State.values.pop(addr)
        State.arrays[addr]["range"] = s.type.range()
        State.arrays[addr]["target_type"] = s.type.target().name
        length = s.type.range()[1] + 1
        State.arrays[addr]["children"] = [ State.get_address(s[i]) for i in range(length) ]
        for i in range(length):
            State.serialize_value(s[i], name + "[" + str(i) + "]")


    @staticmethod
    def _serialize_pointer(s, name, addr):
        try:
            val = State._addressFixer.sub("", State.values[addr]["value"])
            State.pointers[addr] = val
            State.sources[val] = addr
            State.serialize_value(s.dereference(), "(*" + name + ")")
        except gdb.MemoryError as e:
            print(e)

    @staticmethod
    def serialize_value(s, name, parentAddress = None):
        addr = State.get_address(s)
        if addr not in State.values:
            s.fetch_lazy()
            # Consider moving this down for speed
            val = State.val_to_string(name)
            ###
            State.values[addr] = {
                "name": name,
                "type": State._extract_class(s.type),
                "value": val,
                }
            strip = s.type.strip_typedefs()
            if strip != s.type:
                State.values[addr]["stripped_type"] = strip.name
            dynamic = s.dynamic_type
            if dynamic != s.type:
                State.values[addr]["dynamic_type"] = dynamic.name

            if s.type.code == gdb.TYPE_CODE_STRUCT:
                State._serialize_struct(s, name, addr)

            elif s.type.code == gdb.TYPE_CODE_ARRAY:
                State._serialize_array(s, name, addr)

            elif s.type.code == gdb.TYPE_CODE_PTR:
                State._serialize_pointer(s, name, addr)

            State.watch_memory(addr)

    @staticmethod
    def update(s = None, name = None):

        if s is not None and name is not None:
            addr = State.get_address(s)
            if addr in State.values:
                State.values.pop(addr)
            State.serialize_value(s, name)

        elif s is not None and name is None:
            raise Exception("Can not update without variable name")

        else:
            # back up the old dicts
            oldValues = State.values
            oldArrays = State.arrays
            oldStructs = State.structs

            # clear the dicts
            State.values = dict()
            State.arrays = dict()
            State.structs = dict()

            # refill the dicts
            State.serialize_locals()

            # update
            oldValues.update(State.values)
            oldArrays.update(State.arrays)
            oldStructs.update(State.structs)

            # restore
            State.values = oldValues
            State.arrays = oldArrays
            State.structs = oldStructs

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
        if key in State.arrays:
            return State.arrays[key]
        if key in State.structs:
            return State.structs[key]
        return State.values[key]

    @staticmethod
    def serialize_locals():
        State.get_local_vars()
        for k, v in State.gdbVars.items():
            State.serialize_value(v, k)

    @staticmethod
    def display():
        print("Structs:")
        State._pp.pprint(State.structs)
        print("Arrays:")
        State._pp.pprint(State.arrays)
        print("Values:")
        State._pp.pprint(State.values)

    @staticmethod
    def watch_memory(addr):
        try:
            State.watchers[addr] = StateWatcher(addr)
        except gdb.error as e:
            # TODO: figure out a better way to watch the other addresses
            print(e)


State.serialize_locals()
