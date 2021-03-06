#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import datetime

# import gdb

import pymongo

import mongoengine
# import instance

# NOTE: The read_preference should not be needed.  This is a workaround for a
# bug in pymongo.  (http://goo.gl/Somoeu)
connection = mongoengine.connect('memoryoracle',
                    read_preference=\
                            pymongo.read_preferences.ReadPreference.PRIMARY)
db = connection.memoryoracle

if __name__ == "__main__":
    commit = Commit()
    commit.vcs_hash = "shanumbers"
    executable = Executable()
    executable.name = "a.out"
    executable.path = "./a.out"
    executable.hash_sha512 = "some sha512 hash"
    executable.version = "-1"
    execution = Execution()
    execution.arguments = "a potato"
    instance = Instance(name="some_memory")
    instance.save()
    # execution.save()
    # executable.save()
    execution.objects = [instance]
    executable.executions = [execution]
    commit.executables = [executable]
    commit.save()

    print(db.commit.find({"vcs_hash": "shanumbers"}))

    print(commit.to_json())

    print(commit.executables[0].executions[0].objects[0].name)

    print("hello world")
