from snakes import *
from snakes.arcs import *
from snakes.nodes import *
from snakes.data import *

import snakes.compil

class BlackToken (object) :
    def __new__ (cls) :
        if not hasattr(cls, "dot") :
            cls.dot = object.__new__(cls)
        return cls.dot
    def __hash__ (self) :
        return 1957834143963438608 # == hash("BlackToken")

dot = BlackToken()

@hashable
class Marking (dict) :
    def _hash_items (self) :
        return self.items()
    def __call__ (self, place) :
        return self.get(place, mset())
    def copy (self) :
        return self.__class__((k, v.copy()) for k, v in self.items())
    def __add__ (self, other) :
        new = self.copy()
        for k, v in other.items() :
            if k not in new :
                new[k] = v
            else :
                new[k].add(v)
        return new
    def __sub__ (self, other) :
        new = self.copy()
        for k, v in other.items() :
            if new[k] == v :
                del new[k]
            else :
                new[k] -= v
        return new
    def __le__ (self, other) :
        return all(self(k) <= other(k) for k in self.keys())
    def __lt__ (self, other) :
        return (self != other) and (self <= other)
    def __ge__ (self, other) :
        return all(self(k) >= other(k) for k in other.keys())
    def __gt__ (self, other) :
        return (self != other) and (self >= other)

class PetriNet (object) :
    def __init__ (self, name, lang="python") :
        self.name = name
        self.lang = snakes.compil.getlang(lang)
        self._trans = {}
        self._place = {}
        self._node = {}
    def _add_node (self, node, store) :
        if node.name in self._node :
            raise ConstraintError("a node %r exists" % node.name)
        elif hasattr(node, "net") and node.net is not None :
            raise ConstraintError("node %r already in net %r"
                                  % (node.name, node.net.name))
        self._node[node.name] = store[node.name] = node
        node.net = self
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
        if not label.input_allowed :
            raise ConstraintError("%r not allowed on input arcs"
                                  % label.__class__.__name__)
        elif hasattr(label, "net") and label.net is not None :
            raise ConstraintError("label %s already in net %r" % (label, label.net.name))
        p = self.place(place)
        t = self.transition(trans)
        t.add_input(p, label)
        p.post[trans] = t.pre[place] = label
        label.net = self
    def add_output (self, place, trans, label) :
        if hasattr(label, "net") and label.net is not None :
            raise ConstraintError("label %s already in net %r" % (label, label.net.name))
        p = self.place(place)
        t = self.transition(trans)
        t.add_output(p, label)
        p.pre[trans] = t.post[place] = label
        label.net = self
    def get_marking (self) :
        return Marking((p.name, p.tokens.copy()) for p in self.place())
