#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb
import re
import descriptions
import registry
import models
import typed
import frame
import traceback
import mongoengine
from copy import deepcopy
import asyncio
import websockets
import pymongo
import logging
logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
"""
Classes and functions relating to extracting (pulling) data from the debugee
"""

class Pull(typed.Typed):

    _stdLibChecker = re.compile("^std::.*")
    _updatedNames = set()
    _watchers = dict()

    execution = models.Execution()
    execution.save()

    @property
    def description(self):
        return self._description

    @property
    def object(self):
        return self._object

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    @property
    def children(self):
        return self._children

    @property
    def range(self):
        return self._range

    @property
    def target_type(self):
        return self._target_type

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    @property
    def dynamic_type(self):
        return self._dynamic_type

    @property
    def unaliased_type(self):
        return self._unaliased_type

    @property
    def doc(self):
        return self._doc

    def __init__(self, description):
        self._description = description
        # self._object = self.description.object
        self._index = None
        self._name = self.description.name
        self._children = []
        self._range = (0, 1)
        self._target_type = None
        self._value = None
        self._frame = None
        self._execution = Pull.execution
        self._type = None
        self._dynamic_type = None
        self._unaliased_type = None
        self._relativeName = None
        self._frame = None
        self._object = None
        self._paramDict = dict()
        self._doc = None

    @classmethod
    def get_true_type_name(cls, t, nameDecorators = ""):
        if t.code == gdb.TYPE_CODE_PTR:
            return cls.get_true_type_name(t.target(), nameDecorators + "*")
        elif t.code == gdb.TYPE_CODE_ARRAY:
            length = str(t.range()[1] - t.range()[0] + 1)
            return cls.get_true_type_name(t.target(), nameDecorators + "[" + length + "]")
        else:
            if isinstance(t.name, str):
                return t.name + nameDecorators
            else:
                return "<## unknown type ##>"

    def extract_extra_type_info(self):
        strip = self.object.type.strip_typedefs()
        return (strip.name, self.object.dynamic_type)

    def pull(self):
        if self._basic_pull():
            self._pull()
            ## TODO: enable memory watchers
            # self._watchers[self.index] = MemoryWatcher(self)

    def save(self, update=True):
        if update:
            self.pull()

        self.paramDict = {
            "address": str(self.index),
            "name": str(self.name),
            "execution": self.execution,
            "type": str(self.type),
            "dynamic_type": str(self.dynamic_type),
            "unaliased_type": str(self.unaliased_type),
            "range_start": int(self.range[0]),
            "range_end": int(self.range[1])
        }
        self._save()
        self._doc = models.Memory(**self.paramDict)
        self._doc.save()

    def _basic_pull(self):
        if self.name in self._updatedNames:
            return False
        else:
            self._updatedNames.add(self.name)

        if (self.index is None) or (self.index == "?"):
            return False

        if self.index not in self._updateTracker:
            self._updateTracker.add(self.index)
            return True
        else:
            return False

    # def update(self):
    #     self._clear_updated()
    #     self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.index)

    @staticmethod
    def handler_factory(typ):
        # standardLib = Pull._stdLibChecker.match(
        #     Pull.get_true_type_name(typ))
        return registry.handler_lookup(typ.strip_typedefs().code)


class MemoryPull(Pull):

    _addressFixer = re.compile(r" .*")

    def __init__(self, description):
        super(MemoryPull, self).__init__(description)
        self._relativeName = description.relative_name
        self._frame = frame.Frame(description.frame)
        self._object = None

        with frame.Selector(self.frame.frame) as fs:
            sym = self.description.symbol
            if sym is not None:
                typ = sym.type
                if typ.code in {
                        gdb.TYPE_CODE_PTR,
                        gdb.TYPE_CODE_ARRAY,
                        gdb.TYPE_CODE_STRUCT,
                        gdb.TYPE_CODE_INT,
                        gdb.TYPE_CODE_FUNC,
                        }:
                    try:
                        self._object = sym.value(fs.frame.frame)
                    except TypeError:
                        print("DEBUG: TypeError detected!")
            else:
                try:
                    self._object = gdb.parse_and_eval(self.name)
                except gdb.error as e:
                    print("DEBUG:")
                    traceback.print_exc()
                    # pass

        if self.description.symbol and self.description.symbol.type:
            self._type_name = str(self.description.symbol.type)
        elif isinstance(self.object, gdb.Value):
            self._type_name = Pull.get_true_type_name(self.object.type)
        else:
            # TODO: This is for dev.  Remove in production code.
            self._type_name = "void"
            # raise Exception("Untyped memory", self)

        if self.index is None:
            if self.object is None:
                self._index = "?"
            else:
                self._index = str(self.object.address)
            print(self._index)

        # if self.object is not None:
        #     self._dynamic_type, self._stripped_type = \
        #             self.extract_extra_type_info()
        # else:
        #     self._dynamic_type = "?"
        #     self._stripped_type = "?"

    def _save(self):
        if self.frame:
            self._paramDict["frame"] = self.frame

    @property
    def dict(self):
        return { "name": self.name, "address": self.address,
                 "frame": str(self.frame), "type": self.type_name}
                 # "dynamic_type": self.dynamic_type.name,
                 # "stripped_type": self.stripped_type.name}

    @property
    def relative_name(self):
        return self._relativeName

    @property
    def type_name(self):
        return self._type_name

    @property
    def address(self):
        return self._address

    @property
    def object(self):
        return self._object

    @property
    def frame(self):
        return self._frame

    @property
    def stripped_type(self):
        return self._stripped_type

    @property
    def dynamic_type(self):
        return self._dynamic_type


