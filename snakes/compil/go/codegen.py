import snakes.compil.ast as ast
from snakes import arcs

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
    def visit_DefineMarking (self, node) :
        pass
    def visit_SuccProcName (self, node) :
        if node.trans is None :
            name = "AddSucc"
        elif node.trans not in self.succproc :
            name = "AddSucc%03u" % (len(self.succproc) + 1)
        else :
            name = self.succproc[node.trans]
        self.succproc[node.trans] = name
        self.write(name)
    def visit_SuccFuncName (self, node) :
        if node.trans is None :
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
        self.fill("func ")
        self.visit(node.name)
        self.write(" (%s snk.Marking, %s snk.Set) {" % (node.marking, node.succ))
        with self.indent() :
            if node.name.trans :
                self.fill("// successors of %r" % node.name.trans)
                for var, typ in node.ASSIGN.values() :
                    self.fill("var %s %s" % (var, typ))
            else :
                self.fill("// successors for all transitions")
        self.children_visit(node.body, True)
        self.fill("}\n")
    def visit_Assign (self, node) :
        self.fill("%s = %s" % (node.variable, node.expr))
    def visit_IfInput (self, node) :
        self.fill("if %s.NotEmpty(%s) {"
                  % (node.marking, ", ".join(S(p) for p in node.places)))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfToken (self, node) :
        self.fill("if %s.Get(%s).Count(%s) > 0 {"
                  % (node.marking, S(node.place), node.token.source))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_ForeachToken (self, node) :
        var = node.NAMES.fresh(base=node.variable, add=True)
        self.fill("for %s := range %s.Iter(%s) {"
                  % (var, node.marking, S(node.place)))
        with self.indent() :
            self.fill("%s := (%s).(%s)"
                      % (node.variable, var, node.NET.place(node.place).type))
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfGuard (self, node) :
        self.fill("if %s {" % node.guard.source)
        self.children_visit(node.body, True)
        self.fill("}")
    def visit_IfType (self, node) :
        if node.place.type is None :
            self.children_visit(node.body, False)
        elif node.place.type.endswith("()") :
            self.fill("if %s(%s) {" % (node.place.type[:-2], node.token.source))
            self.children_visit(node.body, True)
            self.fill("}")
        elif isinstance(node.LABEL, arcs.Expression) :
            self.children_visit(node.body, False)
        else :
            self.fill("%s = %s" % (node.ASSIGN[node.token.source][0],
                                   node.token.source))
            self.children_visit(node.body, False)
    def _newmarking (self, name, marking, assign) :
        self.fill("%s := snk.Marking{}" % name)
        for place, tokens in marking.items() :
            self.fill("%s.Set(%s" % (name, S(place)))
            for tok in tokens :
                if tok.source in assign :
                    src = assign[tok.source][0]
                else :
                    src = tok.source
                self.write(", %s" % src)
            self.write(")")
    def visit_AddSuccIfEnoughTokens (self, node) :
        subvar = node.NAMES.fresh(base="sub", add=True)
        self._newmarking(subvar, node.sub, node.ASSIGN)
        self.fill("if %s.Geq(%s) {" % (node.old, subvar))
        with self.indent() :
            addvar = node.NAMES.fresh(base="add", add=True)
            self._newmarking(addvar, node.add, node.ASSIGN)
            self.fill("%s.Add(%s.Copy().Sub(%s).Add(%s))"
                      % (node.succ, node.old, subvar, addvar))
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
            for place in node.marking :
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
            for trans, name in self.succproc.items() :
                self.fill("%s: %s," % (S(trans or ""), name))
        self.fill("}\n")
    def visit_SuccFuncTable (self, node) :
        self.fill("// map transitions names to successor funcs")
        self.fill('// "" maps to all-transitions func')
        self.fill("type SuccFuncType func(snk.Marking)snk.Set")
        self.fill("var SuccFunc map[string]SuccFuncType = map[string]SuccFuncType{")
        with self.indent() :
            for trans, name in self.succfunc.items() :
                self.fill("%s: %s," % (S(trans or ""), name))
        self.fill("}\n")

if __name__ == "__main__" :
    import io
    from snakes.io.snk import load
    net = load(open("test/simple-go.snk"))
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
