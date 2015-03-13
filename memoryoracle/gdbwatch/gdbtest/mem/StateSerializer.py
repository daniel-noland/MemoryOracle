#!/usr/bin/env python
# -*- encoding UTF-8 -*-

class StateSerializer(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return json.JSONEncoder.default(self, list(obj))
        else:
            return json.JSONEncoder.default(self, obj)
