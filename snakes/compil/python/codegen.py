import inspect
from snakes.compil import ast, CompilationError

##
## to be included in the generated source code
##

def statespace () :
    "compute the marking graph"
    todo = set([init()])
    done = set()
    succ = set()
    g = {}
    while todo:
        state = todo.pop()
        done.add(state)
        addsucc(state, succ)
        if state not in g :
            g[state] = set()
        g[state].update(succ)
        succ.difference_update(done)
        succ.difference_update(todo)
        todo.update(succ)
        succ.clear()
    return g

def reachable (g=None):
    "compute all the reachable markings"
    if g is None :
        g = statespace()
    return set(g)

def deadlocks (g=None) :
    "compute the set of deadlocks"
    if g is None :
        g = statespace()
    return set(m for m, s in g.items() if not s)

def main () :
    import argparse
    def dump (m) :
        return repr({p : list(t) for p, t in m.items()})
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", dest="size",
                        default=False, action="store_true",
                        help="only print size")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", dest="mode", action="store_const", const="g",
                       help="print full marking graph")
    group.add_argument("-m", dest="mode", action="store_const", const="m",
                       help="only print markings")
    group.add_argument("-d", "--dead", dest="mode", action="store_const", const="d",
                       help="only print deadlocks")
    args = parser.parse_args()
    g = statespace()
    if args.mode in "gm" and args.size :
        print("%s reachable states" % len(g))
    elif args.mode == "d" and args.size :
        print("%s deadlocks" % len(deadlocks(g)))
    elif args.mode == "g" :
        print("INIT ", dump(init()))
        for num, (state, succ) in enumerate(g.items()) :
            print("[%s]" % num, dump(state))
            for s in succ :
                print(">>>", dump(s))
    else :
        print("INIT ", dump(init()))
        if args.mode == "m" :
            get = reachable
        else :
            get = deadlocks
        for num, state in enumerate(get(g)) :
            print("[%s]" % num, dump(state))

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        self.write("# %s\n\nNET = %r\n" % (self.timestamp(), node.name))
        self.children_visit(node.body)
        self.write("\n%s" % inspect.getsource(statespace))
        self.write("\n%s" % inspect.getsource(reachable))
        self.write("\n%s" % inspect.getsource(deadlocks))
        self.write("\n%s" % inspect.getsource(main))
        self.write("\nif __name__ == '__main__':"
                   "\n    main()")
    def visit_DefineMarking (self, node) :
        self.fill("from snakes.nets import Marking, mset, dot\n")
    def visit_DefSuccProc (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" (%s, %s):" % (node.marking, node.succ))
        with self.indent() :
            if node.name.trans :
                self.fill(repr("successors of %r" % node.name.trans))
            else :
                self.fill(repr("successors for all transitions"))
        self.children_visit(node.body, True)
        self.write("\n")
    def visit_Declare (self, node) :
        pass
    def visit_Assign (self, node) :
        self.fill("%s = " % node.variable)
        self.visit(node.expr)
    def visit_IfInput (self, node) :
        self.fill("if %s:" % " and ".join("%s(%r)" % (node.marking, p.name)
                                          for p in node.places))
        self.children_visit(node.body, True)
    def visit_IfToken (self, node) :
        self.fill("if %s in %s(%r):" % (node.token, node.marking, node.place))
        self.children_visit(node.body, True)
    def visit_IfNoToken (self, node) :
        self.fill("if %s not in %s(%r):" % (node.token, node.marking, node.place))
        self.children_visit(node.body, True)
    def visit_IfNoTokenSuchThat (self, node) :
        self.fill("if not any(%s for %s in %s(%r)):"
                  % (node.guard, node.variable, node.marking, node.place))
        self.children_visit(node.body, True)
    def visit_IfPlace (self, node) :
        self.fill("if %s == %s(%r):" % (node.variable, node.marking, node.place))
        self.children_visit(node.body, True)
    def visit_IfAllType (self, node) :
        if node.place.type :
            var = node.CTX.names.fresh()
            self.fill("if all(isinstance(%s, %s) for %s in %s):"
                      % (var, node.place.type, var, node.variable))
            self.children_visit(node.body, True)
        else :
            self.children_visit(node.body, False)
    def visit_GetPlace (self, node) :
        self.fill("%s = %s(%r)" % (node.variable, node.marking, node.place))
    def visit_ForeachToken (self, node) :
        if isinstance(node.variable, ast.Pattern) :
            self.fill("for %s in %s(%r):" % (self._pattern(node.variable.matcher),
                                             node.marking, node.place))
        else :
            self.fill("for %s in %s(%r):" % (node.variable, node.marking, node.place))
        self.children_visit(node.body, True)
    def visit_Expr (self, node) :
        self.write(node.source)
    def visit_And (self, node) :
        for i, item in enumerate(node.items) :
            if i > 0 :
                self.write(" and ")
            self.visit(item)
    def visit_Eq (self, node) :
        self.write("(")
        self.visit(node.left)
        self.write(") == (")
        self.visit(node.right)
        self.write(")")
    def visit_IfGuard (self, node) :
        if isinstance(node.guard, ast.AST) :
            self.fill("if ")
            self.visit(node.guard)
            self.write(":")
        else :
            self.fill("if %s:" % node.guard)
        self.children_visit(node.body, True)
    def _matchtype (self, var, typ) :
        if typ is None :
            pass
        elif isinstance(typ, tuple) :
            yield "isinstance(%s, tuple)" % var
            yield "len(%s) == %s" % (var, len(typ))
            for i, sub in enumerate(typ) :
                for cond in self._matchtype("%s[%s]" % (var, i), sub) :
                    yield cond
        elif typ.endswith("()") :
            yield "%s(%s)" % (typ[:-2], var)
        else :
            yield "isinstance(%s, %s)" % (var, typ)
    def visit_IfType (self, node) :
        if isinstance(node.token, str) :
            var = node.token
        else :
            var = node.token.source
        match = list(self._matchtype(var, node.place.type))
        if not match :
            self.children_visit(node.body, False)
        else :
            self.fill("if %s:" % " and ".join(match))
            self.children_visit(node.body, True)
    def _pattern (self, nest) :
        return "(%s)" % ", ".join(self._pattern(n) if isinstance(n, tuple) else n
                                  for n in nest)
    def _marking (self, var, marking, blame) :
        self.fill("%s = Marking({" % var)
        whole = {}
        for i, (place, tokens) in enumerate(marking.items()) :
            if i > 0 :
                self.write(", ")
            self.write("%r: mset([" % place)
            first = True
            for tok in tokens :
                if isinstance(tok, tuple) :
                    if tok[0] == "mset" :
                        whole[place] = tok[1]
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
            self.write("])")
        self.write("})")
        for place, tokens in whole.items() :
            self.fill("%s[%r].update(%s)" % (var, place, tokens))
    def visit_AddSuccIfEnoughTokens (self, node) :
        subvar = node.NAMES.fresh(base="sub", add=True)
        addvar = node.NAMES.fresh(base="add", add=True)
        subtest = False
        if node.test :
            testvar = node.NAMES.fresh(base="test", add=True)
            self._marking(testvar, node.test, node.BLAME)
            self.fill("if %s <= %s:" % (testvar, node.old))
            indent = 1
        elif node.sub :
            subtest = True
            self._marking(subvar, node.sub, node.BLAME)
            self.fill("if %s <= %s:" % (subvar, node.old))
            indent = 1
        else :
            indent = 0
        with self.indent(indent) :
            if node.sub and not subtest :
                self._marking(subvar, node.sub, node.BLAME)
            if node.add :
                self._marking(addvar, node.add, node.BLAME)
            if node.sub and node.add :
                self.fill("%s.add(%s - %s + %s)" % (node.succ, node.old, subvar,
                                                    addvar))
            elif node.sub :
                self.fill("%s.add(%s - %s)" % (node.succ, node.old, subvar))
            elif node.add :
                self.fill("%s.add(%s + %s)" % (node.succ, node.old, addvar))
            else :
                self.fill("%s.add(%s.copy())" % (node.succ, node.old))
    def visit_DefSuccFunc (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" (%s):" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill(repr("successors of %r" % node.name.trans))
            else :
                self.fill(repr("successors for all transitions"))
        self.children_visit(node.body, True)
        self.write("\n")
    def visit_InitSucc (self, node) :
        self.fill("%s = set()" % node.name)
    def visit_CallSuccProc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write("(%s, %s)" % (node.marking, node.succ))
    def visit_ReturnSucc (self, node) :
        self.fill("return %s" % node.name)
    def visit_DefInitFunc (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" ():")
        with self.indent() :
            self.fill(repr("initial marking"))
            self.fill("return Marking({")
            for i, place in enumerate(node.marking) :
                if i > 0 :
                    self.write(", ")
                self.visit(place)
        self.write("})\n")
    def visit_PlaceMarking (self, node) :
        self.write("%r: mset([" % node.place)
        for i, tok in enumerate(node.tokens) :
            if i > 0 :
                self.write(", %s" % tok.source)
            else :
                self.write(tok.source)
        self.write("])")
    def visit_SuccProcTable (self, node) :
        self.fill("# map transitions names to successor procs")
        self.fill("# None maps to all-transitions proc")
        self.fill("succproc = {")
        for i, (trans, name) in enumerate(self.succproc.items()) :
            if i == 0 == len(self.succproc) - 1 :
                self.write("%r: %s}" % (trans, name))
            elif i == 0 :
                self.write("%r: %s," % (trans, name))
            elif i == len(self.succproc) - 1 :
                self.fill("            %r: %s}" % (trans, name))
            else :
                self.fill("            %r: %s," % (trans, name))
        self.write("\n")
    def visit_SuccFuncTable (self, node) :
        self.fill("# map transitions names to successor funcs")
        self.fill("# None maps to all-transitions func")
        self.fill("succfunc = {")
        for i, (trans, name) in enumerate(self.succfunc.items()) :
            if i == 0 == len(self.succfunc) - 1 :
                self.write("%r: %s}" % (trans, name))
            elif i == 0 :
                self.write("%r: %s," % (trans, name))
            elif i == len(self.succfunc) - 1 :
                self.fill("            %r: %s}" % (trans, name))
            else :
                self.fill("            %r: %s," % (trans, name))
        self.write("\n")

if __name__ == "__main__" :
    import io, sys
    from snakes.io.snk import load
    net = load(open(sys.argv[-1]))
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
