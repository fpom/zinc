from snakes import *

class ArcAnnotation (object) :
    pass

class Value (ArcAnnotation) :
    input_allowed = True
    def __init__ (self, value) :
        self.value = value

class Variable (ArcAnnotation) :
    input_allowed = True
    def __init__ (self, name) :
        self.name = name

class Expression (ArcAnnotation) :
    input_allowed = False
    def __init__ (self, code) :
        self.code = code

class MultiArc (ArcAnnotation) :
    def __init__ (self, first, *others) :
        self.components = (first,) + others
        if any(isinstance(c, self.__class__) for c in self.components) :
            raise ConstraintError("cannot nest %r" % self.__class__.__name__)
        self.input_allowed = all(c.input_allowed for c in self.components)

class Tuple (ArcAnnotation) :
    def __init__ (self, first, *others) :
        self.components = (first,) + others
        if any(isinstance(c, MultiArc) for c in self.components) :
            raise ConstraintError("cannot nest 'MultiArc' in %s"
                                  % self.__class__.__name__)
        self.input_allowed = all(c.input_allowed for c in self.components)

class Test (ArcAnnotation) :
    def __init__ (self, label) :
        self.label = label
        self.input_allowed = label.input_allowed

class Inhibitor (ArcAnnotation) :
    def __init__ (self, label, guard=None) :
        if not label.input_allowed :
            raise ConstraintError("%r not allowed as inhibitor arc"
                                  % label.__class__.__name__)
        self.label = label
        self.guard = guard
        self.input_allowed = True

class Flush (ArcAnnotation) :
    input_allowed = True
    def __init__ (self, name) :
        self.name = name

class Fill (ArcAnnotation) :
    input_allowed = False
    def __init__ (self, code) :
        self.code = code
