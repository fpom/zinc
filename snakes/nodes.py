import operator, logging, collections
from functools import reduce
from snakes.data import mset, WordSet
from snakes.compil import ast
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
        ctx.names = WordSet(self.vars())
        ctx.marking = ctx.names.fresh(base="marking", add=True)
        ctx.succ = ctx.names.fresh(base="succ", add=True)
        ctx.sub = collections.defaultdict(mset)
        ctx.add = collections.defaultdict(mset)
        last = nest = []
        for place, label in sorted(self._input.items(), key=self._astkey) :
            last = label.__ast__(last, place, self, True, ctx,
                                 BLAME=ast.ArcBlame(place.name, self.name, label))
        last.append(ast.IfGuard(ast.Expr(self.guard), []))
        last = last[-1].body
        for place, label in self._output.items() :
            last = label.__ast__(last, place, self, False, ctx,
                                 BLAME=ast.ArcBlame(self.name, place.name, label))
        last.append(ast.AddSuccIfEnoughTokens(ctx.succ, ctx.marking, ctx.sub, ctx.add,
                                              NAMES=ctx.names))
        yield ast.DefSuccProc(ast.SuccProcName(self.name), ctx.marking, ctx.succ, [
            ast.IfInput(ctx.marking, [p.name for p in self._input], nest)])
        yield ast.DefSuccFunc(ast.SuccFuncName(self.name), ctx.marking, [
            ast.InitSucc(ctx.succ),
            ast.CallSuccProc(ast.SuccProcName(self.name), ctx.marking, ctx.succ),
            ast.ReturnSucc(ctx.succ)])
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
