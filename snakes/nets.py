from snakes import *
from snakes.arcs import *
from snakes.nodes import *
from snakes.data import *
from snakes.tokens import *

import snakes.compil
from snakes.compil import ast

class PetriNet (object) :
    def __init__ (self, name, lang="python") :
        self.name = name
        self.lang = snakes.compil.getlang(lang)
        self._context = []
        self._trans = {}
        self._place = {}
        self._node = {}
    def __ast__ (self) :
        ctx = record(net=self)
        mod = ast.Module([ast.Context(l, BLAME=ast.ContextBlame(l))
                          for c in self._context for l in c.splitlines()] + [
            ast.DefineMarking(list(self._place.values()))])
        for t in self._trans.values() :
            mod.body.extend(t.__ast__(ctx.copy()))
        mod.body.append(ast.DefSuccProc(ast.SuccProcName(), "marking", "succ", [
            ast.CallSuccProc(ast.SuccProcName(t.name), "marking", "succ")
            for t in self._trans.values()]))
        mod.body.append(ast.DefSuccFunc(ast.SuccFuncName(), "marking", [
            ast.InitSucc("succ"),
            ast.CallSuccProc(ast.SuccProcName(), "marking", "succ"),
            ast.ReturnSucc("succ")]))
        marking = self.get_marking().__ast__()
        mod.body.append(ast.DefInitMarking(ast.InitName(), marking))
        return mod
    def declare (self, code) :
        self._context.append(code)
    def _add_node (self, node, store) :
        if node.name in self._node :
            raise ConstraintError("a node %r exists" % node.name)
        self._node[node.name] = store[node.name] = node
        node.pre = {}
        node.post = {}
    def add_place (self, place) :
        self._add_node(place, self._place)
    def add_transition (self, trans) :
        self._add_node(trans, self._trans)
    def place (self, name=None) :
        if name is None :
            return self._place.values()
        elif name in self._place :
            return self._place[name]
        else :
            raise ConstraintError("place %r not found" % name)
    def transition (self, name=None) :
        if name is None :
            return self._trans.values()
        elif name in self._trans :
            return self._trans[name]
        else :
            raise ConstraintError("transition %r not found" % name)
    def node (self, name=None) :
        if name is None :
            return self._node.itervalues()
        elif name in self._node :
            return self._node[name]
        else :
            raise ConstraintError("node %r not found" % name)
    def add_input (self, place, trans, label) :
        if not isinstance(label, InputArc) :
            raise ConstraintError("%r not allowed on input arcs"
                                  % label.__class__.__name__)
        p = self.place(place)
        t = self.transition(trans)
        t.add_input(p, label)
        p.post[trans] = t.pre[place] = label
    def add_output (self, place, trans, label) :
        if not isinstance(label, OutputArc) :
            raise ConstraintError("%r not allowed on output arcs"
                                  % label.__class__.__name__)
        p = self.place(place)
        t = self.transition(trans)
        t.add_output(p, label)
        p.pre[trans] = t.post[place] = label
    def get_marking (self) :
        return Marking((p.name, p.tokens.copy()) for p in self.place()
                       if p.tokens)
