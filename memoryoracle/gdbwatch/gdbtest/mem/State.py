#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import gdb.types
import re
import ast
import pickle
import json
import pprint
import exceptions
import traceback

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
        try:
            names = State.get(addr[1:]).keys()
            for name in names:
                State.update(val, name)

        except Exception as e:
            traceback.print_exc()
            print("ERROR: could not find address " + addr[1:])
            print("ERROR: val = " + str(val))
            # State.serialize(val, addr)
        return False

class State(object):

    values = dict()
    structs = dict()
    arrays = dict()
    gdbVars = dict()
    watchers = dict()
    sources = dict()
    pointers = dict()

    _updatedValues = set()
    _updatedStructs = set()
    _updatedArrays = set()
    _updatedPointers = set()

    _pp = pprint.PrettyPrinter(indent=3)

    _addressFixer = re.compile(r" <.*>")
    _spaceFixer = re.compile(r" ")

    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _quoteFinder = re.compile(r"^(\".*\")")
    _arrayFinder = re.compile(r"(.*) (\[\d*\])")

    _intType = gdb.lookup_type("int")

    _classifications = { "array": set(), "struct": set(), "pointer": set() }

    @staticmethod
    def _basic_serialize(v, name, addr, repo, updateTracker, parent = None, parentClassification = None):

        # if (parent is not None and parentClassification is None:
        #     raise Exception("No parent classification!")

        v.fetch_lazy()

        if addr not in updateTracker:
            updateTracker.add(addr)
            if addr not in repo:
                repo[addr] = {
                    name: {
                        "type": { State._extract_class(v.type) },
                        "parents": State._classifications,
                    }
                }
                if parentClassification is not None:
                    if parent not in repo[addr][name]["parents"][parentClassification]:
                        repo[addr][name]["parents"][parentClassification].add(parent)
                        return True
                    else:
                        return False
            else:
                if name in repo[addr]:
                    repo[addr][name]["type"].add(State._extract_class(v.type))
                    repo[addr][name]["parents"][parentClassification].add(parent)
                    return False
                else:
                    repo[addr][name] = {
                            "type": { State._extract_class(v.type) },
                            "parents": { parentClassification: { parent } } \
                                    if parentClassification else classifications
                        }
                    return True

    @staticmethod
    def _true_type(name):
        v = gdb.parse_and_eval(name)
        print("Extracting _true_type from " + str(v.type) + " (" + name + ")")
        valString = State.val_to_string(name)

        if v.type.code == gdb.TYPE_CODE_ARRAY:
            print("-"*20)
            print("FOUND ARRAY!!!")
            print("-"*20)

        ptyp = State._pointerFinder.match(valString)
        if ptyp:
            typ = State._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return gdb.lookup_type(typ).pointer()

        atyp = State._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            print(atyp.group(1))
            print(atyp.group(2))
            length = int(atyp.group(2)[1:-1])
            print("int was actually a " + typ + "[" + str(length) + "]")
            return gdb.lookup_type(typ).array(length - 1)
        else:
            return gdb.lookup_type("int")

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
    def _extract_target_type(t):
        if t.code == gdb.TYPE_CODE_PTR or t.code == gdb.TYPE_CODE_ARRAY:
            return State._extract_target_type(t.target())
        return t.name

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
    def _serialize_value(s, name, addr, parent = None, parentClassification = None):
        State._basic_serialize(s, name, addr, State.values, State._updatedValues,
            parent = parent,
            parentClassification = parentClassification)

        # State._updatedValues.add(addr)
        val = State.val_to_string(name)
        State.values[addr][name]["value"] = val
        strip = s.type.strip_typedefs()
        if strip != s.type:
            State.values[addr][name]["stripped_type"] = strip.name
        dynamic = s.dynamic_type
        if dynamic != s.type:
            State.values[addr][name]["dynamic_type"] = dynamic.name

    @staticmethod
    def _serialize_struct(s, name, addr, parent = None, parentClassification = None):
        if addr not in State._updatedStructs:
            c = State._basic_serialize(s, name, addr, State.structs,
                    State._updatedStructs,
                    parent = parent,
                    parentClassification = parentClassification)
            State.structs[addr][name]["children"] = \
                { f.name: State.get_address(s[f.name]) for f in s.type.fields() }
            for f in s.type.fields():
                State.serialize(s[f.name], name + "." + f.name, parent = addr)

    @staticmethod
    def _serialize_array(s, name, addr, parent = None, parentClassification = None):

        if addr not in State._updatedArrays:

            c = State._basic_serialize(s, name, addr, State.arrays,
                    State._updatedArrays,
                    parent = parent,
                    parentClassification = parentClassification)

            State.arrays[addr][name]["range"] = s.type.range()
            targetType = State._extract_target_type(s.type)
            State.arrays[addr][name]["target_type"] = targetType
            immediateTarget = s.type.target().name
            if immediateTarget is None:
                try:
                    r = s.type.target().range()
                    print("Found multidimensional array in " + name)
                    State._updatedArrays.remove(addr)
                except gdb.error as e:
                    print(e)
                    print("Likely found an array of pointers in " + name)
                    State._updatedPointers.discard(addr)
            length = s.type.range()[1] - s.type.range()[0] + 1
            State.arrays[addr][name]["children"] = \
                { i: State.get_address(s[i]) for i in range(length) }
            for i in range(length):
                State.serialize(s[i], name + "[" + str(i) + "]",
                    parent = addr,
                    parentClassification = "array")


    @staticmethod
    def _serialize_pointer(s, name, addr, parent = None, parentClassification = None):
        if addr not in State._updatedPointers:

            c = State._basic_serialize(s, name, addr, State.pointers,
                    State._updatedPointers,
                    parent = parent,
                    parentClassification = parentClassification)
            State._updatedPointers.add(addr)
            try:
                val = State.val_to_string(name)
                val = State._addressFixer.sub("", val)
                State.pointers[addr] = {
                    "value": val,
                    "name": name,
                    "type": State._extract_class(s.type),
                    "parents": { parent } if parent else set()
                    }
                State.sources[val] = addr
                State.serialize(s.dereference(), "(*" + name + ")", parent = addr,
                        parentClassification = "pointer")
            except gdb.MemoryError as e:
                print(e)
        else:
            if parent:
                State.pointers[addr][name]["parents"][parentClassification].add(parent)

    @staticmethod
    def _serialize_int(s, name, addr, parent = None, parentClassification = None):
        typ = State._true_type(name)
        v = s.cast(typ)
        if typ == State._intType:
            State._serialize_value(v, name, addr, parent = parent,
                    parentClassification = parentClassification)
        else:
            State.serialize(v, name, parent = addr, address = addr,
                    parentClassification = parentClassification)

    @staticmethod
    def serialize(s, name, parent = None, address = None, parentClassification = None):

        if address is None:
            addr = State.get_address(s)
        else:
            addr = address

        if s.type.code == gdb.TYPE_CODE_PTR:
            print("Found " + name + " as pointer")
            State._serialize_pointer(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        elif s.type.code == gdb.TYPE_CODE_ARRAY:
            print("Found " + name + " as array")
            if parent is None:
                p = addr
            State._serialize_array(s, name, addr,
                    parent = parent,
                    parentClassification = "array")

        elif s.type.code == gdb.TYPE_CODE_STRUCT:
            print("Found " + name + " as struct")
            State._serialize_struct(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification
                    )

        elif s.type.code == gdb.TYPE_CODE_INT:
            print("Found " + name + " as int")
            # try:
            #     sStar = gdb.parse_and_eval("*" + name)
            #     print(name + " was actually a pointer")
            #     State.serialize(sStar, "*" + name)
            # except Exception as e:
            State._serialize_int(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        else:
            print("Found " + name + " as value")
            State._serialize_value(s, name, addr, parent = parent)

        State.watch_memory(addr)

    @staticmethod
    def _clear_updated():
        State._updatedValues.clear()
        State._updatedStructs.clear()
        State._updatedArrays.clear()
        State._updatedPointers.clear()


    @staticmethod
    def update(s = None, name = None):

        if s is not None and name is None:
            raise Exception("Can not update without variable name")

        elif s is not None and name is not None:
            State._clear_updated()
            addr = State.get_address(s)
            State.serialize(s, name)

        else:
            State._updates.clear()
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
    def get(key):
        if key in State.pointers:
            return { "val": State.pointers[key], "found_in": "pointers" }
        elif key in State.arrays:
            return { "val": State.arrays[key], "found_in": "arrays" }
        elif key in State.structs:
            return { "val": State.structs[key], "found_in": "structs" }
        elif key in State.values:
            return { "val": State.values[key], "found_in": "values" }
        else:
            raise Exception("---unknown address---")

    @staticmethod
    def serialize_locals():
        State.get_local_vars()
        for k, v in State.gdbVars.items():
            State.serialize(v, k)

    @staticmethod
    def display():
        print("Structs:")
        State._pp.pprint(State.structs)
        print("Arrays:")
        State._pp.pprint(State.arrays)
        print("Values:")
        State._pp.pprint(State.values)
        print("Pointers:")
        State._pp.pprint(State.pointers)

    @staticmethod
    def watch_memory(addr):
        try:
            State.watchers[addr] = StateWatcher(addr)
        except gdb.error as e:
            # TODO: figure out a better way to watch the other addresses
            print(e)


State.serialize_locals()
