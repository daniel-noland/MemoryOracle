#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import TrackedByAddress

class TrackedValue(TrackedByAddress.TrackedByAddress):

    _updatedNames = set()

    def _basic_serialize(self):

        if self.name in TrackedByAddress._updatedNames:
            return False
        else:
            TrackedByAddress._updatedNames.add(name)

        if self.parent is not None and self.parentClassification is None:
            raise Exception("No parent classification!")

        if self.address not in self._updateTracker:
            # self.fetch_lazy()
            self._updateTracker.add(self.address)
            if self.address not in self._instances:
                self._instances[self.address] = {
                        self.name: {
                            "type": { State._extract_class(v.type) },
                            "parents": { self.parentClassification: { self.parent } } \
                                    if self.parent else deepcopy(TrackedByAddress._classifications),
                            "frames": { self.frame.index },
                        }
                }
                if self.parentClassification is not None:
                    if self.parent not in self._instances[self.address][self.name]["parents"][self.parentClassification]:
                        self._instances[self.address][self.name]["parents"][self.parentClassification].add(self.parent)
                    else:
                        return False
                return True
            else:
                if self.name in self._instances[self.address]:
                    self._instances[self.address][self.name]["type"].add(State._extract_class(v.type))
                    self._instances[self.address][self.name]["frames"].add(self.frame.index)
                    if self.parent:
                        self._instances[self.address][self.name]["parents"][self.parentClassification].add(self.parent)
                else:
                    self._instances[self.address][self.name] = {
                            "type": { State._extract_class(v.type) },
                            "parents": { self.parentClassification: { self.parent } } \
                                    if self.parent else deepcopy(TrackedByAddress._classifications),
                            "frames": { self.frame.index },
                        }
                return True

    def serialize(self):

        # if self.address is None:
        #     addr = self.get_address(s)
        # else:
        #     addr = self.address

        if self.type.code == gdb.TYPE_CODE_PTR:
            self._serialize_pointer(s)

        elif self.type.code == gdb.TYPE_CODE_ARRAY:
            p = addr if parent is None else parent
            self._serialize_array(s, name, addr,
                    parent = p,
                    parentClassification = parentClassification)

        elif self.type.code == gdb.TYPE_CODE_STRUCT:
            self._serialize_struct(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        elif self.type.code == gdb.TYPE_CODE_INT:
            self._serialize_int(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        else:
            self._serialize_value(s, name, addr,
                    parent = parent,
                    parentClassification = parentClassification)

        self.watch_memory(addr, name)
        # self._add_to_global_track(addr)


    def _serialize_pointer(self):

        addr = self.address

        if addr not in self._updatedPointers:

            c = self._basic_serialize()

            TrackedValue._updatedPointers.add(addr)

            try:
                val = TrackedValue._addressFixer.sub("", self.value_string())
                self.pointers[addr][name]["value"] = val
                TrackedValue("(*" + name + ")", frame = self.frame,
                        parent = addr,
                        parentClassification = "pointer")
            except gdb.MemoryError as e:
                pass

        else:

            if self.parent:
                self.pointers[addr][name]["parents"][parentClassification].add(
                        self.parent)

