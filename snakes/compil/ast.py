import time

class CodeGenerator (object) :
    def __init__ (self, output) :
        self.output = output
        self.succfunc = {}
        self.succproc = {}
        self.initfunc = None
        self._indent = 0
        self._line = 0
        self._column = 0
    def write (self, code) :
        self.output.write(code)
        nl = code.count("\n")
        self._line += nl
        if nl :
            self._column = len(code) - code.rindex("\n") - 1
        else :
            self._column += len(code)
    def visit (self, node) :
        try :
            handler = getattr(self, "visit_" + node.__class__.__name__)
        except AttributeError :
            raise NotImplementedError("missing handler for '%s'"
                                      % node.__class__.__name__)
        loc = (self._line, self._column)
        handler(node)
        node.loc = (loc, (self._line, self._column))
    def fill (self, code="") :
        self.write("\n" + ("    " * self._indent) + code)
    def children_visit (self, children, indent=False) :
        if indent :
            self._indent += 1
        for child in children :
            self.visit(child)
        if indent :
            self._indent -= 1
    def timestamp (self) :
        return time.strftime("%c")
    def visit_SuccProcName (self, node) :
        if node.trans is None :
            name = "addsucc"
        elif node.trans not in self.succproc :
            name = "addsucc_%03u" % (len(self.succproc) + 1)
        else :
            name = self.succproc[node.trans]
        self.succproc[node.trans] = name
        self.write(name)
    def visit_SuccFuncName (self, node) :
        if node.trans is None :
            name = "succ"
        elif node.trans not in self.succfunc :
            name = "succ_%03u" % (len(self.succfunc) + 1)
        else :
            name = self.succfunc[node.trans]
        self.succfunc[node.trans] = name
        self.write(name)
    def visit_InitName (self, node) :
        name = self.initfunc = "init"
        self.write(name)
    def visit_Context (self, node) :
        for line in node.lines :
            self.write(line + "\n")

##
##
##

class AST (object) :
    def __init__ (self, *largs, **kargs) :
        for key in self._fields :
            setattr(self, key, None)
        for key, val in zip(self._fields, largs) :
            setattr(self, key, val)
        for key, val in kargs.items() :
            setattr(self, key, val)
    def _locate_children (self, line, column) :
        found = []
        for field in self._fields :
            child = getattr(self, field)
            if isinstance(child, AST) :
                found.extend(child.locate(line, column))
            elif isinstance(child, (tuple, list)) :
                for sub in child :
                    if isinstance(sub, AST) :
                        found.extend(sub.locate(line, column))
            elif isinstance(child, dict) :
                for sub in child.values() :
                    if isinstance(sub, AST) :
                        found.extend(sub.locate(line, column))
        return found
    def locate (self, line, column) :
        if not hasattr(self, "loc") :
            raise ValueError("AST has no locations")
        elif self.loc is None :
            return []
        (l0, c0), (l1, c1) = self.loc
        if ((l0 == line == l1 and c0 <= column < c1)
            or (l0 == line < l1 and c0 <= column)
            or (l0 < line == l1 and column <= c1)
            or (l0 < line < l1)) :
            return [self] + self._locate_children(line, column)
        return []

##
## top level
##

class Module (AST) :
    _fields = ["body"]

##
## marking structure
##

class MarkingLookup (AST) :
    _fields = ["marking", "place"]

class MarkingContains (AST) :
    _fields = ["marking", "place", "value"]

class NewMarking (AST) :
    _fields = ["content"]

class NewPlaceMarking (AST) :
    _fields = ["place", "tokens"]

class IsPlaceMarked (AST) :
    _fields = ["marking", "place"]

class AddMarking (AST) :
    _fields = ["left", "right"]

class SubMarking (AST) :
    _fields = ["left", "right"]

class DefineMarking (AST) :
    _fields = []

##
## expressions
##

class Name (AST) :
    _fields = ["name"]

class Value (AST) :
    _fields = ["value"]

class SourceExpr (AST) :
    _fields = ["source"]

class And (AST) :
    _fields = ["children"]

##
## generic control flow
##

class For (AST) :
    _fields = ["variable", "collection", "body"]

class If (AST) :
    _fields = ["expr", "body"]

##
## specific statements
##

class Context (AST) :
    _fields = ["lines"]

class InitSucc (AST) :
    _fields = ["variable"]

class AddSucc (AST) :
    _fields = ["variable", "old", "sub", "add"]

class ReturnSucc (AST) :
    _fields = ["variable"]

##
## functions
##

class DefSuccProc (AST) :
    _fields = ["name", "marking", "succ", "body"]

class SuccProcName (AST) :
    _fields = ["trans"]

class CallSuccProc (AST) :
    _fields = ["name", "marking", "succ"]

class DefSuccFunc (AST) :
    _fields = ["name", "marking", "body"]

class SuccFuncName (AST) :
    _fields = ["trans"]

class DefInitMarking (AST) :
    _fields = ["name", "marking"]

class InitName (AST) :
    _fields = []

##
##
##

test = Module([
    DefineMarking(),
    DefSuccProc(SuccProcName("t1"), "marking", "succ", [
        If(And([IsPlaceMarked("marking", "p1"),
                IsPlaceMarked("marking", "p2")]), [
            For("x", MarkingLookup("marking", "p1"), [
                For("y", MarkingLookup("marking", "p2"), [
                    If(SourceExpr("x != y"), [
                        AddSucc("succ",
                                AddMarking(SubMarking(Name("marking"),
                                                      NewMarking({"p1": [Name("x")],
                                                                  "p2": [Name("y")]})),
                                           NewMarking({"p3": [SourceExpr("x+y")]})))])])])])]),
    DefSuccFunc(SuccFuncName("t1"), "marking", [
        InitSucc("succ"),
        CallSuccProc(SuccProcName("t1"), "marking", "succ"),
        ReturnSucc("succ")]),
    DefSuccProc(SuccProcName(), "marking", "succ", [
        CallSuccProc(SuccProcName("t1"), "marking", "succ"),
        CallSuccProc(SuccProcName("t2"), "marking", "succ")]),
    DefSuccFunc(SuccFuncName(), "marking", [
        InitSucc("succ"),
        CallSuccProc(SuccProcName(), "marking", "succ"),
        ReturnSucc("succ")]),
    DefInitMarking(InitName(),
                   NewMarking({"p1": [Value("1"), Value("2"), Value("3")],
                               "p2": [Value("0"), Value("1")]}))])
