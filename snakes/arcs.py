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
    def __repr__ (self) :
        return "Value(%r)" % self.value
    def vars (self) :
        return set()
    def __ast__ (self, nest, place, trans, isin, ctx, **more) :
        val = ast.Val(self.value)
        if isin : # input arc
            if place.name in ctx.sub and val in ctx.sub[place.name] :
                # this value has already be checked, no need to do it again
                ctx.sub[place.name].add([val])
                return nest
            ctx.sub[place.name].add([val])
            node = ast.IfToken(ctx.marking, place.name, val, body=[], **more)
        else :
            node = ast.IfType(place, token=val, body=[], **more)
            ctx.add[place.name].add([val])
        nest.append(node)
        return node.body

class Variable (InputArc, OutputArc) :
    _order = 10
    def __init__ (self, name) :
        self.name = name
    def __repr__ (self) :
        return "Variable(%r)" % self.name
    def vars (self) :
        return {self.name}
    def __ast__ (self, nest, place, trans, isin, ctx, **more) :
        var = ast.Var(self.name)
        if isin : # input arc
            if place.name in ctx.sub and var in ctx.sub[place.name] :
                # this variable has already be bound, no need to check again
                ctx.sub[place.name].add([var])
                return nest
            ctx.sub[place.name].add([var])
            node = ast.ForeachToken(ctx.marking, place.name, self.name, body=[], **more)
        else :
            node = ast.IfType(place, token=var, body=[], **more)
            ctx.add[place.name].add([var])
        nest.append(node)
        return node.body

class Expression (InputArc, OutputArc) :
    _order = 20
    def __init__ (self, code) :
        self.code = code
    def __repr__ (self) :
        return "Expression(%r)" % self.code
    def vars (self) :
        return set()
    def __ast__ (self, nest, place, trans, isin, ctx, **more) :
        expr = ast.Expr(self.code)
        if isin : # input arc
            if place.name in ctx.sub and expr in ctx.sub[place.name] :
                # this expression has already be checked, no need to do it again
                ctx.sub[place.name].add([expr])
                return nest
            ctx.sub[place.name].add([expr])
            node = ast.IfToken(ctx.marking, place.name, self.code, body=[], **more)
        else :
            node = ast.IfType(place, token=expr, body=[], **more)
            ctx.add[place.name].add([expr])
        nest.append(node)
        return node.body

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
