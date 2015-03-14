#!/usr/bin/env python3
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
from copy import deepcopy

class StateFinish(gdb.FinishBreakpoint):

    def __init__(self, frame):
        super(StateFinish, self).__init__(frame, internal = True)
        self.frameName = str(frame)
        self.silent = True

    def stop(self):
        state = State._instances.get(self.frameName, None)
        if not state:
            print("Frame name not found " + self.frameName)
            return False
        for wp in state.watchers.values():
            wp.delete()
        State._instances.pop(self.frameName)
        return False


class StateWatcher(gdb.Breakpoint):

    def __init__(self, addr, name):
        super(StateWatcher, self).__init__("*" + addr,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True
        self.name = name

    def stop(self):
        frameName = str(gdb.selected_frame())
        addr = self.expression[1:]
        state = State._instances.get(frameName, None)

        if not state:
            state = State()
            c = state.serialize_locals()
            if not c:
                return False

        try:
            val = state.name_to_val(self.name)
            names = state.get_serial(val = val).keys()
            for name in names:
                state.update(val, name)

        except Exception as e:
            traceback.print_exc()
            state.serialize(self.name, address = addr)
            print("ERROR: could not find address " + addr)
        return False

class StateCatch(gdb.Breakpoint):

    trackedFrames = dict()

    def __init__(self, breakCond, frame = None):
        super(StateCatch, self).__init__(breakCond, internal=True)
        self.silent = True
        self.frame = str(frame) if frame else str(gdb.selected_frame())

    def stop(self):
        s = State()
        s.serialize_locals()

class State(object):

    _pp = pprint.PrettyPrinter(indent=3)

    _addressFixer = re.compile(r" <.*>")
    _spaceFixer = re.compile(r" ")

    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _quoteFinder = re.compile(r"^(\".*\")")
    _arrayFinder = re.compile(r"(.*) ((?:\[\d*\])+)")

    _intType = gdb.lookup_type("int")

    _classifications = { "array": set(), "struct": set(), "pointer": set() }

    _instances = dict()

    _objectDictionary = dict()

    class FrameSelector(object):
        def __init__(self, frame):
            self.frame = frame

        def __enter__(self):
            self.oldFrame = gdb.selected_frame()
            self.frame.select()


        def __exit__(self, type, value, tb):
            self.oldFrame.select()

    def __init__(self):
        self.frame = gdb.selected_frame()
        self.frameName = str(self.frame)
        self.frames = dict()
        self.values = dict()
        self.structs = dict()
        self.arrays = dict()
        self.symbols = dict()
        self.localVariables = dict()
        self.watchers = dict()
        self.pointers = dict()

        self._updatedValues = set()
        self._updatedStructs = set()
        self._updatedArrays = set()
        self._updatedPointers = set()
        self._updatedNames = set()

        State._instances[self.frameName] = self

        try:
            self.finish = StateFinish(self.frame)
        except ValueError as e:
            self.finish = None

    @staticmethod
    def _merge_dicts(d1, d2):
        for k, v in d2.items():
            if k in d1:
                typ1 = type(d1[k])
                typ = type(v)
                # multiTypes = set([ type(int()), type(long()), type(str("")), type(float(0.)) ])
                # if typ1 == type(set()) and typ in multiTypes:
                #     d1[k].add(v)
                #     return

                if typ1 != typ:
                    raise Exception("Not compat dict " + str(typ1) + " != " + str(typ) + "," + str(d1[k]) + " <merged " + str(d2[k]))

                if typ == type(set()):
                    d1[k] &= v
                elif typ == type(dict()):
                    State._merge_dicts(d1[k], d2[k])
                elif typ == type(list()):
                    d1[k] += d2[k]
                elif typ == type(str("")):
                    d1[k] = d2[k]
                elif typ == type(tuple()):
                    d1[k] = d2[k]
                else:
                    d1[k] = d2[k]
            else:
                d1[k] = d2[k]
            print(d1[k])

    @staticmethod
    def display_global():
        State._pp.pprint(State._objectDictionary)

    @staticmethod
    def global_state():
        return State._objectDictionary

    def _add_to_global_track(self, addr):
        v = self.values.get(addr, None)
        s = self.structs.get(addr, None)
        a = self.arrays.get(addr, None)
        p = self.pointers.get(addr, None)

        updateDict = dict()

        if v is not None:
            updateDict["values"] = v
        if s is not None:
            updateDict["structs"] = s
        if a is not None:
            updateDict["arrays"] = a
        if p is not None:
            updateDict["pointers"] = p

        if addr not in State._objectDictionary:
            State._objectDictionary[addr] = updateDict
        else:
            # State._pp.pprint(State._objectDictionary)
            State._objectDictionary[addr].update(updateDict)
            # State._merge_dicts(State._objectDictionary[addr], updateDict)

    def _basic_serialize(self, v, name, addr, repo, updateTracker, parent = None, parentClassification = None):

        if name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(name)

        if parent is not None and parentClassification is None:
            raise Exception("No parent classification!")

        if addr not in updateTracker:
            v.fetch_lazy()
            updateTracker.add(addr)
            if addr not in repo:
                repo[addr] = {
                        name: {
                            "type": { State._extract_class(v.type) },
                            "parents": { parentClassification: { parent } } \
                                    if parent else deepcopy(State._classifications),
                            "frames": { self.frameName },
                        }
                }
                if parentClassification is not None:
                    if parent not in repo[addr][name]["parents"][parentClassification]:
                        repo[addr][name]["parents"][parentClassification].add(parent)
                    else:
                        return False
                return True
            else:
                if name in repo[addr]:
                    repo[addr][name]["type"].add(State._extract_class(v.type))
                    repo[addr][name]["frames"].add(self.frameName)
                    if parent:
                        repo[addr][name]["parents"][parentClassification].add(parent)
                else:
                    repo[addr][name] = {
                            "type": { State._extract_class(v.type) },
                            "parents": { parentClassification: { parent } } \
                                    if parent else deepcopy(State._classifications),
                            "frames": { self.frameName },
                        }
                return True

    def _true_type(self, name):
        v = self.name_to_val(name)
        atyp = State._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            dims = map(int, atyp.group(2)[1:-1].split("]["))
            t = gdb.lookup_type(typ)
            for dim in dims:
                t = t.array(dim - 1)
            return t

        valString = self.name_to_valstring(name)
        ptyp = State._pointerFinder.match(valString)
        if ptyp:
            typ = State._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return gdb.lookup_type(typ).pointer()

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

    def get_local_vars(self):
        if self.frame.is_valid():
            try:
                block = self.frame.block()
                self.symbols = { str(sym) : sym for sym in block }
                self.localVariables = { str(sym): sym.value(self.frame) for sym in block }
                return True
            except RuntimeError as e:
                block = None
                self.symbols = dict()
                self.localVariables = dict()
                return False
        else:
            raise Exception("Frame no longer valid")

    def _serialize_value(self, s, name, addr,
            parent = None, parentClassification = None):
        c = self._basic_serialize(s, name, addr, self.values, self._updatedValues,
            parent = parent,
            parentClassification = parentClassification)

        # State._updatedValues.add(addr)
        val = self.name_to_valstring(name)
        self.values[addr][name]["value"] = val
        strip = s.type.strip_typedefs()
        if strip != s.type:
            self.values[addr][name]["stripped_type"] = strip.name
        dynamic = s.dynamic_type
        if dynamic != s.type:
            self.values[addr][name]["dynamic_type"] = dynamic.name

    def _serialize_struct(self, s, name, addr,
            parent = None, parentClassification = None):
        if addr not in self._updatedStructs:
            c = self._basic_serialize(s, name, addr, self.structs,
                    self._updatedStructs,
                    parent = parent,
                    parentClassification = parentClassification)
            self.structs[addr][name]["children"] = \
                { f.name: self.get_address(s[f.name]) for f in s.type.fields() }
            for f in s.type.fields():
                self.serialize(name + "." + f.name, parent = addr,
                        parentClassification = "struct")

    def _serialize_array(self, s, name, addr,
            parent = None, parentClassification = None):

        if addr not in self._updatedArrays:

            c = self._basic_serialize(s, name, addr, self.arrays,
                    self._updatedArrays,
                    parent = parent,
                    parentClassification = parentClassification)

            self.arrays[addr][name]["range"] = s.type.range()
            targetType = State._extract_target_type(s.type)
            self.arrays[addr][name]["target_type"] = targetType
            immediateTarget = s.type.target().name
            if immediateTarget is None:
                # TODO: use codes instead of try catch
                try:
                    r = s.type.target().range()
                    self._updatedArrays.remove(addr)
                except gdb.error as e:
                    self._updatedPointers.discard(addr)
            length = s.type.range()[1] - s.type.range()[0] + 1
            # State.arrays[addr][name]["children"] = \
            #     { i: State.get_address(s[i]) for i in range(length) }
            for i in range(length):
                self.serialize(name + "[" + str(i) + "]",
                    parent = addr,
                    parentClassification = "array")


    def _serialize_pointer(self, s, name, addr,
            parent = None, parentClassification = None):
        if addr not in self._updatedPointers:

            c = self._basic_serialize(s, name, addr, self.pointers,
                    self._updatedPointers,
                    parent = parent,
                    parentClassification = parentClassification)
            self._updatedPointers.add(addr)
            try:
                val = self.name_to_valstring(name)
                val = State._addressFixer.sub("", val)
                self.pointers[addr][name]["value"] = val
                self.serialize("(*" + name + ")",
                        parent = addr,
                        parentClassification = "pointer")
            except gdb.MemoryError as e:
                pass
        else:
            if parent:
                self.pointers[addr][name]["parents"][parentClassification].add(
                        parent)

    def _serialize_int(self, s, name, addr, parent = None, parentClassification = None):
        typ = self._true_type(name)
        v = s.cast(typ)
        if typ.code == gdb.TYPE_CODE_PTR:
            self._serialize_pointer(v, name, addr, parent = addr,
                    parentClassification = "pointer")
        elif typ.code == gdb.TYPE_CODE_ARRAY:
            self._serialize_array(v, name, addr, parent = addr,
                    parentClassification = "array")
        elif typ.code == gdb.TYPE_CODE_STRUCT:
            self._serialize_struct(v, name, addr, parent = parent,
                    parentClassification = parentClassification)
        else:
            self._serialize_value(v, name, addr, parent = parent,
                    parentClassification = parentClassification)

    def serialize(self, name, parent = None, address = None, parentClassification = None):

        s = self.name_to_val(name)

        if address is None:
            addr = self.get_address(s)
        else:
            addr = address

        if s.type.code == gdb.TYPE_CODE_PTR:
            self._serialize_pointer(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        elif s.type.code == gdb.TYPE_CODE_ARRAY:
            p = addr if parent is None else parent
            self._serialize_array(s, name, addr,
                    parent = p,
                    parentClassification = "array")

        elif s.type.code == gdb.TYPE_CODE_STRUCT:
            self._serialize_struct(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        elif s.type.code == gdb.TYPE_CODE_INT:
            self._serialize_int(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        else:
            self._serialize_value(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        self.watch_memory(addr, name)
        self._add_to_global_track(addr)

    def _clear_updated(self, addr = None):
        if addr:
            self._updatedValues.pop(addr)
            self._updatedStructs.pop(addr)
            self._updatedArrays.pop(addr)
            self._updatedPointers.pop(addr)
        else:
            self._updatedValues.clear()
            self._updatedStructs.clear()
            self._updatedArrays.clear()
            self._updatedPointers.clear()


    def update(self, s = None, name = None, classification = None):

        if s is not None and name is None:
            raise Exception("Can not update without variable name")

        elif s is not None and name is not None:
            self._clear_updated()
            if name in self._updatedNames:
                return
            else:
                self._updatedNames.add(name)

            self.serialize(name)

            self._updatedNames.discard(name)

        else:
            self._clear_updated()
            # back up the old dicts
            oldValues = self.values
            oldArrays = self.arrays
            oldStructs = self.structs

            # clear the dicts
            self.values = dict()
            self.arrays = dict()
            self.structs = dict()

            # refill the dicts
            self.serialize_locals()

            # update
            oldValues.update(self.values)
            oldArrays.update(self.arrays)
            oldStructs.update(self.structs)

            # restore
            self.values = oldValues
            self.arrays = oldArrays
            self.structs = oldStructs

    def name_to_valstring(self, name):
        with State.FrameSelector(self.frame):
            gdbPrint = gdb.execute("print " + name, False, True)
            ansSections = gdbPrint[:-1].split(" = ")[1:]
            return " ".join(ansSections)

    def name_to_val(self, name):
        with State.FrameSelector(self.frame):
            return gdb.parse_and_eval(name)

    def get_serial(self, val = None, address = None, code = None):

        if code is not None and address is None:
            raise Exception("Can not get_serial from code without address")

        if code is None and address is not None:
            raise Exception("Can not get_serial from address without type code")

        addr = address if address is not None else self.get_address(val)
        cl = code if code is not None else val.type.code

        if cl == gdb.TYPE_CODE_PTR:
            ret = self.pointers[addr]
        elif cl == gdb.TYPE_CODE_STRUCT:
            ret = self.structs[addr]
        elif cl == gdb.TYPE_CODE_ARRAY:
            ret = self.arrays[addr]
        elif cl == gdb.TYPE_CODE_INT:
            ret = self.structs.get(addr, None)
            if not ret:
                ret = self.arrays.get(addr, None)
            if not ret:
                ret = self.pointers.get(addr, None)
            if not ret:
                ret = self.values.get(addr, None)
        else:
            ret = self.values.get(addr, None)

        return ret


    def serialize_locals(self):
        self._updatedNames.clear()
        self.get_local_vars()
        for k in self.localVariables:
            self.serialize(k)

    def display(self):
        print("Structs:")
        self._pp.pprint(self.structs)
        print("Arrays:")
        self._pp.pprint(self.arrays)
        print("Values:")
        self._pp.pprint(self.values)
        print("Pointers:")
        self._pp.pprint(self.pointers)

    def watch_memory(self, addr, name):
        try:
            self.watchers[addr] = StateWatcher(addr, name)
        except gdb.error as e:
            # TODO: figure out a better way to watch the other addresses
            print(e)

class StateSerializer(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return { "set": list(obj) }
        return json.JSONEncoder.default(self, StateSerializer.equal_fix(obj))

def stopped(event):
    state = State()
    state.serialize_locals()
    with open("arrays.json", "w") as outfile:
        json.dump(state.arrays, outfile, cls=StateSerializer)
    with open("pointers.json", "w") as outfile:
        json.dump(state.pointers, outfile, cls=StateSerializer)
    with open("structs.json", "w") as outfile:
        json.dump(state.structs, outfile, cls=StateSerializer)
    with open("values.json", "w") as outfile:
        json.dump(state.values, outfile, cls=StateSerializer)

gdb.events.stop.connect(stopped)
