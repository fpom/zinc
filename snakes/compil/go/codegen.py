import re
import snakes.compil.ast as ast

def _str (s) :
    return '"%s"' % s.replace('"', '\\"')

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        name = re.sub("(^[\W\d])|\W", "", node.name) or "net"
        self.write("// %s\npackage %s\n" % (self.timestamp(), name))
        self.children_visit(node.body)
    def visit_DefineMarking (self, node) :
        self.fill('import "snk"\nimport "fmt"\n')
    def visit_DefSuccProc (self, node) :
        self.fill("func ")
        self.visit(node.name)
        self.write(" (%s *snk.Marking, %s *snk.Set) {" % (node.marking, node.succ))
        self.children_visit(node.body, True)
        self.fill("}\n")
    def visit_InputMarked (self, node) :
        self.write("%s.NotEmpty(" % node.marking)
        for i, p in enumerate(node.places) :
            if i == 0 :
                self.write(_str(p))
            else :
                self.write(", " + _str(p))
        self.write(")")
    def visit_If (self, node) :
        self.fill("if ")
        self.visit(node.expr)
        self.write(" {")
        self.children_visit(node.body, True)
        self.fill("}")


    def visit_MarkingLookup (self, node) :
        self.write("%s[%r].keys()" % (node.marking, node.place))
    def visit_MarkingContains (self, node) :
        self.write("%s in %s[%r]" % (node.value, node.marking, node.place))
    def visit_NewMarking (self, node) :
        self.write("Marking({")
        for child in node.content :
            self.visit(child)
            if child is not node.content[-1] :
                self.write(", ")
        self.write("})")
    def visit_NewPlaceMarking (self, node) :
        self.write("%r: [" % node.place)
        for tok in node.tokens :
            self.visit(tok)
            if tok is not node.tokens[-1] :
                self.write(", ")
        self.write("]")
    def visit_Name (self, node) :
        self.write(node.name)
    def visit_Value (self, node) :
        self.write(node.value)
    def visit_SourceExpr (self, node) :
        self.write(node.source)
    def visit_And (self, node) :
        for child in node.children[:-1] :
            self.visit(child)
            self.write(" and ")
        self.visit(node.children[-1])
    def visit_For (self, node) :
        self.fill("for %s in " % node.variable)
        self.visit(node.collection)
        self.write(":")
        self.children_visit(node.body, True)
    def visit_InitSucc (self, node) :
        self.fill("%s = set()" % node.variable)
    def visit_AddSucc (self, node) :
        self.fill("%s.add(" % node.variable)
        self.visit(node.old)
        self.write(" - ")
        self.visit(node.sub)
        self.write(" + ")
        self.visit(node.add)
        self.write(")")
    def visit_ReturnSucc (self, node) :
        self.fill("return %s" % node.variable)
    def visit_CallSuccProc (self, node) :
        self.fill()
        self.visit(node.name)
        self.write("(%s, %s)" % (node.marking, node.succ))
    def visit_DefSuccFunc (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" (%s):" % node.marking)
        self.children_visit(node.body, True)
        self.write("\n")
    def visit_DefInitMarking (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" ():")
        self._indent += 1
        self.fill("return ")
        self.visit(node.marking)
        self._indent -= 1
        self.write("\n")

if __name__ == "__main__" :
    import io
    from snakes.io.snk import Parser
    net = Parser(open("test/simple-go.snk").read()).parse()
    gen = CodeGenerator(io.StringIO())
    gen.visit(net.__ast__())
    print(gen.output.getvalue().rstrip())