class StructurePull(MemoryPull):
    """
    *Concrete" class representing a specific memory structure.

    This includes all instances of classes and structs in C++.
    It is worth noting that the first member variable of a
    memory structure has the same address as the memory structure,
    and may thus share a node in the memory topology.
    """

    _typeHandlerCode = gdb.TYPE_CODE_STRUCT
    _updateTracker = set()
    _watchers = dict()

    def _pull(self):
        name = deepcopy(str(self.name))
        if name[0] == "*":
            name = name[1:]
            marker = "->"
        else:
            marker = "."
        name += marker
        for f in self.object.type.fields():
            childDescription= descriptions.MemoryDescription(
                name + f.name,
                relativeName=marker)
            childHandler = Pull.handler_factory(f.type)
            childObj = childHandler(childDescription)
            childObj.save()
            self._children.append(childObj.doc)


    def _save(self, update=True):
        super(StructurePull, self)._save()
        if len(self.children) > 0:
            # TODO: This needs cyclic memory torture testing.
            for child in self.children:
                # TODO: find bug which makes this check necessary
                if child is not None:
                    child.save(update=update)
            self.paramDict["children"] = self.children


class ArrayPull(MemoryPull):

    repository = dict()
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_ARRAY

    def _pull(self):
        s = self.object

        # compute range of array in C sizeof(type) units
        self._range = s.type.range()

        # compute the type of data the array contains e.g. for float[2] the
        # answer is float for float[3][2][7] the answer is float
        print(self.type, type(self.type))
        self._target_type = target_type_name(s.type)

        # compute the immediate type of data the array contains.  e.g. for
        # float[2] the answer is float.  for float[3][2][7] the answer is
        # float[3][2]
        immediateTarget = s.type.target()

        # if the immediateTarget is an array type, then its first element will
        # have the same address as the current array.  Still, we want to treat
        # it as as different creature, so we remove the current address from
        # the updateTracker.

        # TODO: if the first element of the array is a pointer back to the
        # array, this may cause an infinite loop.  *This algorithm needs
        # torture testing.*
        if immediateTarget.code == gdb.TYPE_CODE_ARRAY:
            self._updateTracker.remove(self.index)

        # CONCERN: This should always be correct, but I
        # can't think of a time when the first value of
        # range would be non zero.  Still, this costs
        # very little, and if we support some "1 indexed"
        # langauge, then the algorithm should still work.
        children = []
        childHandler = Pull.handler_factory(immediateTarget)
        for i in range(self.range[0], self.range[1] + 1):
            relativeName = "[" + str(i) + "]"
            childName = self.name + relativeName
            childDesc = descriptions.MemoryDescription(
                childName,
                relativeName=relativeName)
            childObj = childHandler(childDesc)
            childObj.save()
            self._children.append(childObj.doc)

    def _save(self, update=True):

        if len(self.children) > 0:
            # TODO: This needs cyclic memory torture testing.
            # for child in self.children:
            #     child.save(update=update)
            self.paramDict["children"] = self.children


class PrimitivePull(MemoryPull):
    """
    *Abstract* class to represent a primitive data type in the debugge.

    NOTE: Primitive data types are directly printable types such as int and
    double.
    """

    # def __init__(self):
    #     super(PrimitivePull, self).__init__()
    #     self.value = self.val_string()

    def val_string(self):
        """
        Get the printed value of a primitive object
        """
        with frame.Selector(self.frame.frame) as s:
            ## TODO: Find a way to print values without messing with the $# vars
            # in the gdb interface.
            gdbPrint = gdb.execute("print " + self.name, False, True)
            ## TODO: If we can't fix the $# var, we may as well use it.
            ## this is free information we may as well store for the user's use.
            ansSections = gdbPrint[:-1].split(" = ")[1:]
            return " ".join(ansSections)


