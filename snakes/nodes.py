import operator, logging, collections
from functools import reduce
from snakes import TypingError
from snakes.data import mset, WordSet
from snakes.tokens import Token
from snakes.arcs import MultiArc

class Node (object) :
    pass

class Place (Node) :
    def __init__ (self, name, tokens=[], type=None) :
        toks = []
        for t in tokens :
            if not isinstance(t, Token) :
                logging.warn("interpreted Python token %r in %s as source code %r"
                             % (t, name, repr(t)))
                t = Token(repr(t))
            toks.append(t)
        self.name = name
        self.tokens = mset(toks)
        self.type = type
    def __repr__ (self) :
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.name,
                                   list(self.tokens), self.type)
    def __iter__ (self) :
        return iter(self.tokens)
    def is_empty (self) :
        return bool(self.tokens)

class _Declarations (dict) :
    def __init__ (self, names) :
        dict.__init__(self)
        self.names = names
    def __setitem__ (self, name, type) :
        if self.get(name, type) != type :
            raise TypingError("variable '%s:%s' redeclared with type %r"
                              % (name, self[name], type))
        dict.__setitem__(self, name, type)
    def new (self, type) :
        name = self.names.fresh()
        self[name] = type
        return name

class Transition (Node) :
    def __init__ (self, name, guard=None) :
        self.name = name
        self.guard = guard
        self._input = {}
        self._output = {}
    def __repr__ (self) :
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.guard)
    def _astkey (self, arc) :
        return arc[1]._order
    def __ast__ (self, ctx) :
        names = WordSet(self.vars())
        ctx.update(names    = names,
                   marking  = names.fresh(base="marking"),
                   succ     = names.fresh(base="succ"),
                   sub      = collections.defaultdict(list),
                   add      = collections.defaultdict(list),
                   test     = collections.defaultdict(list),
                   notempty = set(),
                   declare  = _Declarations(names),
                   bound    = {},
                   trans    = self,
        )
        # input arcs
        arcs = []
        for place, label in self._input.items() :
            if isinstance(label, MultiArc) :
                arcs.extend((place, comp) for comp in label.components)
            else :
                arcs.append((place, label))
        arcs.sort(key=self._astkey)
        last = nest = []
        for place, label in arcs :
            last = label.__astin__(last, place, ctx,
                                   PLACE=place, ISIN=True, LABEL=label,
                                   BLAME=ctx.ArcBlame(place.name, self.name, label))
        # guard
        if self.guard :
            last.append(ctx.If(ctx.Expr(self.guard),
                               BLAME=ctx.GuardBlame(self.name, self.guard)))
            last = last[-1].body
        # output arcs
        arcs = []
        for place, label in self._output.items() :
            if isinstance(label, MultiArc) :
                arcs.extend((place, comp) for comp in label.components)
            else :
                arcs.append((place, label))
        for place, label in arcs :
            last = label.__astout__(last, place, ctx,
                                    PLACE=place, ISIN=False, LABEL=label,
                                    BLAME=ctx.ArcBlame(self.name, place.name, label))
        # eliminate tokens that are both consumed & produced in the same place
        for place in set(ctx.sub) & set(ctx.add) :
            sub = mset(ctx.sub[place])
            sub.discard(ctx.add[place])
            add = mset(ctx.add[place])
            add.discard(ctx.sub[place])
            if sub :
                ctx.sub[place] = list(sub)
            else :
                del ctx.sub[place]
            if add :
                ctx.add[place] = list(add)
            else :
                del ctx.add[place]
        # eliminate empty places
        for mk in (ctx.sub, ctx.add) :
            for place, tokens in list(mk.items()) :
                if not tokens :
                    del mk[place]
        # code to produce successor marking
        if ctx.test :
            for place, tokens in ctx.sub.items() :
                ctx.test[place].extend(tokens)
        else :
            ctx.test = {}
        tip = ctx.IfEnoughTokens(ctx.marking, ctx.test, ctx.sub, ctx.add,
                                 BLAME=ctx.TransitionBlame(self.name))
        last.append(tip)
        stop = [tip]
        inest = tip.copy(nest, stop)
        itip = stop[0]
        # generate top-level succ proc
        tip.body.append(ctx.AddSucc(ctx.succ, ctx.marking, ctx.test, ctx.sub, ctx.add,
                                    BLAME=ctx.TransitionBlame(self.name)))
        if ctx.notempty :
            yield ctx.DefSuccProc(ctx.SuccProcName(self.name), ctx.marking, ctx.succ, [
                ctx.Declare(dict(ctx.declare)),
                ctx.IfInput(ctx.marking, ctx.notempty, nest)])
        else :
            yield ctx.DefSuccProc(ctx.SuccProcName(self.name), ctx.marking, ctx.succ, [
                ctx.Declare(dict(ctx.declare))] + nest)
        # generate top-level succ func
        yield ctx.DefSuccFunc(ctx.SuccFuncName(self.name), ctx.marking, [
            ctx.InitSucc(ctx.succ),
            ctx.CallSuccProc(ctx.SuccProcName(self.name), ctx.marking, ctx.succ),
            ctx.ReturnSucc(ctx.succ)])
        # generate top-level succ iterator
        itip.body.append(ctx.YieldEvent(ctx.marking, ctx.test, ctx.sub, ctx.add,
                                        BLAME=ctx.TransitionBlame(self.name)))
        if ctx.notempty :
            yield ctx.DefSuccIter(ctx.SuccIterName(self.name), ctx.marking, [
                ctx.Declare(dict(ctx.declare)),
                ctx.IfInput(ctx.marking, ctx.notempty, inest)])
        else :
            yield ctx.DefIterProc(ctx.SuccIterName(self.name), ctx.marking, [
                ctx.Declare(dict(ctx.declare))] + inest)
    def add_input (self, place, label) :
        self._input[place] = label
    def remove_input (self, place) :
        del self._input[place]
    def add_output (self, place, label) :
        self._output[place] = label
    def remove_output (self, place) :
        del self._output[place]
    def vars (self) :
        return reduce(operator.or_, (a.vars() for a in self._input.values()), set())
    def input (self) :
        return self._input.items()
    def output (self) :
        return self._output.items()
