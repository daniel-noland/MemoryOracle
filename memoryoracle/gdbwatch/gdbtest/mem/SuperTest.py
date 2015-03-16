#!/usr/bin/env python
# -*- encoding UTF-8 -*-
# PythonDecorators/my_decorator.py

class entry_exit(object):

    def __init__(self, f):
        self.f = f
        print("inside my_decorator.__init__()")

    def __call__(self):
        print("Entering", self.f.__name__)
        self.f()
        print("Exited", self.f.__name__)

@entry_exit
def aFunction():
    print("inside aFunction()")

print("Finished decorating aFunction()")

aFunction()
aFunction()
