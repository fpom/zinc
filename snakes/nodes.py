import operator
from functools import reduce
from snakes.data import mset, record, WordSet
from snakes.compil import ast

class Node (object) :
    pass

class Place (Node) :
    def __init__ (self, name, tokens=[], props={}) :
        self.name = name
        self.tokens = mset(tokens)
        self.props = record(props)
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
        ctx.bounded = set()
        flow_sub = {}
        flow_add = {}
        last = loopnest = []
        for place, label in sorted(self._input.items(), key=self._astkey) :
            last = label.__bindast__(last, ctx.marking, place.name)
            flow_sub[place.name] = label.__flowast__()
            ctx.bounded.update(label.vars())
        for place, label in self._output.items() :
            flow_add[place.name] = label.__flowast__()
        last.append(ast.If(ast.SourceExpr(self.guard), [
            ast.AddSucc(
                ctx.succ,
                ast.Name(ctx.marking),
                ast.NewMarking([ast.NewPlaceMarking(p, t) for p, t in flow_sub.items()]),
                ast.NewMarking([ast.NewPlaceMarking(p, t) for p, t in flow_add.items()]))]))
        yield ast.DefSuccProc(ast.SuccProcName(self.name), ctx.marking, ctx.succ, [
            ast.If(ast.And([ast.IsPlaceMarked(ctx.marking, p.name)
                            for p in self._input]),
                   loopnest)])
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
