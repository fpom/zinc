from . import CompileError, ConstraintError, LanguageError, ParseError, \
    TypingError, ZINCError
from .arcs import Arc, Expression, Fill, Flush, Inhibitor, InputArc, MultiArc, \
    OutputArc, Test, Tuple, Value, Variable
from .nodes import Node, Place, Transition
from .data import WordSet, hashable, hdict, iterate, mset, mutation, nest, record
from .tokens import BlackToken, BlackWhiteToken, CodeToken, Marking, Token, \
    black, dot, white
from .utils import autorepr

import zinc.compil

class NodeError (ConstraintError) :
    pass

class ArcError (ConstraintError) :
    pass

@hashable
@autorepr
class PetriNet (object) :
    def __init__ (self, name, lang="python") :
        self._name = name
        self.lang = zinc.compil.getlang(lang)
        self.declare = self.lang.Declare()
        self._trans = {}
        self._place = {}
        self._node = {}
    @property
    def name (self) :
        return self._name
    def _hash_items (self) :
        return [self.name]
    def __eq__ (self, other) :
        try :
            return self.name == other.name
        except :
            return False
    def __str__ (self) :
        return str(self.name)
    def copy (self, name=None) :
        net = self.__class__(name or self.name, self.lang.name)
        net.declare = self.declare.copy()
        for place in self.place() :
            net.add_place(place.copy())
        for trans in self.transition() :
            net.add_transition(trans.copy())
            for place, label in trans.input() :
                net.add_input(place.name, trans.name, label.copy())
            for place, label in trans.output() :
                net.add_output(place.name, trans.name, label.copy())
        return net
    ##
    ## compilation
    ##
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
    ##
    ## nodes
    ##
    def _add_node (self, node, store) :
        if node.name in self._node :
            raise NodeError("a node %r exists" % node.name)
        self._node[node.name] = store[node.name] = node
        node.pre = {}
        node.post = {}
    def _remove_node (self, name, store) :
        del store[name]
        del self._node[name]
    def add_place (self, place) :
        self._add_node(place, self._place)
    def add_transition (self, trans) :
        self._add_node(trans, self._trans)
    def remove_place (self, name) :
        place = self.place(name)
        self._remove_node(name, self._place)
        for trans in place.post :
            self.remove_input(place.name, trans)
        for trans in place.pre :
            self.remove_output(place.name, trans)
    def remove_transition (self, name) :
        trans = self.transition(name)
        self._remove_node(name, self._trans)
        for place in trans.pre :
            self.remove_input(place, trans.name)
        for place in trans.post :
            self.remove_output(place, trans.name)
    def place (self, name=None) :
        if name is None :
            return self._place.values()
        elif name in self._place :
            return self._place[name]
        else :
            raise NodeError("place %r not found" % name)
    def has_place (self, name) :
        return name in self._place
    def has_transition (self, name) :
        return name in self._trans
    def has_node (self, name) :
        return name in self._node
    def __contains__ (self, name) :
        return name in self._node
    def transition (self, name=None) :
        if name is None :
            return self._trans.values()
        elif name in self._trans :
            return self._trans[name]
        else :
            raise NodeError("transition %r not found" % name)
    def node (self, name=None) :
        if name is None :
            return self._node.itervalues()
        elif name in self._node :
            return self._node[name]
        else :
            raise NodeError("node %r not found" % name)
    def copy_place (self, source, target) :
        src = self.place(source)
        self.add_place(src.copy())
        for trans, label in src.post.items() :
            self.add_input(source, trans, label)
        for trans, label in src.pre.items() :
            self.add_output(source, trans, label)
    def copy_transition (self, source, target) :
        src = self.transition(source)
        self.add_transition(src.copy())
        for place, label in src.pre.items() :
            self.add_input(place, source, label)
        for place, label in src.post.items() :
            self.add_output(place, source, label)
    def rename_node (self, old, new) :
        if old in self._place :
            self.rename_place(old, new)
        else :
            self.rename_transition(old, new)
    def rename_place (self, old, new) :
        self.copy_place(old, new)
        self.remove_place(old)
    def rename_transition (self, old, new) :
        self.copy_transition(old, new)
        self.remove_transition(old)
    def merge_places (self, target, sources) :
        src = [self.place(p) for p in iterate(sources)]
        tgt = src[0].copy(name=target)
        types = [s.type for s in src if s.type is not None]
        if types :
            tgt.type = self.lang.union(*types)
        self.add_place(tgt)
        for s in src[1:] :
            tgt.tokens.add(s.tokens)
            for trans, label in s.post.items() :
                self.add_input(target, trans, label, aggregate=True)
            for trans, label in s.pre.items() :
                self.add_output(target, trans, label, aggregate=True)
    def merge_transitions (self, target, sources) :
        src = [self.transition(t) for t in iterate(sources)]
        tgt = src[0].copy(name=target)
        guards = [s.guard for s in src if s.guard is not None]
        if guards :
            tgt.guard = self.lang.and_(*guards)
        self.add_transition(tgt)
        for s in src[1:] :
            for place, label in s.post.items() :
                self.add_output(place, target, label, aggregate=True)
            for place, label in s.pre.items() :
                self.add_input(place, target, label, aggregate=True)
    ##
    ## arcs
    ##
    def add_input (self, place, trans, label, aggregate=True) :
        if not isinstance(label, InputArc) :
            raise ArcError("%r not allowed on input arcs" % label.__class__.__name__)
        p = self.place(place)
        t = self.transition(trans)
        if place in t.pre :
            if aggregate :
                label = t.pre[place] + label
            else :
                raise ArcError("arc from %s to %s already exists" % (place, trans))
        t.add_input(p, label)
        p.post[trans] = t.pre[place] = label
    def remove_input (self, place, trans, label=None) :
        p = self.place(place)
        t = self.transition(trans)
        if place not in t.pre :
            raise ArcError("not arc from %s to %s" % (place, trans))
        elif label is None :
            t.remove_input(p)
            del p.post[trans], t.pre[place]
        else :
            label = t.pre[place] - label
            t.add_input(p, label)
            p.post[trans] = t.pre[place] = label
    def add_output (self, place, trans, label, aggregate=True) :
        if not isinstance(label, OutputArc) :
            raise ArcError("%r not allowed on output arcs" % label.__class__.__name__)
        p = self.place(place)
        t = self.transition(trans)
        if place in t.post :
            if aggregate :
                label = t.post[place] + label
            else :
                raise ArcError("arc from %s to %s already exists" % (trans, place))
        t.add_output(p, label)
        p.pre[trans] = t.post[place] = label
    def remove_output (self, place, trans, label=None) :
        p = self.place(place)
        t = self.transition(trans)
        if place not in t.post :
            raise ArcError("not arc from %s to %s" % (trans, place))
        elif label is None :
            t.remove_output(p)
            del p.pre[trans], t.post[place]
        else :
            label = t.post[place] - label
            t.add_output(p, label)
            p.pre[trans] = t.post[place] = label
    def pre (self, nodes) :
        result = set()
        for node in iterate(nodes) :
            try :
                result.update(self._node[node].pre.keys())
            except KeyError :
                raise NodeError("node '%s' not found" % node)
        return result
    def post (self, nodes) :
        result = set()
        for node in iterate(nodes) :
            try :
                result.update(self._node[node].post.keys())
            except KeyError :
                raise NodeError("node '%s' not found" % node)
        return result
    ##
    ## markings
    ##
    def get_marking (self) :
        return Marking((p.name, p.tokens.copy()) for p in self.place()
                       if p.tokens)
    def add_marking (self, marking, times=1) :
        for place, tokens in marking.items() :
            self.place(place).add(tokens, times)
    def set_marking (self, marking) :
        for place, tokens in marking.items() :
            self.place(place).reset(tokens)
    def sub_marking (self, marking, times=1) :
        for place, tokens in marking.items() :
            self.place(place).sub(tokens, times)
