import operator, logging, collections
from functools import reduce
from . import TypingError
from .data import mset, WordSet, hashable
from .tokens import Token
from .arcs import MultiArc
from .utils import autorepr

class Node (object) :
    def __init__ (self, name) :
        self._name = name
    @property
    def name (self) :
        return self._name

@hashable
@autorepr(tokens=mset())
class Place (Node) :
    def __init__ (self, name, tokens=[], type=None) :
        super().__init__(name)
        toks = []
        for t in tokens :
            if not isinstance(t, Token) :
                logging.warn("interpreted Python token %r in %s as source code %r"
                             % (t, name, repr(t)))
                t = Token(repr(t))
            toks.append(t)
        self.tokens = mset(toks)
        self.type = type
    def _hash_items (self) :
        return [self.name]
    def __str__ (self) :
        return str(self.name)
    def __eq__ (self, other) :
        try :
            return self.name == other.name
        except :
            return False
    def __iter__ (self) :
        return iter(self.tokens)
    def __contains__ (self, token) :
        return token in self.tokens
    def is_empty (self) :
        return bool(self.tokens)
    def copy (self, name=None) :
        return self.__class__(name or self.name, self.tokens, self.type)
    def add (self, tokens) :
        self.tokens.add(tokens)
    def clear (self) :
        self.tokens.clear()
    def remove (self, tokens) :
        self.tokens.remove(tokens)
    def reset (self, tokens) :
        self.clear()
        self.add(tokens)

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

@hashable
@autorepr
class Transition (Node) :
    def __init__ (self, name, guard=None) :
        super().__init__(name)
        self.guard = guard
        self._input = {}
        self._output = {}
    def _hash_items (self) :
        return [self.name]
    def copy (self, name=None) :
        return self.__class__(name or self.name, self.guard)
    def __eq__ (self, other) :
        try :
            return self.name == other.name
        except :
            return False
    def __str__ (self) :
        return str(self.name)
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
            add = mset(ctx.add[place])
            newsub = sub / add
            newadd = add / sub
            if newsub != sub :
                ctx.test[place].extend(sub & add)
            if newsub :
                ctx.sub[place] = list(newsub)
            else :
                del ctx.sub[place]
            if newadd :
                ctx.add[place] = list(add)
            else :
                del ctx.add[place]
        # eliminate empty places
        for mk in (ctx.sub, ctx.add, ctx.test) :
            for place, tokens in list(mk.items()) :
                if not tokens :
                    del mk[place]
        # also test for tokens that will be consumed
        if ctx.test :
            for place, tokens in ctx.sub.items() :
                ctx.test[place].extend(tokens)
        else :
            ctx.test = {}
        # code to produce successor marking
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
            yield ctx.DefSuccIter(ctx.SuccIterName(self.name), ctx.marking, [
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
