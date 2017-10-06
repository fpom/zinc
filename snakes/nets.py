from snakes import *
from snakes.arcs import *
from snakes.nodes import *
from snakes.data import *

import snakes.compil
from snakes.compil import ast

class BlackToken (object) :
    def __new__ (cls) :
        if not hasattr(cls, "dot") :
            cls.dot = object.__new__(cls)
        return cls.dot
    def __hash__ (self) :
        return hash(self.__class__.__name__)

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
    def __ast__ (self) :
        m = {}
        for place, tokens in self.items() :
            if tokens :
                l = m[place] = []
                for t in tokens :
                    if isinstance(t, Expression) :
                        l.append(ast.Expression(t.code))
                    elif isinstance(t, Value) :
                        l.append(ast.Value(t.value))
                    else :
                        l.append(ast.Value(repr(t)))
        return ast.NewMarking(m)

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
        mod = ast.Module([ast.DefineMarking([(p.name, p.tokens, p.props)
                                             for p in self._place.values()])])
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

if __name__ == "__main__" :
    n = PetriNet("net")
    n.add_place(Place("p1", range(3)))
    n.add_place(Place("p2", range(1,4)))
    n.add_place(Place("p3"))
    n.add_transition(Transition("t1", "x!=y"))
    n.add_input("p1", "t1", Value("0"))
    n.add_input("p2", "t1", Variable("y"))
    n.add_output("p3", "t1", Expression("x+y"))
    n.add_transition(Transition("t2", "z<=5"))
    n.add_input("p2", "t2", Variable("z"))
    n.add_output("p1", "t2", Value("0"))
    n.add_output("p2", "t2", Expression("z+2"))
    from snakes.compil.python import codegen
    tree = n.__ast__()
    gen = codegen(tree)
    lines = gen.output.getvalue().splitlines() + [""]
    def get (loc) :
        if loc is None :
            return ""
        code = []
        (l0, c0), (l1, c1) = loc
        for i in range(l0, l1+1) :
            if i == l0 == l1 :
                return lines[i][c0:c1+1]
            elif i == l0 :
                code.append(" " * c0 + lines[i][c0:])
            elif i == l1 :
                code.append(lines[i][:c1+1])
            else :
                code.append(lines[i])
        return "\n".join(code)
    found = tree.locate(9, 45)
    for node in found :
        print("###", node.__class__.__name__, node.loc)
        print(get(node.loc))
        print("#" * 79)
