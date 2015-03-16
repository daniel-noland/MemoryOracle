#!/usr/bin/env python
# -*- encoding UTF-8 -*-
"""
File containing the abstract Tracked class.
"""

class Tracked(object):
    """
    *Abstract* class to represent a piece of information from the debugee
    to track.
    """
    pass


class ExternalDecorator(Tracked):
    """
    *Decorator* class to decorate a tracked object as being external
    to your work.
    """
    pass


