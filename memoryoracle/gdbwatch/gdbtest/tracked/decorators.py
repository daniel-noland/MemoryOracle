#!/usr/bin/env python
# -*- encoding UTF-8 -*-

from .tracked import Tracked


class ExternalDecorator(Tracked):
    """
    *Decorator* class to decorate a tracked object as being external
    to your work.
    """
    pass


class StandardDecorator(Tracked):
    """
    *Decorator* class to decorate a tracked object as belonging to
    the languages standard library.
    """
