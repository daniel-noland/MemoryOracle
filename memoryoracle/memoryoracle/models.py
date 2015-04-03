# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models

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

    # @classmethod
    # def create(cls, description):
    #     trackedObject = cls(description)
    #     trackedObject.id = Schema.gen_id()
    #     trackedObject.name = description.name
    #     return trackedObject

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
    type = models.CharField(max_length=200)

    class Meta:
        abstract = True

    class DetectionError(Exception):
        pass

    _typeCodeMap = dict()
    # _typeCodeMap = {
            # gdb.TYPE_CODE_ERROR: TypeDetectionError,
            # }

    # _typeHandlerCode = gdb.TYPE_CODE_ERROR

    @property
    def type(self):
        if self._type is None:
            self._type = Typed._type_lookup(self.gdb_type.code)
        return self._type

    @staticmethod
    def type_handler():
        return Typed._type_lookup(Typed._typeHandlerCode)

    @property
    def type_code(self):
        raise NotImplementedError("Abstract class Typed has no type code")

    @property
    def gdb_type(self):
        return self.object.type


class Memory(Typed):

    address = models.CharField(max_length=64)
    has_symbol = models.BooleanField(default=False)
    data = models.TextField()

    class Meta:
        managed = True
        db_table = 'memory'


class ProgramFile(Tracked):

    id_commit = models.ForeignKey(Commit)
    path = models.CharField(max_length=200)
    size = models.BigIntegerField()

    class Meta:
        abstract = True


class ObjectFile(ProgramFile):

    class Meta:
        managed = True
        db_table = 'object_file'


class SourceFile(ProgramFile):

    lines = models.BigIntegerField()

    class Meta:
        managed = True
        db_table = 'source_file'


class Symbol(Typed):

    class Meta:
        managed = True
        db_table = 'symbol'


class Type(Tracked):

    class Meta:
        managed = True
        db_table = 'type'
