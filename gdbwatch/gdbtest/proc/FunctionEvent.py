#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import gdb

def function_call_pre(event):
    print("event type: pre function call")
    print(event)

def function_call_post(event):
    print("event type: post function call")
    print(event)

def event_stop(event):
    print("event type: stop")
    print(event)


gdb.events.stop.connect(event_stop)
# gdb.events.inferior_call_pre.connect(function_call_pre)
# print(gdb.events)
# gdb.events.inferior_call_pre.connect(function_call_pre)
# gdb.events.call_post.connect(function_call_post)

