#!/usr/bin/env python
# -*- encoding UTF-8 -*-

# THIS CODE DERIVED FORM cma.py

import gdb
import signal
import re
import threading

#-----------------------------------------------------------------------
#Archs

# TODO: Update all arch classes to use gdb.Architecture checks instead of this
# hack

class arch_x86_32(object):
    def is_current(self):
        if gdb.execute("info reg", True, True).find("eax") >= 0:
            return True
        return False
    def get_arg(self, num):
        if num > 1:
            raise Exception("get_arg %d is not supported." %num)
        gdb.execute("up", False, True)
        ret = long(gdb.parse_and_eval("*(unsigned int *)($esp + " + str(num * 4) + ")"))
        gdb.execute("down", False, True)
        return ret
    def get_ret(self):
        return long(gdb.parse_and_eval("$eax"))

class arch_x86_64(object):
    def is_current(self):
        return gdb.newest_frame().architecture().name() == "i386:x86-64"

    def get_arg(self, num):
        if num == 0:
            return long(gdb.newest_frame().read_register("rdi"))
        elif num == 1:
            return long(gdb.newest_frame().read_register("rsi"))
        else:
            raise Exception("get_arg %d is not supported." %num)
    def get_ret(self):
        return long(gdb.newest_frame().read_register("rax"))

class arch_arm(object):
    def is_current(self):
        if gdb.execute("info reg", True, True).find("cpsr") >= 0:
            return True
        return False
    def get_arg(self, num):
        if num == 0:
            return long(gdb.parse_and_eval("$r0"))
        elif num == 1:
            return long(gdb.parse_and_eval("$r1"))
        else:
            raise Exception("get_arg %d is not supported." %num)
    def get_ret(self):
        return long(gdb.parse_and_eval("$r0"))

archs = (arch_x86_32, arch_x86_64, arch_arm)

for e in archs:
    arch = e()
    if arch.is_current():
        break
else:
    raise Exception("Current architecture is not supported by CMA.")

class BreakException(Exception):
    pass

class DynamicBreak(gdb.Breakpoint):

    def _heap_track(self, ret, size):
        print("_tracked ", ret, size)
        gdb.execute("echo " + str(size) )
        not_released_add(ret, size)

    def _heap_release(self):
        print("_released ", arch.get_arg(0))
        released_add(arch.get_arg(0))


class DynamicBreakAlloc(DynamicBreak):
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
