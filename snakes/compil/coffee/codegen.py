from snakes.compil import ast, CompilationError

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        self.exports = {}
        libpath = self.options.get("libpath", ".")
        self.write("# %s\n" % self.timestamp())
        self.fill("main = require '%s/main'" % libpath)
        self.fill("{eq} = require '%s/dicts'" % libpath)
        self.fill("{Mset} = require '%s/multisets'" % libpath)
        self.fill("{Marking, dot} = require '%s/markings'" % libpath)
        self.fill("{Set} = require '%s/sets'" % libpath)
        self.fill("\nNET = %r" % node.name)
        self.exports["NET"] = "NET"
        self.children_visit(node.body)
        self.exports["run"] = ("() -> main.main(%r, %s, %s, %s)"
                               % (node.name, self.initfunc, self.succproc[""],
                                  self.succiter[""]))
        self.exports["init"] = self.initfunc
        self.fill("module.exports =")
        with self.indent() :
            for exp in sorted(self.exports.items()) :
                self.fill("%r: %s" % exp)
        if self.options.get("main", False) :
            self.fill()
            self.fill("module.exports.run()")
    def visit_DefineMarking (self, node) :
        pass
    def visit_DefSuccProc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write(" = (%s, %s) ->" % (node.marking, node.succ))
        with self.indent() :
            if node.name.trans :
                self.fill("# successors of %r" % node.name.trans)
            else :
                self.fill("# successors for all transitions")
        self.children_visit(node.body, True)
        self.write("\n")
    def visit_Declare (self, node) :
        pass
    def visit_Assign (self, node) :
        self.fill("%s = " % node.variable)
        self.visit(node.expr)
    def visit_AssignItem (self, node) :
        self.fill("%s = %s" % (node.variable, node.container))
        for p in node.path :
            self.write("[%s]" % p)
    def visit_IfInput (self, node) :
        self.fill("if not (%s)" % " or ".join("%s.empty(%r)" % (node.marking, p.name)
                                              for p in node.places))
        self.children_visit(node.body, True)
    def visit_IfToken (self, node) :
        self.fill("if %s.get(%r).count(%s) > 0"
                  % (node.marking, node.place.name, node.token))
        self.children_visit(node.body, True)
    def visit_IfNoToken (self, node) :
        self.fill("if %s.get(%r).count(%s) == 0"
                  % (node.marking, node.place.name, node.token))
        self.children_visit(node.body, True)
    def visit_IfNoTokenSuchThat (self, node) :
        self.fill("if not (")
        self.visit(node.guard)
        self.write(" for %s from %s.get(%r).iter())"
                   % (node.variable, node.marking, node.place.name))
        self.write(".reduce((a, b) -> a or b)")
        self.children_visit(node.body, True)
    def visit_IfPlace (self, node) :
        self.fill("if %s.eq(%s.get(%r))"
                  % (node.variable, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_IfAllType (self, node) :
        if node.place.type :
            var = node.CTX.names.fresh()
            self.fill("if (%s instanceof %s for %s from %s.iter())"
                      % (var, node.place.type, var, node.variable))
            self.write(".reduce((a, b) -> a and b)")
            self.children_visit(node.body, True)
        else :
            self.children_visit(node.body, False)
    def visit_GetPlace (self, node) :
        self.fill("%s = %s.get(%r)" % (node.variable, node.marking, node.place.name))
    def visit_ForeachToken (self, node) :
        self.fill("for %s in %s.get(%r).iter()"
                  % (node.variable, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_Break (self, node) :
        self.fill("break")
    def visit_Expr (self, node) :
        self.write(node.source)
    def visit_TrueConst (self, node) :
        self.write("true")
    def visit_FalseConst (self, node) :
        self.write("false")
    def visit_And (self, node) :
        for i, item in enumerate(node.items) :
            if i > 0 :
                self.write(" and ")
            self.visit(item)
    def visit_Eq (self, node) :
        self.write("eq(")
        self.visit(node.left)
        self.write(", ")
        self.visit(node.right)
        self.write(")")
    def visit_If (self, node) :
        self.fill("if ")
        self.visit(node.guard)
        self.children_visit(node.body, True)
    def _matchtype (self, var, typ) :
        if typ is None :
            pass
        elif isinstance(typ, tuple) :
            yield True, "%s instanceof Array" % var
            yield True, "%s.length == %s" % (var, len(typ))
            for i, sub in enumerate(typ) :
                for cond in self._matchtype("%s[%s]" % (var, i), sub) :
                    yield cond
        elif typ.endswith("()") :
            yield False, "%s(%s)" % (typ[:-2], var)
        else :
            yield False, "%s instanceof %s" % (var, typ)
    def visit_IfType (self, node) :
        match = list(c[1] for c in self._matchtype(node.token, node.place.type))
        if not match :
            self.children_visit(node.body, False)
        else :
            self.fill("if %s" % " and ".join(match))
            self.children_visit(node.body, True)
    def visit_IfTuple (self, node) :
        match = list(c[1] for c in self._matchtype(node.token, node.place.type)
                     if c[0])
        if not match :
            self.children_visit(node.body, False)
        else :
            self.fill("if %s" % " and ".join(match))
            self.children_visit(node.body, True)
    def _pattern (self, nest) :
        return "[%s]" % ", ".join(self._pattern(n) if isinstance(n, tuple) else n
                                  for n in nest)
    def _marking (self, var, marking, blame) :
        self.fill("%s = new Marking()" % var)
        whole = []
        for i, (place, tokens) in enumerate(marking.items()) :
            self.fill("%s.set(%r, " % (var, place))
            first = True
            for tok in tokens :
                if isinstance(tok, tuple) :
                    if tok[0] == "mset" :
                        whole.append((place, tok[1]))
                    else :
                        raise CompilationError("unsupported type '%s(%s)'" % tok,
                                               blame)
                else :
                    if not first :
                        self.write(", ")
                    first = False
                    if isinstance(tok, ast.Pattern) :
                        self.write(self._pattern(tok.matcher))
                    else :
                        self.write(tok)
            self.write(")")
        for place, tokens in whole :
            self.fill("%s.get(%r).update(%s)" % (var, place, tokens))
    def visit_IfEnoughTokens (self, node) :
        if not hasattr(node.CTX, "subvar") :
            node.CTX.subvar = node.NAMES.fresh(base="sub")
        if not hasattr(node.CTX, "addvar") :
            node.CTX.addvar = node.NAMES.fresh(base="add")
        subtest = False
        if node.test :
            if not hasattr(node.CTX, "testvar") :
                node.CTX.testvar = node.NAMES.fresh(base="test", add=True)
            self._marking(node.CTX.testvar, node.test, node.BLAME)
            self.fill("if %s.get(%s)" % (node.old, node.CTX.testvar))
            indent = 1
        elif node.sub :
            subtest = True
            self._marking(node.CTX.subvar, node.sub, node.BLAME)
            self.fill("if %s.geq(%s)" % (node.old, node.CTX.subvar))
            indent = 1
        else :
            indent = 0
        with self.indent(indent) :
            if node.sub and not subtest :
                self._marking(node.CTX.subvar, node.sub, node.BLAME)
            if node.add :
                self._marking(node.CTX.addvar, node.add, node.BLAME)
            self.children_visit(node.body, False)
    def visit_AddSucc (self, node) :
        if node.sub and node.add :
            self.fill("%s.add(%s.copy().sub(%s).add(%s))"
                      % (node.succ, node.old, node.CTX.subvar, node.CTX.addvar))
        elif node.sub :
            self.fill("%s.add(%s.copy().sub(%s))"
                      % (node.succ, node.old, node.CTX.subvar))
        elif node.add :
            self.fill("%s.add(%s.copy().add(%s))"
                      % (node.succ, node.old, node.CTX.addvar))
        else :
            self.fill("%s.add(%s.copy())" % (node.succ, node.old))
    def visit_YieldEvent (self, node) :
        mvar = node.NAMES.fresh(base="mode")
        self.fill("%s = {" % mvar)
        for i, v in enumerate(node.CTX.trans.vars()) :
            if i > 0 :
                self.write(", ")
            self.write("%r: %s" % (v, node.CTX.bound[v]))
        self.write("}")
        if node.sub and node.add :
            self.fill("yield [%r, %s, %s, %s]"
                      % (node.CTX.trans.name, mvar, node.CTX.subvar, node.CTX.addvar))
        elif node.sub :
            self.fill("yield [%r, %s, %s, new Marking()]"
                      % (node.CTX.trans.name, mvar, node.CTX.subvar))
        elif node.add :
            self.fill("yield [%r, %s, ne Marking(), %s]"
                      % (node.CTX.trans.name, mvar, node.CTX.addvar))
        else :
            self.fill("yield [%r, %s, new Marking(), new Marking()]"
                      % (node.CTX.trans.name, mvar))
    def visit_DefSuccIter (self, node) :
        self.fill()
        self.visit(node.name)
        self.write(" = (%s) ->" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill("# successors of %r" % node.name.trans)
                self.children_visit(node.body, False)
            else :
                self.fill("# successors for all transitions")
                for name in node.body :
                    self.fill("for event from ")
                    self.visit(name)
                    self.write("(%s)" % node.marking)
                    with self.indent() :
                        self.fill("yield event")
        self.write("\n")
    def visit_DefSuccFunc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write(" = (%s) ->" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill("# successors of %r" % node.name.trans)
            else :
                self.fill("# successors for all transitions")
        self.children_visit(node.body, True)
        self.write("\n")
    def visit_InitSucc (self, node) :
        self.fill("%s = new Set()" % node.name)
    def visit_CallSuccProc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write("(%s, %s)" % (node.marking, node.succ))
    def visit_ReturnSucc (self, node) :
        self.fill("return %s" % node.name)
    def visit_DefInitFunc (self, node) :
        var = "$__$"
        self.fill()
        self.visit(node.name)
        self.write(" = ->")
        with self.indent() :
            self.fill("# initial marking")
            self.fill("%s = new Marking()" % var)
            for i, place in enumerate(node.marking) :
                self.fill("%s.set(" % var)
                self.visit(place)
                self.write(")")
            self.fill("return %s" % var)
        self.write("\n")
    def visit_PlaceMarking (self, node) :
        self.write("%r, " % node.place)
        self.write(", ".join(tok.source for tok in node.tokens))
    def visit_SuccProcTable (self, node) :
        self.exports["succproc"] = "succproc"
        self.fill("# map transitions names to successor procs")
        self.fill("# '' maps to all-transitions proc")
        self.fill("succproc =")
        with self.indent() :
            for trans, name in sorted(self.succproc.items()) :
                self.fill("%r: %s" % (trans, name))
        self.write("\n")
    def visit_SuccFuncTable (self, node) :
        self.exports["succfunc"] = "succfunc"
        self.fill("# map transitions names to successor funcs")
        self.fill("# '' maps to all-transitions func")
        self.fill("succfunc =")
        with self.indent() :
            for trans, name in sorted(self.succfunc.items()) :
                self.fill("%r: %s" % (trans, name))
        self.write("\n")
    def visit_SuccIterTable (self, node) :
        self.exports["succiter"] = "succiter"
        self.fill("# map transitions names to successor iterators")
        self.fill("# '' maps to all-transitions iterator")
        self.fill("succiter =")
        with self.indent() :
            for trans, name in sorted(self.succiter.items()) :
                self.fill("%r: %s" % (trans, name))
        self.write("\n")

if __name__ == "__main__" :
    import io, sys
    from snakes.io.snk import load
    net = load(open(sys.argv[-1]))
    gen = CodeGenerator(io.StringIO(), libpath="./libs/js", main=True)
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
