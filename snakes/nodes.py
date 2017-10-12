import operator, logging, collections
from functools import reduce
from snakes.data import mset, WordSet
from snakes.tokens import Token

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

class Transition (Node) :
    def __init__ (self, name, guard=None) :
        self.name = name
        self.guard = guard
        self._input = {}
        self._output = {}
    def _astkey (self, arc) :
        return arc[1]._order
    def __ast__ (self, ctx) :
        names = WordSet(self.vars())
        ctx.update(names   = names,
                   trans   = self,
                   marking = names.fresh(base="marking", add=True),
                   succ    = names.fresh(base="succ", add=True),
                   sub     = collections.defaultdict(mset),
                   add     = collections.defaultdict(mset),
                   assign  = {})
        last = nest = []
        for place, label in sorted(self._input.items(), key=self._astkey) :
            last = label.__ast__(last, place, self, True, ctx,
                                 PLACE=place, ISIN=True, LABEL=label,
                                 BLAME=ctx.ArcBlame(place.name, self.name, label))
        last.append(ctx.IfGuard(ctx.Expr(self.guard), [],
                                BLAME=ctx.GuardBlame(self.name, self.guard)))
        last = last[-1].body
        for place, label in self._output.items() :
            last = label.__ast__(last, place, self, False, ctx,
                                 PLACE=place, ISIN=False, LABEL=label,
                                 BLAME=ctx.ArcBlame(self.name, place.name, label))
        last.append(ctx.AddSuccIfEnoughTokens(ctx.succ, ctx.marking, ctx.sub, ctx.add))
        yield ctx.DefSuccProc(ctx.SuccProcName(self.name), ctx.marking, ctx.succ, [
            ctx.IfInput(ctx.marking, [p.name for p in self._input], nest)])
        yield ctx.DefSuccFunc(ctx.SuccFuncName(self.name), ctx.marking, [
            ctx.InitSucc(ctx.succ),
            ctx.CallSuccProc(ctx.SuccProcName(self.name), ctx.marking, ctx.succ),
            ctx.ReturnSucc(ctx.succ)])
    def add_input (self, place, label) :
        self._input[place] = label
    def add_output (self, place, label) :
        self._output[place] = label
    def vars (self) :
        return reduce(operator.or_, (a.vars() for a in self._input.values()), set())
    def input (self) :
        return self._input.items()
    def output (self) :
        return self._output.items()
