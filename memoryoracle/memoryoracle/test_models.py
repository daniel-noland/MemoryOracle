#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import unittest

import django
django.setup()

import memoryoracle.models
import string
import random


class ModelTest(object):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    def test_if_exists(self):
        createdObjects = self.dataClass()
        for orm in createdObjects:
            testOrm = self.cls.objects.get(id=orm.id)
            self.assertEqual(testOrm.id, orm.id)
            self.assertEqual(testOrm, orm)


class ModelTestData(object):

    _STORE_TESTS = 10
    _RANDOM_NAME_LENGTH = 20

    _depends = []

    def __init__(self):
        pass

    @classmethod
    def depends(cls):
        return cls._depends

    @staticmethod
    def STORE_TESTS():
        return ModelTestData._STORE_TESTS

    @classmethod
    def gen_name(cls):
        return "___test_name___" + \
                ''.join(random.choice(string.ascii_lowercase)
                        for i in range(ModelTestData._RANDOM_NAME_LENGTH))

    @classmethod
    def set_up_depends(cls):
        for dep in cls.depends():
            dep.set_up_class()

    @classmethod
    def tear_down_depends(cls):
        for dep in cls.depends():
            dep.tear_down_class()

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        if self._i < len(self.orms):
            self._i += 1
            return self.orms[self._i - 1]
        else:
            raise StopIteration()

    @classmethod
    def tear_down_class(cls):
        for orm in cls.orms:
            print("toasting orm: ", orm.id)
            orm.delete()
        cls.tear_down_depends()


class ProgramTestData(ModelTestData):

    model = memoryoracle.models.Program

    _depends = []

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [ {"name": cls.gen_name()} for x in range(cls.STORE_TESTS()) ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelProgram(unittest.TestCase, ModelTest):

    dataClass = ProgramTestData

    cls = memoryoracle.models.Program

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()


class CommitTestData(ModelTestData):

    model = memoryoracle.models.Commit

    _depends = [ProgramTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "name": ModelTestData.gen_name(),
                    "id_program": prog,
                    "branch_name": ModelTestData.gen_name(),
                    "vcs_hash": ModelTestData.gen_name()
                } for prog in cls.data["ProgramTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelCommit(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = CommitTestData

    cls = memoryoracle.models.Commit


class ExecutableTestData(ModelTestData):

    model = memoryoracle.models.Executable

    _depends = [CommitTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "name": ModelTestData.gen_name(),
                    "path": ModelTestData.gen_name(),
                    "id_commit": commit,
                } for commit in cls.data["CommitTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelExecutable(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = ExecutableTestData

    cls = memoryoracle.models.Executable


class ExecutionTestData(ModelTestData):

    model = memoryoracle.models.Execution

    _depends = [ExecutableTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "name": ModelTestData.gen_name(),
                    "id_executable": executable,
                } for executable in cls.data["ExecutableTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelExecution(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = ExecutionTestData

    cls = memoryoracle.models.Execution


class MemoryTestData(ModelTestData):

    model = memoryoracle.models.Memory

    _depends = [ExecutionTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "name": ModelTestData.gen_name(),
                    "id_execution": execution,
                    "type": "__test_type__",
                    "address": ModelTestData.gen_name(),
                    "has_symbol": random.choice([True, False]),
                    "data": ModelTestData.gen_name(),
                } for execution in cls.data["ExecutionTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelMemory(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = MemoryTestData

    cls = memoryoracle.models.Memory


class ObjectFileTestData(ModelTestData):

    model = memoryoracle.models.ObjectFile

    _depends = [CommitTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "id_commit": commit,
                    "path": ModelTestData.gen_name(),
                    "size": random.randint(0, 1000),
                } for commit in cls.data["CommitTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelObjectFile(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = ObjectFileTestData

    cls = memoryoracle.models.ObjectFile


class SourceFileTestData(ModelTestData):

    model = memoryoracle.models.SourceFile

    _depends = [CommitTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "id_commit": commit,
                    "path": ModelTestData.gen_name(),
                    "size": random.randint(0, 1000),
                    "lines": random.randint(0, 1000),
                } for commit in cls.data["CommitTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelSourceFile(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = SourceFileTestData

    cls = memoryoracle.models.SourceFile


class SymbolTestData(ModelTestData):

    model = memoryoracle.models.Symbol

    _depends = [ExecutionTestData]

    @classmethod
    def set_up_class(cls):
        cls.set_up_depends()
        cls.data = { x.__name__: x() for x in cls.depends() }
        cls.argsList = [
                {
                    "id_execution": execution,
                    "type": ModelTestData.gen_name(),
                } for execution in cls.data["ExecutionTestData"] ]
        cls.orms = [ cls.model.objects.create(**kwargs) for kwargs in cls.argsList ]


class TestModelSymbol(unittest.TestCase, ModelTest):

    @classmethod
    def setUpClass(cls):
        data = cls.dataClass.set_up_class()

    @classmethod
    def tearDownClass(cls):
        cls.dataClass.tear_down_class()

    dataClass = SymbolTestData

    cls = memoryoracle.models.Symbol


if __name__ == '__main__':
    unittest.main()
