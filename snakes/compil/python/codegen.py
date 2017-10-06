import snakes.compil.ast as ast

class CodeGenerator (ast.CodeGenerator) :
    def visit_Module (self, node) :
        self.write("# %s\n" % self.timestamp())
        self.children_visit(node.body)
    def visit_DefineMarking (self, node) :
        self.fill("from snakes.nets import Marking\n")
    def visit_MarkingLookup (self, node) :
        self.write("%s[%r].keys()" % (node.marking, node.place))
    def visit_MarkingContains (self, node) :
        self.write("%s in %s[%r]" % (node.value, node.marking, node.place))
    def visit_NewMarking (self, node) :
        self.write("Marking({")
        for i, place in enumerate(node.content) :
            if i > 0 :
                self.write(", ")
            self.write("%r: [" % place)
            for tok in node.content[place][:-1] :
                self.visit(tok)
                self.write(", ")
            self.visit(node.content[place][-1])
            self.write("]")
        self.write("})")
    def visit_IsPlaceMarked (self, node) :
        self.write("%s[%r]" % (node.marking, node.place))
    def visit_AddMarking (self, node) :
        self.visit(node.left)
        self.write(" + ")
        self.visit(node.right)
    def visit_SubMarking (self, node) :
        self.visit(node.left)
        self.write(" - ")
        self.visit(node.right)
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
    def visit_If (self, node) :
        self.fill("if ")
        self.visit(node.expr)
        self.write(":")
        self.children_visit(node.body, True)
    def visit_InitSucc (self, node) :
        self.fill("%s = set()" % node.variable)
    def visit_AddSucc (self, node) :
        self.fill("%s.add(" % node.variable)
        self.visit(node.expr)
        self.write(")")
    def visit_ReturnSucc (self, node) :
        self.fill("return %s" % node.variable)
    def visit_DefSuccProc (self, node) :
        self.fill("def ")
        self.visit(node.name)
        self.write(" (%s, %s):" % (node.marking, node.succ))
        self.children_visit(node.body, True)
        self.write("\n")
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
    import sys
    CodeGenerator(sys.stdout).visit(ast.test)
