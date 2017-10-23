from functools import reduce
from operator import and_, or_
from itertools import chain
from snakes import ConstraintError
from snakes.data import record

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
        self._order = max(a._order for a in chain(arcs, more.values())) + 1
        self.__dict__.update(more)
        return arcs

class InputArc (Arc) :
    pass

class OutputArc (Arc) :
    pass

class _Ast (object) :
    def _bind (self, type, ctx, name=None) :
        if self.source in ctx.bound :
            return ctx.bound[self.source], False
        elif name is None :
            name = ctx.bound[self.source] = ctx.declare.new(type)
            return name, True
        else :
            ctx.declare[name] = type
            ctx.bound[self.source] = name
            return name, True

class _AstBindTestConsume (_Ast) :
    def __astin__ (self, nest, place, ctx, **more) :
        ctx.notempty.add(place)
        varname, isnew = self._bind(place.type, ctx)
        ctx.sub[place.name].append(varname)
        if isnew :
            nest.append(ctx.Assign(varname, ctx.Expr(self.source), **more))
        node = ctx.IfToken(ctx.marking, place.name, varname, **more)
        nest.append(node)
        return node.body
    def __astnotin__ (self, nest, place, ctx, guard, **more) :
        varname, isnew = self._bind(place.type, ctx)
        if isnew :
            nest.append(ctx.Assign(varname, ctx.Expr(self.source), **more))
        node = ctx.IfNoToken(ctx.marking, place.name, varname, **more)
        nest.append(node)
        return node.body

class _AstTypeProduce (_Ast) :
    def __astout__ (self, nest, place, ctx, **more) :
        varname, isnew = self._bind(place.type, ctx)
        ctx.add[place.name].append(varname)
        if isnew :
            nest.append(ctx.Assign(varname, ctx.Expr(self.source), **more))
        node = ctx.IfType(place, varname, **more)
        nest.append(node)
        return node.body

class Value (InputArc, OutputArc, _AstBindTestConsume, _AstTypeProduce) :
    _order = 0
    def __init__ (self, value) :
        self.source = value
    def __repr__ (self) :
        return "Value(%r)" % self.source
    def vars (self) :
        return set()

class Expression (InputArc, OutputArc, _AstBindTestConsume, _AstTypeProduce) :
    _order = 20
    def __init__ (self, code) :
        self.source = code
    def __repr__ (self) :
        return "Expression(%r)" % self.source
    def vars (self) :
        return set()

class Variable (InputArc, OutputArc, _AstTypeProduce) :
    _order = 10
    def __init__ (self, name) :
        self.source = name
    def __repr__ (self) :
        return "Variable(%r)" % self.source
    def vars (self) :
        return {self.source}
    def __astin__ (self, nest, place, ctx, **more) :
        ctx.notempty.add(place)
        varname, isnew = self._bind(place.type, ctx, self.source)
        ctx.sub[place.name].append(varname)
        if isnew :
            node = ctx.ForeachToken(ctx.marking, place.name, varname, **more)
        else :
            node = ctx.IfToken(ctx.marking, place.name, varname, **more)
        nest.append(node)
        return node.body
    def __astnotin__ (self, nest, place, ctx, guard, **more) :
        varname, isnew = self._bind(place.type, ctx, self.source)
        if isnew and not guard :
            node = ctx.IfEmpty(ctx.marking, place.name, **more)
            del ctx.declare[varname]
        elif isnew :
            node = ctx.IfNoTokenSuchThat(ctx.marking, place.name, varname,
                                         ctx.Expr(guard), **more)
        elif guard :
            raise ConstraintError("inhibition guard forbidden for %r"
                                  " (bounded on another arc)" % self)
        else :
            node = ctx.IfNoToken(ctx.marking, place.name, varname, **more)
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

class Flush (InputArc, _Ast) :
    _order = 15
    def __init__ (self, name) :
        self.source = name
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.source)
    def vars (self) :
        return {self.source}
    def __astin__ (self, nest, place, ctx, **more) :
        varname, isnew = self._bind(("mset", place.type), ctx, self.source)
        ctx.sub[place.name].append(("mset", varname))
        if isnew :
            node = ctx.GetPlace(varname, ctx.marking, place.name, **more)
            ret = nest
        else :
            node = ctx.IfPlace(ctx.marking, place.name, varname, **more)
            ret = node.body
        nest.append(node)
        return ret

class Fill (OutputArc, _Ast) :
    _order = 30
    def __init__ (self, code) :
        self.source = code
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.source)
    def vars (self) :
        return set()
    def __astout__ (self, nest, place, ctx, **more) :
        varname, isnew = self._bind(("mset", place.type), ctx)
        ctx.add[place.name].append(("mset", varname))
        if isnew :
            nest.append(ctx.Assign(varname, ctx.Expr(self.source), **more))
        node = ctx.IfAllType(place, varname, **more)
        nest.append(node)
        return node.body

