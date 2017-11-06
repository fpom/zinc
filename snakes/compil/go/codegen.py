from operator import attrgetter

from snakes.compil import ast
from snakes import TypingError

def S (text) :
    return '"%s"' % text.replace('"', '\\"')

preamble = """// %(timestamp)s
package main

import "snk"
var NET string = %(net)s
"""

closing = """
func StateSpace () snk.Graph {
    return snk.StateSpace(Init, AddSucc)
}

func Reachable () snk.Set {
    return snk.Reachable(Init, AddSucc)
}

func DeadLocks () snk.Set {
    return snk.DeadLocks(Init, AddSucc)
}

func main () {
    snk.Main(NET, Init, AddSucc)
}
"""

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        self.write(preamble % {"timestamp" : self.timestamp(), "net" : S(node.name)})
        self.children_visit(node.body)
        self.fill(closing)
    def _typedef (self, typ, place) :
        if typ is None or typ in self.typedef :
            pass
        elif isinstance(typ, str) and typ.endswith("()") :
            self.typedef[typ] = "interface{}"
        elif isinstance(typ, str) :
            self.typedef[typ] = typ
        elif isinstance(typ, tuple) :
            fields = [self._typedef(t, "%s._%s" % (place, i))
                      for i, t in enumerate(typ)]
            name = self.typedef[typ] = "tuple%03u" % len(self.typedef)
            self.fill("// tokens in %r" % place)
            self.fill("type %s struct {" % name)
            with self.indent() :
                for i, f in enumerate(fields) :
                    self.fill("_%s %s" % (i, f))
            self.fill("}\n")
        else :
            raise TypingError("don't know how to implement type %r" % typ)
        return self.typedef[typ]
    def visit_DefineMarking (self, node) :
        self.typedef = {None : "interface{}"}
        for place in node.places :
            self._typedef(place.type, place.name)
    def visit_SuccProcName (self, node) :
        if not node.trans :
            name = "AddSucc"
        elif node.trans not in self.succproc :
            name = "AddSucc%03u" % (len(self.succproc) + 1)
        else :
            name = self.succproc[node.trans]
        self.succproc[node.trans] = name
        self.write(name)
    def visit_SuccFuncName (self, node) :
        if not node.trans :
            name = "Succ"
        elif node.trans not in self.succfunc :
            name = "Succ%03u" % (len(self.succfunc) + 1)
        else :
            name = self.succfunc[node.trans]
        self.succfunc[node.trans] = name
        self.write(name)
    def visit_InitName (self, node) :
        name = self.initfunc = "Init"
        self.write(name)
    def visit_DefSuccProc (self, node) :
        self.unused = set()
        self.fill("func ")
        self.visit(node.name)
        self.write(" (%s snk.Marking, %s snk.Set) {" % (node.marking, node.succ))
        with self.indent() :
            if node.name.trans :
                self.fill("// successors for transition %r" % node.name.trans)
            else :
                self.fill("// successors for all transitions")
        self.children_visit(node.body, True)
        with self.indent() :
            if self.unused :
                self.fill("// work around 'declared and not used' compilation error")
                self.fill("// variables are kept to be typechecked by the compiler")
                self.fill("return")
                for var in self.unused :
                    self.fill("_ = %s" % var)
        self.fill("}\n")
    def visit_Declare (self, node) :
        self.unused.update(node.variables)
        for var, typ in node.variables.items() :
            if isinstance(typ, tuple) and typ[0] == "mset" :
                self.typedef[typ] = "snk.Mset"
            self.fill("var %s %s" % (var, self.typedef[typ]))
    def visit_Assign (self, node) :
        self.fill("%s = " % node.variable)
        self.visit(node.expr)
    def visit_AssignItem (self, node) :
        self.unused.discard(node.container)
        self.fill("%s = %s" % (node.variable, node.container))
        for p in node.path :
            self.write("._%s" % p)
    def visit_Expr (self, node) :
        self.unused.discard(node.source)
        self.write(node.source)
    def visit_IfInput (self, node) :
        self.fill("if %s.NotEmpty(%s) {"
                  % (node.marking, ", ".join(S(p.name) for p in node.places)))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfToken (self, node) :
        self.unused.discard(node.token)
        self.fill("if %s.Get(%s).Count(%s) > 0 {"
                  % (node.marking, S(node.place.name), node.token))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfNoToken (self, node) :
        self.unused.discard(node.token)
        self.fill("if %s.Get(%s).Count(%s) == 0 {"
                  % (node.marking, S(node.place.name), node.token))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfNoTokenSuchThat (self, node) :
        bvar = node.CTX.names.fresh()
        tvar = node.CTX.names.fresh(base=node.variable)
        self.fill("%s := true" % bvar)
        self.fill("for %s := range %s.Iter(%s) {"
                  % (tvar, node.marking, S(node.place.name)))
        with self.indent() :
            self.fill("%s = (%s).(%s)"
                      % (node.variable, tvar, self.typedef[node.place.type]))
            self.fill("if ")
            self.visit(node.guard)
            self.write(" {")
            with self.indent() :
                self.fill("%s = false" % bvar)
                self.fill("break")
            self.fill("}")
        self.fill("}")
        self.fill("if %s {" % bvar)
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_GetPlace (self, node) :
        self.fill("%s = %s.Get(%s)" % (node.variable, node.marking, S(node.place.name)))
    def visit_ForeachToken (self, node) :
        var = node.NAMES.fresh(base=node.variable, add=True)
        self.fill("for %s := range %s.Iter(%s) {"
                  % (var, node.marking, S(node.place.name)))
        with self.indent() :
            self.fill("%s = (%s).(%s)"
                      % (node.variable, var, self.typedef[node.place.type]))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_Break (self, node) :
        self.fill("break")
    def visit_IfPlace (self, node) :
        self.unused.discard(node.variable)
        self.fill("if %s.Get(%s).Eq(%s) {"
                  % (node.marking, S(node.place.name), node.variable))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfAllType (self, node) :
        if node.place.type :
            self.unused.discard(node.variable)
            bvar = node.CTX.names.fresh()
            tvar = node.CTX.names.fresh()
            self.fill("%s := true" % bvar)
            self.fill("for %s := range %s.Iter() {"
                      % (tvar, node.variable))
            with self.indent() :
                self.fill("_, %s = (%s).(%s)"
                          % (bvar, tvar, self.typedef[node.place.type]))
                self.fill("if ! %s { break }" % bvar)
            self.fill("}")
            self.fill("if %s {" % bvar)
            self.children_visit(node.body, True)
            self.fill("}")
        else :
            self.children_visit(node.body, False)
    def visit_If (self, node) :
        self.fill("if ")
        self.visit(node.guard)
        self.write(" {")
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_TrueConst (self, node) :
        self.write("true")
    def visit_FalseConst (self, node) :
        self.write("false")
    def visit_And (self, node) :
        for i, item in enumerate(node.items) :
            if i > 0 :
                self.write(" && ")
            self.visit(item)
    def visit_Eq (self, node) :
        self.write("(")
        self.visit(node.left)
        self.write(") == (")
        self.visit(node.right)
        self.write(")")
    def visit_IfType (self, node) :
        if isinstance(node.place.type, str) and node.place.type.endswith("()") :
            self.unused.discard(node.token)
            self.fill("if %s(%s) {" % (node.place.type[:-2], node.token))
            self.children_visit(node.body, True)
            self.fill("}")
        else :
            self.children_visit(node.body, False)
    def visit_IfTuple (self, node) :
        self.children_visit(node.body)
    def _pattern (self, matcher, placetype) :
        self.unused.difference_update(matcher)
        return "%s{%s}" % (self.typedef[placetype],
                           ", ".join(self._pattern(m, t) if isinstance(m, tuple)
                                     else m for m, t in zip(matcher, placetype)))
    def _newmarking (self, name, marking, assign) :
        self.fill("%s := snk.Marking{}" % name)
        whole = []
        for place, tokens in marking.items() :
            found = False
            for i, tok in enumerate(tokens) :
                if tok in assign :
                    src = assign[tok]
                elif isinstance(tok, tuple) and tok[0] == "mset" :
                    whole.append((place, tok[1]))
                    continue
                elif isinstance(tok, ast.Pattern) :
                    src = self._pattern(tok.matcher, tok.placetype)
                else :
                    src = tok
                if i == 0 :
                    self.fill("%s.Set(%s" % (name, S(place)))
                self.write(", %s" % src)
                found = True
                self.unused.discard(src)
            if found :
                self.write(")")
        for place, tokens in whole :
            self.unused.discard(tokens)
            self.fill("%s.Update(%s, %s)" % (name, S(place), tokens))
    def visit_AddSuccIfEnoughTokens (self, node) :
        subtest = False
        subvar = node.NAMES.fresh(base="sub")
        if node.test :
            testvar = node.NAMES.fresh(base="test")
            self._newmarking(testvar, node.test, node.BOUND)
            self.fill("if %s.Geq(%s) {" % (node.old, testvar))
            indent = 1
        elif node.sub :
            subtest = True
            self._newmarking(subvar, node.sub, node.BOUND)
            self.fill("if %s.Geq(%s) {" % (node.old, subvar))
            indent = 1
        else :
            indent = 0
        with self.indent(indent) :
            if node.sub and not subtest :
                self._newmarking(subvar, node.sub, node.BOUND)
            if node.add :
                addvar = node.NAMES.fresh(base="add")
                self._newmarking(addvar, node.add, node.BOUND)
            if node.sub and node.add :
                self.fill("%s.Add(%s.Copy().Sub(%s).Add(%s))"
                          % (node.succ, node.old, subvar, addvar))
            elif node.sub :
                self.fill("%s.Add(%s.Copy().Sub(%s))" % (node.succ, node.old, subvar))
            elif node.add :
                self.fill("%s.Add(%s.Copy().Add(%s))" % (node.succ, node.old, addvar))
            else :
                self.fill("%s.Add(%s.Copy())"  % (node.succ, node.old))
        if indent :
            self.fill("}")
    def visit_DefSuccFunc (self, node) :
        self.fill("func ")
        self.visit(node.name)
        self.write(" (%s snk.Marking) snk.Set {" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill("// successors of %r" % node.name.trans)
            else :
                self.fill("// successors for all transitions")
        self.children_visit(node.body, True)
        self.fill("}\n")
    def visit_InitSucc (self, node) :
        self.fill("%s := snk.Set{}" % node.name)
    def visit_CallSuccProc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write("(%s, %s)" % (node.marking, node.succ))
    def visit_ReturnSucc (self, node) :
        self.fill("return %s" % node.name)
    def visit_DefInitFunc (self, node) :
        self.fill("func ")
        self.visit(node.name)
        self.write(" () snk.Marking {")
        with self.indent() :
            self.fill("// initial marking")
            self.fill("init := snk.Marking{}")
            for place in sorted(node.marking, key=attrgetter("place")) :
                self.fill("init.Set(")
                self.visit(place)
                self.write(")")
            self.fill("return init")
        self.fill("}\n")
    def visit_PlaceMarking (self, node) :
        self.write(S(node.place))
        for tok in node.tokens :
            self.write(", %s" % tok.source)
    def visit_SuccProcTable (self, node) :
        self.fill("// map transitions names to successor procs")
        self.fill('// "" maps to all-transitions proc')
        self.fill("type SuccProcType func(snk.Marking, snk.Set)")
        self.fill("var SuccProc map[string]SuccProcType = map[string]SuccProcType{")
        with self.indent() :
            for trans, name in sorted(self.succproc.items()) :
                self.fill("%s: %s," % (S(trans or ""), name))
        self.fill("}\n")
    def visit_SuccFuncTable (self, node) :
        self.fill("// map transitions names to successor funcs")
        self.fill('// "" maps to all-transitions func')
        self.fill("type SuccFuncType func(snk.Marking)snk.Set")
        self.fill("var SuccFunc map[string]SuccFuncType = map[string]SuccFuncType{")
        with self.indent() :
            for trans, name in sorted(self.succfunc.items()) :
                self.fill("%s: %s," % (S(trans or ""), name))
        self.fill("}\n")

if __name__ == "__main__" :
    import io, sys
    from snakes.io.snk import load
    net = load(open(sys.argv[-1]))
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
