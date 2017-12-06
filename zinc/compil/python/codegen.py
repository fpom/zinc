import inspect, collections
from zinc.compil import ast, CompilationError

##
## to be included in the generated source code
##

event = init = addsucc = itersucc = None

def dumpmarking (m) :
    if hasattr(m, "ident") :
        return "[%s] %s" % (m.ident, {p : list(t) for p, t in m.items()})
    else :
        return str({p : list(t) for p, t in m.items()})

def statespace (print_states, print_succs, print_dead) :
    i = init()
    i.ident = 0
    todo = collections.deque([i])
    seen = {i : 0}
    dead = 0
    while todo:
        state = todo.popleft()
        succ = set()
        addsucc(state, succ)
        if not succ :
            dead += 1
        if (print_dead and not succ) or print_states :
            print(dumpmarking(state))
        for s in succ :
            if s in seen :
                s.ident = seen[s]
            else :
                s.ident = seen[s] = len(seen)
                todo.append(s)
            if print_succs :
                print(" >", dumpmarking(s))
    return len(seen), dead

def lts () :
    i = init()
    i.ident = 0
    todo = collections.deque([i])
    seen = {i : 0}
    while todo:
        state = todo.popleft()
        print(dumpmarking(state))
        for trans, mode, sub, add in itersucc(state) :
            succ = state - sub + add
            if succ in seen :
                succ.ident = seen[succ]
            else :
                succ.ident = seen[succ] = len(seen)
                todo.append(succ)
            print("@ %s = %s" % (trans, mode))
            print(" -", dumpmarking(sub))
            print(" +", dumpmarking(add))
            print(" >", dumpmarking(succ))