class PointerPull(PrimitivePull):
    """
    *Concrete* class to represent a pointer in the debugge.
    """
    _updateTracker = set()
    _watchers = dict()
    _typeHandlerCode = gdb.TYPE_CODE_PTR

    def __init__(self, description):
        super(PointerPull, self).__init__(description)
        self.target = None
        self._validTarget = False

    def _pull(self):
        relativeName = "*"
        targetName = relativeName + self.name
        desc = descriptions.MemoryDescription(
            targetName,
            relativeName=relativeName)
        targetHandler = Pull.handler_factory(self.object.type.target())
        if targetHandler:
            self.target = targetHandler(desc)
        else:
            print("DEBUG: Unhandled obj type for ", str(self.object.type.target()))
            return

        try:
            self.target.save()
            self._validTarget = True
        except gdb.MemoryError as e:
            # TODO: Decorate target as invalid in this case.
            print("MEMORY ACCESS ERROR")
            print(e)
            pass

    def _save(self, update=True):
        super(PointerPull, self)._save()
        print("valid target:", self._validTarget)
        if self._validTarget:
            print("Target = ", self.target)
            if self.target.index == self.index:
                print("SELF LOOP FOUND")
            print(self.target.index, self.index)
            print("self.target = ", self.target)
            print("self.target.children = ", self.target.children)
            self.target.save()
            self.paramDict["children"] = [self.target.doc]


class IntPull(PrimitivePull):
    """
    *Concrete* class to represent integral types.
    """

    _updateTracker = set()
    repository = dict()
    _watchers = dict()
    _arrayFinder = re.compile(r"(.*) ((?:\[\d*\])+)")
    _pointerFinder = re.compile(r"(\(.* \*\)) ")
    _spaceFixer = re.compile(r" ")
    _typeHandlerCode = gdb.TYPE_CODE_INT

    def _find_hidden_type(self):
        v = self.object
        atyp = IntPull._arrayFinder.match(str(v.type))
        if atyp:
            typ = atyp.group(1)
            dims = map(int, atyp.group(2)[1:-1].split("]["))
            t = gdb.lookup_type(typ)
            for dim in dims:
                t = t.array(dim - 1)
            return t

        valString = self.val_string()
        ptyp = IntPull._pointerFinder.match(valString)
        if ptyp:
            typ = IntPull._spaceFixer.sub("", ptyp.group(0)[1:-3])
            return gdb.lookup_type(typ).pointer()

        return False

    def _pull(self):
        # NOTE: I know this is a hack, but nothing I can do.
        # The problem is that sometimes gdb thinks pointers
        # and arrays are ints.
        hidden_typ = self._find_hidden_type()
        if isinstance(hidden_typ, gdb.Type):
            print("DEBUG: Found hidden type!") ## DEBUG
            self._description._object = self.object.cast(hidden_typ)
            Pull.factory(self.description).pull()
        else:
            self._value = self.val_string()
            typ = self.object.type
            self._type = Pull.get_true_type_name(typ)


class FloatPull(PrimitivePull):
    """
    *Concrete* class to represent floating point primitivies.
    """
    _updateTracker = set()
    _watchers = dict()

    _typeHandlerCode = gdb.TYPE_CODE_FLT

    def _pull(self):
        self._value = self.val_string()

# registry.TypeRegistration(CallPull)
registry.TypeRegistration(StructurePull)
registry.TypeRegistration(ArrayPull)
registry.TypeRegistration(PointerPull)
registry.TypeRegistration(IntPull)
registry.TypeRegistration(FloatPull)

# TODO: Refactor this to live in the main memory class.
# That way memories own their watchers, rather than the reverse.
# This has the advantage that it should stop complaints from gdb
# when objects go out of scope.
class MemoryWatcher(gdb.Breakpoint):

    def __init__(self, memory):
        self._memory = memory
        self._type_name = descriptions.type_name(memory.type)
        addr = memory.address
        expression = self._memory.name
        super(MemoryWatcher, self).__init__(
                expression,
                gdb.BP_WATCHPOINT,
                gdb.WP_WRITE,
                True,
                False)
        self.silent = True

    def stop(self):
        try:
            if self.memory:
                self.memory.update()
            else:
                print("Memory gone!")
        except Exception as e:
            traceback.print_exc()
        return False

    @property
    def memory(self):
        return self._memory


def get_frame_symbols(frm=None):
    with frame.Selector(frm) as fs:
        f = fs.frame
        if f.is_valid():
            return { str(sym) for sym in f.block() }
        else:
            raise Exception("Frame no longer valid")

