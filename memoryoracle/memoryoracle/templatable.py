#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import tracked

class Templatable(tracked.Tracked):
    pass


class Alias(Templatable):
    pass


class Type(Templatable):
    pass


class Union(Type):
    pass


class TemplateDecorator(Templatable):
    pass


class TemplatedDecorator(Templatable):
    pass


class Typedef(Alias):
    pass


class ChildTypeDecorator(Type):
    pass


class Enum(Type):
    pass


class StronglyTypedEnum(Type):
    pass
