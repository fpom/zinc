import time

class CodeGenerator (object) :
    def __init__ (self, output) :
        self.output = output
    def timestamp (self) :
        return time.strftime("%c")
    def visit (self, node) :
        try :
            handler = getattr(self, "visit_" + node.__class__.__name__)
        except AttributeError :
            handler = self.generic_visit
        handler(node)
    def generic_visit (self, node) :
        pass
    def children_visit (self, children) :
        for child in children :
            self.visit(child)

##
##
##

class AST (object) :
    def __init__ (self, *largs, **kargs) :
        for key, val in zip(self._fields, largs) :
            setattr(self, key, val)
        for key, val in kargs.items() :
            setattr(self, key, val)

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

class NewMarking (AST) :
    _fields = ["content"]

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

class InitSucc (AST) :
    _fields = ["variable"]

class AddSucc (AST) :
    _fields = ["variable", "expr"]

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
    _fields = ["marking"]

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
    DefSuccFunc(None, "marking", [
        InitSucc("succ"),
        CallSuccProc(SuccProcName("t1"), "marking", "succ"),
        CallSuccProc(SuccProcName("t2"), "marking", "succ"),
        ReturnSucc("succ")]),
    DefInitMarking(NewMarking({"p1": [Value("1"), Value("2"), Value("3")],
                               "p2": [Value("0"), Value("1")]}))])