def serialize_frame_globals(frm=None):
    frame = frm if frm is not None else gdb.selected_frame()
    block = frame.block().global_block
    serialize_block_locals(block)

def serialize_upward(baseBlock = None):

    if baseBlock is None:
        f = gdb.newest_frame()

    while f is not None:
        serialize_block_locals(f.block())
        f = f.older()

def serialize_block_locals(blk = None):
    Pull._updatedNames.clear()
    block = blk if blk is not None else gdb.selected_frame().block()
    for sym in block:
        if sym.is_constant:
            continue
        desc = descriptions.MemoryDescription(sym.name, symbol = sym)
        objHandler = Pull.handler_factory(sym.type)
        if not objHandler:
            continue
        obj = objHandler(desc)
        obj.pull()
        if isinstance(obj.object, gdb.Symbol):
            continue
        obj.save()

def serialize_frame_locals(frm = None):
    Pull._updatedNames.clear()
    with frame.Selector(frm) as fs:
        f = fs.frame
        if f.is_valid():
            for sym in f.block():
                desc = descriptions.MemoryDescription(sym.name)
                handler = Pull.handler_factory(sym.type)
                obj = handler(desc)
                obj.save()

# def type_name(t, nameDecorators = ""):
#     if t.code == gdb.TYPE_CODE_PTR:
#         return type_name(t.target(), nameDecorators + "*")
#     elif t.code == gdb.TYPE_CODE_ARRAY:
#         length = str(t.range()[1] - t.range()[0] + 1)
#         return type_name(t.target(), nameDecorators + "[" + length + "]")
#     else:
#         return t.name + nameDecorators

def target_type_name(t):
    if t.code == gdb.TYPE_CODE_PTR or t.code == gdb.TYPE_CODE_ARRAY:
        return target_type_name(t.target())
    return t.name

# class StateSerializer(json.JSONEncoder):

#     def default(self, obj):
#         if isinstance(obj, set):
#             return {"set": list(obj)}
#         return json.JSONEncoder.default(self, StateSerializer.equal_fix(obj))

# def stopped(event):
#     arrayData = [ v2 for k, v in Array.repository.items() for k2, v2 in v.items() ]

#     with open("arrays.json", "w") as outfile:
#         json.dump(arrayData, outfile, cls=StateSerializer)

#     with open("pointers.json", "w") as outfile:
#         json.dump(Pointer.repository, outfile, cls=StateSerializer)

#     with open("structs.json", "w") as outfile:
#         json.dump(Structure.repository, outfile, cls=StateSerializer)

#     with open("values.json", "w") as outfile:
#         json.dump(Int.repository, outfile, cls=StateSerializer)

#     # with open("functions.json", "w") as outfile:
#     #     json.dump(Call.repository, outfile, cls=StateSerializer)

# gdb.events.stop.connect(stopped)

# frameDescription = descriptions.MemoryDescription("yourframe")
# f = frame.Frame(gdb.selected_frame())
# e = models.Execution()
# e.save()
# d = descriptions.MemoryDescription("aa", address="1", execution=e)
# x = IntPull(d)
# x.save()


# dStruct = descriptions.MemoryDescription("exx")
# xStruct = StructurePull(dStruct)
# xStruct.save()

# dArray = descriptions.MemoryDescription("b", execution=e)
# xArray = ArrayPull(dArray)

# NOTE: The read_preference should not be needed.  This is a workaround for a
# bug in pymongo.  (http://goo.gl/Somoeu)
connection = mongoengine.connect('memoryoracle',
                    read_preference=\
                            pymongo.read_preferences.ReadPreference.PRIMARY)

db = connection.memoryoracle

class MemoryOracle(object):

    messageQueue = []

    host = "localhost"

    port = 8765

    active = True


    def __init__(self):
        self._server = None

    def start(self):

        if not self._server:
            self._server = websockets.serve(pingpong, MemoryOracle.host, MemoryOracle.port)
            asyncio.get_event_loop().run_until_complete(self._server)


messages = typed.Typed.objects(execution=Pull.execution)
i = -1

@asyncio.coroutine
def send(message):
    yield from asyncio.sleep(1.0)
    return message

@asyncio.coroutine
def pingpong(websocket, path):
    global i
    global messages
    while MemoryOracle.active and i < len(messages) - 1:
        if not websocket.open:
            print("websocket closed")
            break
        i += 1
        yield from websocket.send(messages[i].to_json())
        greeting = yield from websocket.recv()

serialize_upward()

start_server = websockets.serve(pingpong, '192.168.1.190', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
