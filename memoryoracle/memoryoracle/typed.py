#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""

import tracked
# import gdb
import mongoengine

"""
Class Typed, which represents debugee
objects with a gdb.TYPE_CODE.
"""
class Typed(mongoengine.Document):

    # _typeHandlerCode = gdb.TYPE_CODE_ERROR

    meta = { 'allow_inheritance': True }
