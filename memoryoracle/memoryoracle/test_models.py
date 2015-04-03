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


if __name__ == '__main__':
    unittest.main()
