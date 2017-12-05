from zinc import *
from zinc.arcs import *
from zinc.nodes import *
from zinc.data import *
from zinc.tokens import *

import zinc.compil

class PetriNet (object) :
    def __init__ (self, name, lang="python") :
        self.name = name
        self.lang = zinc.compil.getlang(lang)
        self.declare = self.lang.Declare()
        self._trans = {}
        self._place = {}
        self._node = {}
    def __repr__ (self) :
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.lang.name)
    def build (self, name="net", saveto=None, **options) :
        return zinc.compil.build(self.lang, self.__ast__(name), saveto, **options)
    def __ast__ (self, name="net") :
        ctx = zinc.compil.Context(net=self)
        mod = ctx.Module(name,
                         [ctx.Context(self.declare.copy()),
                          ctx.DefineMarking(list(self._place.values()))])
        for name, trans in sorted(self._trans.items()) :
            mod.body.extend(trans.__ast__(zinc.compil.Context(net=self)))
        mod.body.append(ctx.DefSuccProc(ctx.SuccProcName(), "marking", "succ", [
            ctx.CallSuccProc(ctx.SuccProcName(t.name), "marking", "succ")
            for n, t in sorted(self._trans.items())]))
        mod.body.append(ctx.DefSuccFunc(ctx.SuccFuncName(), "marking", [
            ctx.InitSucc("succ"),
            ctx.CallSuccProc(ctx.SuccProcName(), "marking", "succ"),
            ctx.ReturnSucc("succ")]))
        mod.body.append(ctx.DefSuccIter(ctx.SuccIterName(), "marking", [
            ctx.SuccIterName(t.name) for n, t in sorted(self._trans.items())]))
        marking = self.get_marking().__ast__(zinc.compil.Context(net=self))
        mod.body.extend([ctx.DefInitFunc(ctx.InitName(), marking),
                         ctx.SuccProcTable(),
                         ctx.SuccFuncTable(),
                         ctx.SuccIterTable()])
        return mod
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
        if place in t.pre :
            raise ConstraintError("arc from %s to %s already exists"
                                  % (place, trans))
        t.add_input(p, label)
        p.post[trans] = t.pre[place] = label
    def remove_input (self, place, trans) :
        p = self.place(place)
        t = self.transition(trans)
        if place not in t.pre :
            raise ConstraintError("not arc from %s to %s" % (place, trans))
        t.remove_input(p)
        del p.post[trans], t.pre[place]
    def add_output (self, place, trans, label) :
        if not isinstance(label, OutputArc) :
            raise ConstraintError("%r not allowed on output arcs"
                                  % label.__class__.__name__)
        p = self.place(place)
        t = self.transition(trans)
        if place in t.post :
            raise ConstraintError("arc from %s to %s already exists"
                                  % (trans, place))
        t.add_output(p, label)
        p.pre[trans] = t.post[place] = label
    def remove_output (self, place, trans) :
        p = self.place(place)
        t = self.transition(trans)
        if place not in t.post :
            raise ConstraintError("not arc from %s to %s" % (trans, place))
        t.remove_output(p)
        del p.pre[trans], t.post[place]
    def get_marking (self) :
        return Marking((p.name, p.tokens.copy()) for p in self.place()
                       if p.tokens)
