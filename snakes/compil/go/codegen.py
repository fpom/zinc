import re
from operator import attrgetter

from snakes.compil import ast
from snakes import TypingError

def S (text) :
    return '"%s"' % text.replace('"', '\\"')

preamble = """// %(timestamp)s
package %(package)s
"""

closing = """
func main () {
    snk.Main(NET, Init, AddSucc, IterSucc)
}
"""

_letter = re.compile("\W+")

class CodeGenerator (ast.CodeGenerator) :
    def visit_Context (self, node) :
        node.decl('import "snk"', "import")
        node.decl("type Token struct {}")
        node.decl("var DOT Token = Token{}")
        node.decl("var NET string = %s\n" % S(node.NET.name))
        ast.CodeGenerator.visit_Context(self, node)
    def visit_Module (self, node) :
        self.write(preamble % {"timestamp" : self.timestamp(),
                               "package" : node.name})
        self.children_visit(node.body)
        self.fill(closing)
    def _tupledef (self, typ) :
        return "_".join([""] + [_letter.sub("", self.typedef[t]) for t in typ] + [""])
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
            name = self.typedef[typ] = self._tupledef(typ)
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
    def visit_SuccIterName (self, node) :
        if not node.trans :
            name = "IterSucc"
        elif node.trans not in self.succiter :
            name = "IterSucc%03u" % (len(self.succiter) + 1)
        else :
            name = self.succiter[node.trans]
        self.succiter[node.trans] = name
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
            self.children_visit(node.body, False)
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
        bvar = node.CTX.names.fresh(base="b" + node.variable)
        pvar = node.CTX.names.fresh(base="p" + node.variable)
        ivar = node.CTX.names.fresh(base="i" + node.variable)
        self.fill("%s := true" % bvar)
        self.fill("for %s, %s := %s.Iter(%s); %s != nil; %s = %s.Next() {"
                  % (ivar, pvar, node.marking, S(node.place.name), pvar, pvar, ivar))
        with self.indent() :
            self.fill("%s = (*%s).(%s)"
                      % (node.variable, pvar, self.typedef[node.place.type]))
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
        ivar = node.NAMES.fresh(base="i" + node.variable)
        pvar = node.NAMES.fresh(base="p" + node.variable)
        self.fill("for %s, %s := %s.Iter(%s); %s != nil; %s = %s.Next() {"
                  % (ivar, pvar, node.marking, S(node.place.name), pvar, pvar, ivar))
        with self.indent() :
            self.fill("%s = (*%s).(%s)"
                      % (node.variable, pvar, self.typedef[node.place.type]))
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
            bvar = node.CTX.names.fresh(base="b" + node.variable)
            ivar = node.CTX.names.fresh(base="i" + node.variable)
            pvar = node.CTX.names.fresh(base="p" + node.variable)
            self.fill("%s := true" % bvar)
            self.fill("for %s, %s := %s.Iter(); %s != nil; %s = %s.Next() {"
                      % (ivar, pvar, node.variable, pvar, pvar, ivar))
            with self.indent() :
                self.fill("_, %s = (*%s).(%s)"
                          % (bvar, pvar, self.typedef[node.place.type]))
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
        self.fill("%s := snk.MakeMarking()" % name)
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
    def visit_IfEnoughTokens (self, node) :
        subtest = False
        if not hasattr(node.CTX, "subvar") :
            node.CTX.subvar = node.NAMES.fresh(base="sub")
        if not hasattr(node.CTX, "addvar") :
            node.CTX.addvar = node.NAMES.fresh(base="add")
        if node.test :
            if not hasattr(node.CTX, "testvar") :
                node.CTX.testvar = node.NAMES.fresh(base="test")
            self._newmarking(node.CTX.testvar, node.test, node.BOUND)
            self.fill("if %s.Geq(%s) {" % (node.old, node.CTX.testvar))
            indent = 1
        elif node.sub :
            subtest = 1
            self._newmarking(node.CTX.subvar, node.sub, node.BOUND)
            self.fill("if %s.Geq(%s) {" % (node.old, node.CTX.subvar))
            indent = 1
        else :
            indent = 0
        with self.indent(indent) :
            if node.sub and not subtest :
                self._newmarking(node.CTX.subvar, node.sub, node.BOUND)
            if node.add :
                self._newmarking(node.CTX.addvar, node.add, node.BOUND)
            self.children_visit(node.body, False)
        if indent :
            self.fill("}")
    def visit_AddSucc (self, node) :
        if node.sub and node.add :
            self.fill("%s.Add(%s.Copy().Sub(%s).Add(%s))"
                      % (node.succ, node.old, node.CTX.subvar, node.CTX.addvar))
        elif node.sub :
            self.fill("%s.Add(%s.Copy().Sub(%s))"
                      % (node.succ, node.old, node.CTX.subvar))
        elif node.add :
            self.fill("%s.Add(%s.Copy().Add(%s))"
                      % (node.succ, node.old, node.CTX.addvar))
        else :
            self.fill("%s.Add(%s.Copy())"  % (node.succ, node.old))
    def visit_YieldEvent (self, node) :
        mvar = node.NAMES.fresh(base="mode")
        self.fill("%s := snk.Binding{" % mvar)
        tvars = node.CTX.trans.vars()
        last = len(tvars) - 1
        for i, v in enumerate(tvars) :
            self.write("%s: %s" % (S(v), node.CTX.bound[v]))
            if i < last :
                self.write(", ")
        self.write("}")
        if node.sub and node.add :
            self.fill("if ! %s.Put(&snk.Event{%s, %s, %s, %s}) { return }"
                      % (node.CTX.iterator, S(node.CTX.trans.name), mvar,
                         node.CTX.subvar, node.CTX.addvar))
        elif node.sub :
            self.fill("if ! %s.Put(&snk.Event{%s, %s, %s, snk.MakeMarking()})"
                      " { return }" % (node.CTX.iterator, S(node.CTX.trans.name),
                                       mvar, node.CTX.subvar))
        elif node.add :
            self.fill("if ! %s.Put(&snk.Event{%s, %s, snk.MakeMarking(), %s})"
                      " { return }" % (node.CTX.iterator, S(node.CTX.trans.name),
                                       mvar, node.CTX.addvar))
        else :
            self.fill("if ! %s.Put(&snk.Event{%s, %s,"
                      " snk.MakeMarking(), snk.MakeMarking()}) { return }"
                      % (node.CTX.iterator, mvar, S(node.CTX.trans.name)))
    def visit_DefSuccIter (self, node) :
        self.unused = set()
        self.fill("func ")
        self.visit(node.name)
        if node.name.trans :
            node.CTX.iterator = node.NAMES.fresh(base="it")
        else :
            node.CTX.iterator = "it"
        self.write(" (%s snk.Marking, %s snk.SuccIterator) {"
                   % (node.marking, node.CTX.iterator))
        with self.indent() :
            if node.name.trans :
                self.fill("// successors for transition %r" % node.name.trans)
                self.children_visit(node.body, False)
            else :
                self.fill("// successors for all transitions")
                for name in node.body :
                    self.fill("for i, p := snk.Iter(")
                    self.visit(name)
                    self.write(", %s); p != nil; p = i.Next() {" % node.marking)
                    with self.indent() :
                        self.fill("if ! %s.Put(p) { return }" % node.CTX.iterator)
                    self.fill("}")
            self.fill("%s.Put(nil)" % node.CTX.iterator)
            if self.unused :
                self.fill("// work around 'declared and not used' compilation error")
                self.fill("// variables are kept to be typechecked by the compiler")
                self.fill("return")
                for var in self.unused :
                    self.fill("_ = %s" % var)
        self.fill("}\n")
    def visit_DefSuccFunc (self, node) :
        self.fill("func ")
        self.visit(node.name)
        self.write(" (%s snk.Marking) snk.Set {" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill("// successors of %r" % node.name.trans)
            else :
                self.fill("// successors for all transitions")
            self.children_visit(node.body, False)
        self.fill("}\n")
    def visit_InitSucc (self, node) :
        self.fill("%s := snk.MakeSet()" % node.name)
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
            self.fill("init := snk.MakeMarking(0)")
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
    def visit_SuccIterTable (self, node) :
        self.fill("// map transitions names to successor iterators")
        self.fill('// "" maps to all-transitions iterator')
        self.fill("var SuccIter map[string]snk.SuccIterFunc"
                  " = map[string]snk.SuccIterFunc{")
        with self.indent() :
            for trans, name in sorted(self.succiter.items()) :
                self.fill("%s: %s," % (S(trans or ""), name))
        self.fill("}\n")

if __name__ == "__main__" :
    import io, sys
    from snakes.io.snk import load
    net = load(open(sys.argv[-1]))
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__("main"))
    print(gen.output.getvalue().rstrip())
