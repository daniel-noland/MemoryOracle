#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb

class NewFinishBreak(gdb.FinishBreakpoint):
    def stop(self):
        print("finished new call")
        print(self.return_value)
        return False

    def out_of_scope():
        print("something strange")

class NewBreak(gdb.Breakpoint):
    def stop(self):
        print("hit new call")
        fin = NewFinishBreak()
        return False

NewBreak("operator new")