def main () :
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", dest="size",
                        default=False, action="store_true",
                        help="only print size")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", dest="mode", action="store_const", const="g",
                       help="print marking graph")
    group.add_argument("-l", dest="mode", action="store_const", const="l",
                       help="print LTS (detailled marking graph)")
    group.add_argument("-m", dest="mode", action="store_const", const="m",
                       help="only print markings")
    group.add_argument("-d", dest="mode", action="store_const", const="d",
                       help="only print deadlocks")
    args = parser.parse_args()
    if args.mode in "gml" and args.size :
        n, _ = statespace(False, False, False)
        print("%s reachable states" % n)
    elif args.mode == "d" and args.size :
        _, n = statespace(False, False, False)
        print("%s deadlocks" % n)
    elif args.mode == "g" :
        statespace(True, True, False)
    elif args.mode in "m" :
        statespace(True, False, False)
    elif args.mode in "d" :
        statespace(False, False, True)
    elif args.mode == "l" :
        lts()

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        self.write("# %s\n\nNET = %r\n" % (self.timestamp(), node.name))
        self.write("import itertools, collections")
        self.children_visit(node.body)
        self.write("\n%s" % inspect.getsource(dumpmarking))
        self.write("\n%s" % inspect.getsource(statespace))
        self.write("\n%s" % inspect.getsource(lts))
        self.write("\n%s" % inspect.getsource(main))
        self.write("\nif __name__ == '__main__':"
                   "\n    main()\n")
    def visit_DefineMarking (self, node) :
        self.fill("from zinc.nets import Marking, mset, dot, hdict")
        self.fill("event = collections.namedtuple('event', "
                  "['trans', 'mode', 'sub', 'add'])\n")
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
    def visit_AssignItem (self, node) :
        self.fill("%s = %s" % (node.variable, node.container))
        for p in node.path :
            self.write("[%s]" % p)
    def visit_IfInput (self, node) :
        self.fill("if %s:" % " and ".join("%s(%r)" % (node.marking, p.name)
                                          for p in node.places))
        self.children_visit(node.body, True)
    def visit_IfToken (self, node) :
        self.fill("if %s in %s(%r):" % (node.token, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_IfNoToken (self, node) :
        self.fill("if %s not in %s(%r):" % (node.token, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_IfNoTokenSuchThat (self, node) :
        self.fill("if not any(")
        self.visit(node.guard)
        self.write(" for %s in %s(%r)):"
                   % (node.variable, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_IfPlace (self, node) :
        self.fill("if %s == %s(%r):" % (node.variable, node.marking, node.place.name))
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
        self.fill("%s = %s(%r)" % (node.variable, node.marking, node.place.name))
    def visit_ForeachToken (self, node) :
        self.fill("for %s in %s(%r):" % (node.variable, node.marking, node.place.name))
        self.children_visit(node.body, True)
    def visit_Break (self, node) :
        self.fill("break")
    def visit_Expr (self, node) :
        self.write(node.source)
    def visit_TrueConst (self, node) :
        self.write("True")
    def visit_FalseConst (self, node) :
        self.write("False")
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
    def visit_If (self, node) :
        self.fill("if ")
        self.visit(node.guard)
        self.write(":")
        self.children_visit(node.body, True)
    def _matchtype (self, var, typ) :
        if typ is None :
            pass
        elif isinstance(typ, tuple) :
            yield True, "isinstance(%s, tuple)" % var
            yield True, "len(%s) == %s" % (var, len(typ))
            for i, sub in enumerate(typ) :
                for cond in self._matchtype("%s[%s]" % (var, i), sub) :
                    yield cond
        elif typ.endswith("()") :
            yield False, "%s(%s)" % (typ[:-2], var)
        else :
            yield False, "isinstance(%s, %s)" % (var, typ)
    def visit_IfType (self, node) :
        match = list(c[1] for c in self._matchtype(node.token, node.place.type))
        if not match :
            self.children_visit(node.body, False)
        else :
            self.fill("if %s:" % " and ".join(match))
            self.children_visit(node.body, True)
    def visit_IfTuple (self, node) :
        match = list(c[1] for c in self._matchtype(node.token, node.place.type)
                     if c[0])
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
        whole = []
        for i, (place, tokens) in enumerate(marking.items()) :
            if i > 0 :
                self.write(", ")
            self.write("%r: mset([" % place)
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
            self.write("])")
        self.write("})")
        for place, tokens in whole :
            self.fill("%s[%r].update(%s)" % (var, place, tokens))
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
            self.fill("if %s <= %s:" % (node.CTX.testvar, node.old))
            indent = 1
        elif node.sub :
            subtest = True
            self._marking(node.CTX.subvar, node.sub, node.BLAME)
            self.fill("if %s <= %s:" % (node.CTX.subvar, node.old))
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
            self.fill("%s.add(%s - %s + %s)" % (node.succ, node.old,
                                                node.CTX.subvar,
                                                node.CTX.addvar))
        elif node.sub :
            self.fill("%s.add(%s - %s)" % (node.succ, node.old, node.CTX.subvar))
        elif node.add :
            self.fill("%s.add(%s + %s)" % (node.succ, node.old, node.CTX.addvar))
        else :
            self.fill("%s.add(%s.copy())" % (node.succ, node.old))
    def visit_YieldEvent (self, node) :
        mvar = node.NAMES.fresh(base="mode")
        self.fill("%s = hdict({" % mvar)
        for i, v in enumerate(node.CTX.trans.vars()) :
            if i > 0 :
                self.write(", ")
            self.write("%r: %s" % (v, node.CTX.bound[v]))
        self.write("})")
        if node.sub and node.add :
            self.fill("yield event(%r, %s, %s, %s)"
                      % (node.CTX.trans.name, mvar, node.CTX.subvar, node.CTX.addvar))
        elif node.sub :
            self.fill("yield event(%r, %s, %s, Marking())"
                      % (node.CTX.trans.name, mvar, node.CTX.subvar))
        elif node.add :
            self.fill("yield event(%r, %s, Marking(), %s)"
                      % (node.CTX.trans.name, mvar, node.CTX.addvar))
        else :
            self.fill("yield event(%r, %s, Marking(), Marking())"
                      % (node.CTX.trans.name, mvar))
    def visit_DefSuccIter (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" (%s):" % node.marking)
        with self.indent() :
            if node.name.trans :
                self.fill(repr("successors of %r" % node.name.trans))
                self.children_visit(node.body, False)
            else :
                self.fill("return itertools.chain(")
                last = len(node.body) - 1
                for i, name in enumerate(node.body) :
                    if i > 0 :
                        ######### "return itertools.chain("
                        self.fill("                       ")
                    self.visit(name)
                    self.write("(%s)" % node.marking)
                    if i < last :
                        self.write(",")
                    else :
                        self.write(")")
        self.write("\n")
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
        self.fill("# '' maps to all-transitions proc")
        self.fill("succproc = {")
        for i, (trans, name) in enumerate(sorted(self.succproc.items())) :
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
        self.fill("# '' maps to all-transitions func")
        self.fill("succfunc = {")
        for i, (trans, name) in enumerate(sorted(self.succfunc.items())) :
            if i == 0 == len(self.succfunc) - 1 :
                self.write("%r: %s}" % (trans, name))
            elif i == 0 :
                self.write("%r: %s," % (trans, name))
            elif i == len(self.succfunc) - 1 :
                self.fill("            %r: %s}" % (trans, name))
            else :
                self.fill("            %r: %s," % (trans, name))
        self.write("\n")
    def visit_SuccIterTable (self, node) :
        self.fill("# map transitions names to successor iterators")
        self.fill("# '' maps to all-transitions iterator")
        self.fill("succiter = {")
        for i, (trans, name) in enumerate(sorted(self.succiter.items())) :
            if i == 0 == len(self.succiter) - 1 :
                self.write("%r: %s}" % (trans, name))
            elif i == 0 :
                self.write("%r: %s," % (trans, name))
            elif i == len(self.succiter) - 1 :
                self.fill("            %r: %s}" % (trans, name))
            else :
                self.fill("            %r: %s," % (trans, name))
        self.write("\n")

if __name__ == "__main__" :
    import io, sys
    from zinc.io.zn import load
    net = load(open(sys.argv[-1]))
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
