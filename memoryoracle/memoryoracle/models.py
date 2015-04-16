from __future__ import unicode_literals

import gdb
from django.db import models
from jsonfield import JSONField
from copy import deepcopy

from uuid import uuid4 as uuid

class Schema(object):

    _ID_LENGTH = 36

    _MAX_NAME_LENGTH = 200

    _ADDRESS_LENGTH = 64

    @staticmethod
    def ID_LENGTH():
        return Schema._ID_LENGTH

    @staticmethod
    @property
    def MAX_NAME_LENGTH():
        return Schema._MAX_NAME_LENGTH

    @staticmethod
    @property
    def ADDRESS_LENGTH():
        return Schema._ADDRESS_LENGTH

    @staticmethod
    def gen_id():
        return str(uuid())


class Tracked(models.Model):

    # id = models.CharField(primary_key=True, max_length=36, default=Schema.gen_id)
    name = models.TextField(default=None)

    class Meta:
        abstract = True


class Program(Tracked):

    class Meta:
        db_table = 'program'


class Commit(Tracked):

    id_program = models.ForeignKey(Program)
    vcs_hash = models.CharField(unique=True, max_length=200)
    branch_name = models.CharField(max_length=200)

    class Meta:
        db_table = 'commit'


class Executable(Tracked):

    path = models.TextField(default="./a.out")
    id_commit = models.ForeignKey(Commit)

    class Meta:
        db_table = 'executable'


class Execution(Tracked):

    id_executable = models.ForeignKey(Executable, default=None)

    class Meta:
        db_table = 'execution'


class Typed(Tracked):

    id_execution = models.ForeignKey(Execution)
    type = models.TextField()
    description = models.JSONField(default=None)
    data = models.JSONField(default=None)

    _updatedNames = set()

    class Meta:
        abstract = True

    class DetectionError(Exception):
        pass

    class DataError(Exception):
        pass

    _typeCodeMap = {
            gdb.TYPE_CODE_ERROR: TypeDetectionError,
    }

    _typeHandlerCode = gdb.TYPE_CODE_ERROR

    def _basic_track(self, **kwargs):

        self.args = deepcopy(kwargs)

        if kwargs["name"] in self._updatedNames:
            self.args["update"] = False
            return self.args["update"]

        self._updatedNames.add(kwargs["name"])

        if isinstance(kwargs["type"], gdb.Type):
            self.args["type"] = str(typ)

        if isinstance(kwargs["description"], Description):
            self.args["description"] = kwargs["description"].dict

        if isinstance(kwargs["data"], gdb.Value):
            self.args["data"] = dict()
            self.debugee_data = kwargs["data"]

        if isinstance(self.args["data"], dict):
            self.debugee_data = None
        else:
            raise DataError(
                    "Invalid data field!  Must be dictionary or gdb.Value")

        if self.index(self.args) not in self._updateTracker:
            self._updateTracker.add(self.args["index"])
            # self.repository[self.index][self.name] = self.description.dict
            self.args["description"] = self.args["description"].dict
            self.args["update"] = True
        else:
            self.args["update"] = False

        return self.args["update"]

    def track(self, **kwargs):
        if self._basic_track(**kwargs):
            self._track()

    def __init__(self, *args, **kwargs):

        if len(args) > 0:
            raise Exception("Only keyword values allowed in __init__!")

        self.track(self, **kwargs)
        super(Typed, self).__init__(*args, **self.args)
        self._watchers[self.index] = InstanceWatcher(self)

    @staticmethod
    def type_handler():
        return Typed._type_lookup(self._typeHandlerCode)

    @property
    def type_code(self):
        raise NotImplementedError("Abstract class Typed has no type code")

    @property
    def gdb_type(self):
        return json.loads(self.data)["type"]


class Memory(Typed):
    """
    Model representing an instance of an addressable object with a type from
    the debugee.

    This class enforces that the object have a memory address
    in the debugge, or that an appropriate address is specified.
    """

    address = models.CharField(max_length=64)
    has_symbol = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name="children")

    _updateTracker = set()
    _watchers = dict()
    _addressFixer = re.compile(r" .*")

    def update(self):
        self._clear_updated()
        self.track()

    def _clear_updated(self):
        self._updateTracker.discard(self.index)

    @property
    def watchers(self):
        return self._watchers

    def _compute_index(self):
        return self._addressFixer.sub("", str(self.address))

    # @property
    # def frame(self):
    #     return self.description.frame

    def __init__(self, *args, **kwargs):
        super(Memory, self).__init__(*args, **kwargs)
        self.track()

    class Meta:
        db_table = 'memory'


class ProgramFile(Tracked):

    id_commit = models.ForeignKey(Commit)
    path = models.CharField(max_length=200)
    size = models.BigIntegerField()

    class Meta:
        abstract = True


class ObjectFile(ProgramFile):

    class Meta:
        db_table = 'object_file'


class SourceFile(ProgramFile):

    lines = models.BigIntegerField()

    class Meta:
        db_table = 'source_file'


class Symbol(Typed):

    class Meta:
        db_table = 'symbol'


class Type(Tracked):

    class Meta:
        db_table = 'type'
