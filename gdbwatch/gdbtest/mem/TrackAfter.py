#!/usr/bin/env python
# -*- encoding UTF-8 -*-


class TrackAfter(object):

    def __init__(self, update = False):
        self.update = update

    def __call__(self, method):

        def wrapped_method(*args):
            method(*args)
            args[0].track_instance(update = self.update)

        return wrapped_method
