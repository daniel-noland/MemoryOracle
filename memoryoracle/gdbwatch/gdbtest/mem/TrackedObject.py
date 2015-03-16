#!/usr/bin/env python
# -*- encoding UTF-8 -*-

from .Exceptions import MemoryOracleException
from .Exceptions import AbstractClassInitializationError


class DuplicateError(MemoryOracleException):
    pass


class TrackedObject(object):

    # _instances = dict()

    def __init__(self, *args, **kwargs):
        raise AbstractClassInitializationError(
                "Attempted to init abstract class TrackedObject")

    @property
    def identifier(self):
        raise NotImplementedError(
                "Identifier must be implemented by sub-class")

    def track_instance(self, update = True):
        if not update:
            self._check_duplicate(self)
        self._index = self._construct_index()
        self._store_instance(self)

    @property
    def index(self):
        return self._index

    @classmethod
    @property
    def instances(cls):
        return cls._instances

    def _construct_index(self):
        return str(self.identifier)

    @classmethod
    def _check_duplicate(cls, instance):
        check = cls.instances.get(instance.index, False)
        if check:
            return
        else:
            raise DuplicateError(
                    "Illegal attempt to create duplicte tracked object "
                    + str(check))

    @classmethod
    def _store_instance(cls, instance):
        cls._instances[instance.index] = instance

