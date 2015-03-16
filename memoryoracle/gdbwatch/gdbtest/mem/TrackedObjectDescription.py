#!/usr/bin/env python
# -*- encoding UTF-8 -*-

# GDB Imports
import gdb

# Memory Oracle Imports
from .FrameSelector import FrameSelector


class Description(object):

    _addressFixer = re.compile(r" <.*>")
    _spaceFixer = re.compile(r" ")

    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _quoteFinder = re.compile(r"^(\".*\")")
    _arrayFinder = re.compile(r"(.*) ((?:\[\d*\])+)")

    _intType = gdb.lookup_type("int")

    _classifications = { "array": set(), "struct": set(), "pointer": set(),
            "primative": set(), "function": set(), "method": set(),
            "type": set(), "typedef": set(), "template": set(), "union": set(),
            "enum": set(), "frame": set(), "symbol": set()}

    def __init__(self, name, frame = None, address = None,
            parent = None, parentClassification = None):


        self._trueTypeFound = False

        self._name = name
        self._address = address
        self._parent = parent
        self._parentClassification = parentClassification

        with FrameSelector(frame = frame) as fs:
            self._frame = fs.frame
            self._value = gdb.parse_and_eval(self.name)

        c = self.type.code

        if c == gdb.TYPE_CODE_INT or c == gdb.TYPE_CODE_PTR or \
           c == gdb.TYPE_CODE_ARRAY:
            self._targetType = self.target_type(update = True)
        else:
            self._targetType = None

        if self._address is not None and self.value.address is not None:
            error = "You must not specify the address of an object"
            error += " owned by the inferior.\n"
            error += "(This option exists for objects created by the debugger)"
            raise ValueError(error)

        if self.value.address is not None:
            self._address = self.value.address
        else:
            error = "No address available to Description!\n"
            error += "(you must specify an address for objects created by"
            error += " the debugger)"
            raise ValueError(error)

    @staticmethod
    def _compute_target_type(t):
        if t.code == gdb.TYPE_CODE_PTR or t.code == gdb.TYPE_CODE_ARRAY:
            return Description._compute_target_type(t.target())
        return t

    def target_type(self, update = False):
        if update:
            self._targetType = Description._compute_target_type(self.type)
        return self._targetType

    def target_type_name(self, update = False):
        return self.target_type(update = update).name

    def value_string(self):
        with FrameSelector(self.frame):
            gdbPrint = gdb.execute("print " + self.name, False, True)
            ansSections = gdbPrint[:-1].split(" = ")[1:]
            return " ".join(ansSections)

    def _true_type(self):
        v = self.gdb_value
        atyp = Description._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            dims = map(int, atyp.group(2)[1:-1].split("]["))
            t = gdb.lookup_type(typ)
            for dim in dims:
                t = t.array(dim - 1)
            return TrackedType(t)

        valString = self.value_string()
        ptyp = Description._pointerFinder.match(valString)
        if ptyp:
            typ = Description._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return TrackedType(gdb.lookup_type(typ).pointer())

        return TrackedType(v.type)

    @property
    def gdb_value(self):
        return self._value

    @property
    def is_optimized_out(self):
        return self.gdb_value.is_optimized_out

    @property
    def type(self):
        if not self._trueTypeFound:
            self._type = TrackedType(self._true_type())
            self._trueTypeFound = True
        return self._type

    @property
    def dynamic_type(self):
        return self.gdb_value.dynamic_type

    @property
    def is_lazy(self):
        return self.gdb_value.is_lazy

    def cast(self, typ):
        if isinstance(typ, TrackedType):
            return self.gdb_value.cast(typ.gdb_type)
        return self.gdb_value.cast(typ)

    def dereference(self):
        return self.gdb_value.dereference()

    def referenced_value(self):
        return self.gdb_value.referenced_type()

    def dynamic_cast(self, typ):
        return self.gdb_value.dynamic_cast(typ)

    def reinterpret_cast(self, typ):
        return self.gdb_value.reinterpret_cast(typ)

    def string(self, *args, **kwargs):
        return self.gdb_value.string(*args, **kwargs)

    def lazy_string(self, *args, **kwargs):
        return self.gdb_value.lazy_string(*args, **kwargs)

    def fetch_lazy(self):
        self.gdb_value.fetch_lazy()

    @property
    def frame(self):
        return self._frame
