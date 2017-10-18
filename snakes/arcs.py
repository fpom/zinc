from functools import reduce
from operator import and_, or_
from itertools import chain
from snakes import ConstraintError

class Arc (object) :
    def _nest (self, *arcs, **more) :
        for a in chain(arcs, more.values()) :
            if (not any(isinstance(a, base)
                        for base in self.__class__.__bases__)
                or not any(isinstance(self, allowed)
                           for allowed in a._nestable_in)) :
                raise ConstraintError("cannot nest %r into %s"
                                      % (a, self.__class__.__name__))
        self._nestable_in = reduce(and_,
                                   (a._nestable_in for a in chain(arcs, more.values())),
                                   self._nestable_in)
        self._order = max(a._order for a in chain(arcs, more.values()))
        self.__dict__.update(more)
        return arcs

class InputArc (Arc) :
    pass

class OutputArc (Arc) :
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
        val = ctx.Val(self.value)
        if isin : # input arc
            if place.name in ctx.sub and val in ctx.sub[place.name] :
                # this value has already be checked, no need to do it again
                ctx.sub[place.name].append(val)
                return nest
            ctx.sub[place.name].append(val)
            node = ctx.IfToken(ctx.marking, place.name, val, body=[], **more)
        else :
            if self.value not in ctx.assign :
                ctx.assign[self.value] = (ctx.names.fresh(add=True), place.type)
            node = ctx.IfType(place, token=val, body=[], **more)
            ctx.add[place.name].append(val)
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
        var = ctx.Var(self.name)
        if isin : # input arc
            if place.name in ctx.sub and var in ctx.sub[place.name] :
                # this variable has already be bound, no need to check again
                ctx.sub[place.name].append(var)
                return nest
            ctx.sub[place.name].append(var)
            node = ctx.ForeachToken(ctx.marking, place.name, self.name, body=[], **more)
        else :
            if self.name not in ctx.assign :
                ctx.assign[self.name] = (ctx.names.fresh(base=self.name, add=True),
                                         place.type)
            node = ctx.IfType(place, token=var, body=[], **more)
            ctx.add[place.name].append(var)
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
        if self.code in ctx.assign :
            var = ctx.Var(ctx.assign[self.code][0])
            if isin and place.name in ctx.sub and var in ctx.sub[place.name] :
                ctx.sub[place.name].append(var)
                return nest
        else :
            var = ctx.Var(ctx.names.fresh(True))
            ctx.assign[self.code] = (var.source, place.type)
            nest.append(ctx.Assign(var.source, self.code,
                                   BLAME=ctx.ArcBlame(place.name, trans.name,
                                                      self.code)))
        if isin :
            ctx.sub[place.name].append(var)
            node = ctx.IfToken(ctx.marking, place.name, var, body=[], **more)
        else :
            ctx.add[place.name].append(var)
            node = ctx.IfType(place, token=var, body=[], **more)
        nest.append(node)
        return node.body

class MultiArc (InputArc, OutputArc) :
    _nestable_in = set()
    def __init__ (self, first, *others) :
        self.components = self._nest(first, *others)
    def __repr__ (self) :
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(c) for c in self.components))
    def vars (self) :
        return reduce(or_, (c.vars() for c in self.components), set())
    def __ast__ (self, nest, place, trans, isin, ctx, **more) :
        for comp in self.components :
            nest = comp.__ast__(nest, place, trans, isin, ctx, **more)
        return nest

class Tuple (InputArc, OutputArc) :
    def __init__ (self, first, *others) :
        self.components = self._nest(first, *others)
    def __repr__ (self) :
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(c) for c in self.components))
    def vars (self) :
        return reduce(or_, (c.vars() for c in self.components), set())

class Test (InputArc, OutputArc) :
    _nestable_in = {MultiArc}
    def __init__ (self, label) :
        self._nest(label=label)
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.label)
    def vars (self) :
        return self.label.vars()

class Inhibitor (InputArc) :
    _nestable_in = {MultiArc}
    def __init__ (self, label, guard=None) :
        self._nest(label=label)
        self.guard = guard
    def __repr__ (self) :
        return "%s(%r, %r)" % (self.__class__.__name__, self.label, self.guard)
    def vars (self) :
        return self.label.vars()

class Flush (InputArc) :
    _order = 15
    _nestable_in = {Test, Inhibitor}
    def __init__ (self, name) :
        self.name = name
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.name)
    def vars (self) :
        return {self.name}

class Fill (OutputArc) :
    _order = 25
    _nestable_in = {Test}
    def __init__ (self, code) :
        self.code = code
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.code)
    def vars (self) :
        return set()

Value._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Variable._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Expression._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Tuple._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
