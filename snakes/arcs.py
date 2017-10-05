import operator
from functools import reduce
from snakes import ConstraintError
from snakes.compil import ast

class Arc (object) :
    pass

class InputArc (Arc) :
    pass

class OutputArc (Arc) :
    pass

class NotNestedArc (Arc) :
    pass

class Value (InputArc, OutputArc) :
    _order = 0
    def __init__ (self, value) :
        self.value = value
    def vars (self) :
        return set()
    def __bindast__ (self, nest, marking, place) :
        node = ast.If(ast.MarkingContains(marking, place, self.value), [])
        nest.append(node)
        return node.body
    def __flowast__ (self) :
        return [ast.Value(self.value)]

class Variable (InputArc, OutputArc) :
    _order = 10
    def __init__ (self, name) :
        self.name = name
    def vars (self) :
        return {self.name}
    def __bindast__ (self, nest, marking, place) :
        node = ast.For(self.name, ast.MarkingLookup("marking", place), [])
        nest.append(node)
        return node.body
    def __flowast__ (self) :
        return [ast.Name(self.name)]

class Expression (InputArc, OutputArc) :
    _order = 20
    def __init__ (self, code) :
        self.code = code
    def vars (self) :
        return set()
    def __flowast__ (self) :
        return [ast.SourceExpr(self.code)]

class MultiArc (InputArc, OutputArc, NotNestedArc) :
    def __init__ (self, first, *others) :
        self.components = (first,) + others
        for c in self.components :
            if isinstance(c, NotNestedArc) :
                raise ConstraintError("cannot nest %r" % c.__class__.__name__)
        self._order = max(c._order for c in self.components)
    def vars (self) :
        return reduce(operator.or_, (c.vars() for c in self.components), set())

class Tuple (InputArc, OutputArc) :
    def __init__ (self, first, *others) :
        self.components = (first,) + others
        for c in self.components :
            if isinstance(c, NotNestedArc) :
                raise ConstraintError("cannot nest %r" % c.__class__.__name__)
        self._order = max(c._order for c in self.components)
    def vars (self) :
        return reduce(operator.or_, (c.vars() for c in self.components), set())

class Test (InputArc, OutputArc) :
    def __init__ (self, label) :
        self.label = label
        self._order = label._order
    def vars (self) :
        return self.label.vars()

class Inhibitor (InputArc) :
    def __init__ (self, label, guard=None) :
        self.label = label
        self.guard = guard
        self._order = label._order
    def vars (self) :
        return self.label.vars()

class Flush (InputArc) :
    _order = 15
    def __init__ (self, name) :
        self.name = name
    def vars (self) :
        return {self.name}

class Fill (OutputArc) :
    _order = 25
    def __init__ (self, code) :
        self.code = code
    def vars (self) :
        return {self.name}
