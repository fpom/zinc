from snakes.data import mset, record
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
    def __ast__ (self) :
        flow_sub = {}
        flow_add = {}
        last = loopnest = []
        for place, label in self._input.items() :
            loop = label.__bindast__("marking", place.name)
            last.append(loop)
            last = loop.body
            flow_sub[place.name] = label.__flowast__()
        for place, label in self._output.items() :
            flow_add[place.name] = label.__flowast__()
        last.append(ast.If(ast.SourceExpr(self.guard), [
            ast.AddSucc("succ",
                        ast.AddMarking(
                            ast.SubMarking(ast.Name("marking"),
                                           ast.NewMarking(flow_sub)),
                            ast.NewMarking(flow_add)))]))
        yield ast.DefSuccProc(ast.SuccProcName(self.name), "marking", "succ", [
            ast.If(ast.And([ast.IsPlaceMarked("marking", p.name)
                            for p in self._input]), loopnest)])
        yield ast.DefSuccFunc(ast.SuccFuncName(self.name), "marking", [
            ast.InitSucc("succ"),
            ast.CallSuccProc(ast.SuccProcName(self.name), "marking", "succ"),
            ast.ReturnSucc("succ")])
    def add_input (self, place, label) :
        self._input[place] = label
    def add_output (self, place, label) :
        self._output[place] = label
    def input (self) :
        return self._input.items()
    def output (self) :
        return self._output.items()
