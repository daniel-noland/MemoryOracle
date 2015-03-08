#!/usr/bin/env python
# -*- encoding UTF-8 -*-

# THIS CODE DERIVED FORM cma.py

import gdb
import signal
import re
import threading

from .Heap import Heap

#-----------------------------------------------------------------------
#Archs

# TODO: Update all arch classes to use gdb.Architecture checks instead of this
# hack

class Arch(object):

    class x86_32(object):

        @staticmethod
        def is_current():
            if gdb.execute("info reg", True, True).find("eax") >= 0:
                return True
            return False

        @staticmethod
        def get_arg(num):
            if num > 1:
                raise Exception("get_arg %d is not supported." %num)
            gdb.execute("up", False, True)
            ret = long(gdb.parse_and_eval(
                "*(unsigned int *)($esp + " + str(num * 4) + ")")
                )
            gdb.execute("down", False, True)
            return ret

        @staticmethod
        def get_ret():
            return long(gdb.parse_and_eval("$eax"))

    class x86_64(object):

        @staticmethod
        def is_current():
            return gdb.newest_frame().architecture().name() == "i386:x86-64"

        @staticmethod
        def get_arg(num):
            if num == 0:
                return long(gdb.newest_frame().read_register("rdi"))
            elif num == 1:
                return long(gdb.newest_frame().read_register("rsi"))
            else:
                raise Exception("get_arg %d is not supported." %num)

        @staticmethod
        def get_ret(self):
            return long(gdb.newest_frame().read_register("rax"))

    class arm(object):

        @staticmethod
        def is_current():
            if gdb.execute("info reg", True, True).find("cpsr") >= 0:
                return True
            return False

        @staticmethod
        def get_arg(num):
            if num == 0:
                return long(gdb.parse_and_eval("$r0"))
            elif num == 1:
                return long(gdb.parse_and_eval("$r1"))
            else:
                raise Exception("get_arg %d is not supported." %num)

        @staticmethod
        def get_ret():
            return long(gdb.parse_and_eval("$r0"))

    archs = (Arch.x86_32, Arch.x86_64, Arch.arm)

    current = None

    for e in Arch.archs:
        if e.is_current():
            Arch.current = e
            break
    else:
        raise Exception("Current architecture is not supported by MemoryOracle.")

arch = Arch.current

class BreakException(Exception):
    pass


class DynamicBreak(gdb.Breakpoint):

    @staticmethod
    def _heap_track(ret, size):
        print("_tracked ", ret, size)
        gdb.execute("echo " + str(size) )
        not_released_add(ret, size)

    @staticmethod
    def _heap_release():
        print("_released ", arch.get_arg(0))
        released_add(arch.get_arg(0))


class DynamicBreakAlloc(DynamicBreak):

    allocs = dict()

    def stop(self):
        size = arch.get_arg(0)
        fin = DynamicBreakAllocFinish()
        return False


class DynamicBreakAllocFinish(gdb.FinishBreakpoint):
    def stop(self):
        print("finish return " + str(hex(arch.get_ret())))
        return False


class DynamicBreakCalloc(DynamicBreak):
    def event(self):
        size = arch.get_arg(0) * arch.get_arg(1)
        DynamicBreak._disable_finish_enable()
        self._heap_track(arch.get_ret(), size)


class DynamicBreakRealloc(DynamicBreak):
    def event(self):
        super()._heap_release()
        size = arch.get_arg(1)
        DynamicBreak._disable_finish_enable()
        super()._heap_track(arch.get_ret(), size)


class DynamicBreakRelease(DynamicBreak):
    def event(self):
        super()._heap_release()
        DynamicBreak._disable_finish_enable()


b = DynamicBreakAlloc("operator new", gdb.BP_BREAKPOINT, gdb.WP_READ, True)
print("hello")
