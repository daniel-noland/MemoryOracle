#!/usr/bin/env python
# -*- encoding UTF-8 -*-


class Allocations(object):

    def __init__(self, addr, typ, count = 1):
        self.type = typ
        self.count = count
        instances[addr] = self