class Test (InputArc, OutputArc) :
    _nestable_in = {MultiArc}
    def __init__ (self, label) :
        self._nest(label=label)
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.label)
    def vars (self) :
        return self.label.vars()
    def __astin__ (self, nest, place, ctx, **more) :
        if place.name in ctx.sub :
            pos = len(ctx.sub[place.name])
        else :
            pos = 0
        newnest = self.label.__astin__(nest, place, ctx, **more)
        if place.name in ctx.sub :
            tokens = ctx.sub[place.name]
            new = len(tokens)
            ctx.test[place.name].extend(tokens[pos - new:])
            del tokens[pos - new:]
        return newnest
    def __astout__ (self, nest, place, ctx, **more) :
        if place.name in ctx.add :
            pos = len(ctx.add[place.name])
        else :
            pos = 0
        newnest = self.label.__astout__(nest, place, ctx, **more)
        if place.name in ctx.add :
            tokens = ctx.add[place.name]
            new = len(tokens)
            del tokens[pos - new:]
        return newnest

class Inhibitor (InputArc) :
    _nestable_in = {MultiArc}
    def __init__ (self, label, guard=None) :
        if isinstance(label, _AstBindTestConsume) and guard :
            raise ConstraintError("inhibition guard forbidden together with %s"
                                  % label)
        self._nest(label=label)
        self.guard = guard
    def __repr__ (self) :
        return "%s(%r, %r)" % (self.__class__.__name__, self.label, self.guard)
    def vars (self) :
        return self.label.vars()
    def __astin__ (self, nest, place, ctx, **more) :
        return self.label.__astnotin__(nest, place, ctx, self.guard, **more)

class Tuple (InputArc, OutputArc) :
    def __init__ (self, first, *others) :
        self.components = self._nest(first, *others)
    def __repr__ (self) :
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(c) for c in self.components))
    def vars (self) :
        return reduce(or_, (c.vars() for c in self.components), set())
    def _walk (self, *others) :
        l = len(self.components)
        for t in others :
            if not isinstance(t, tuple) :
                raise ValueError("not a tuple %r" % t)
            elif len(t) != l  :
                raise ConstraintError("tuple length do not match")
        for i, (first, *z) in enumerate(zip(self.components, *others)) :
            if isinstance(first, Tuple) :
                for p, t in first._walk(*z) :
                    yield [i] + p, t
            else :
                yield [i], [first] + z
    def _fold (self, items) :
        slots = [None] * len(self.components)
        for path, label in items :
            if len(path) == 1 :
                slots[path[0]] = label
            elif slots[path[0]] is None :
                slots[path[0]] = [(path[1:], label)]
            else :
                slots[path[0]].append((path[1:], label))
        return tuple(c._fold(s) if isinstance(c, Tuple) else s
                     for c, s in zip(self.components, slots))
    def _none (self) :
        return tuple(c._none() if isinstance(c, Tuple) else None
                     for c in self.components)
    def __astin__ (self, nest, place, ctx, **more) :
        ctx.notempty.add(place)
        match = []
        guard = []
        pvar = ctx.declare.new(place.type)
        node = ctx.ForeachToken(ctx.marking, place.name, pvar, **more)
        nest.append(node)
        nest = node.body
        if place.type :
            nest.append(ctx.IfTuple(place, pvar, **more))
            nest = nest[0].body
        placetype = place.type or self._none()
        for path, (label, type) in self._walk(placetype) :
            if isinstance(label, (Value, Expression)) or label.source in ctx.bound :
                var = ctx.declare.new(type)
                nest.append(ctx.AssignItem(var, pvar, path, **more))
                guard.append(ctx.Eq(ctx.Expr(var), ctx.Expr(label.source), **more))
            else :
                var = label.source
                nest.append(ctx.AssignItem(var, pvar, path, **more))
            match.append((path, var))
            ctx.bound[label.source] = var
        ctx.sub[place.name].append(ctx.Pattern(self, self._fold(match), placetype))
        if guard :
            node = ctx.IfGuard(ctx.And(guard, **more), **more)
            nest.append(node)
            nest = node.body
        return nest
    def __astout__ (self, nest, place, ctx, **more) :
        toadd = []
        placetype = place.type or self._none()
        for path, (label, type) in self._walk(placetype) :
            nest = label.__astout__(nest, record(name=place.name, type=type), ctx,
                                    **more)
            toadd.append((path, ctx.add[place.name].pop(-1)))
        ctx.add[place.name].append(ctx.Pattern(self, self._fold(toadd), placetype))
        return nest

Value._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Variable._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Expression._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Tuple._nestable_in = {Tuple, Test, Inhibitor, MultiArc}
Flush._nestable_in = {Test}
Fill._nestable_in = {Test, MultiArc}
