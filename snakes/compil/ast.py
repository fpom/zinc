import time, io

try:
    import autopep8
except :
    autopep8 = None

##
##
##

class _Record (object) :
    def __init__ (self, *largs, **kargs) :
        for key in self._fields :
            setattr(self, key, None)
        for key, val in zip(self._fields, largs) :
            setattr(self, key, val)
        for key, val in kargs.items() :
            setattr(self, key, val)
    def _dump (self, out) :
        out.write("%s(" % self.__class__.__name__)
        for field in self._fields :
            out.write("%s=" % field)
            child = getattr(self, field)
            if isinstance(child, _Record) :
                child._dump(out)
            elif isinstance(child, list) :
                out.write("[")
                for sub in child :
                    if isinstance(sub, _Record) :
                        sub._dump(out)
                    else :
                        out.write(repr(sub))
                    if sub is not child[-1] :
                        out.write(",\n")
                out.write("]")
            elif isinstance(child, dict) :
                out.write("{")
                for i, (key, sub) in enumerate(child.items()) :
                    out.write("%r: " % key)
                    if isinstance(sub, _Record) :
                        sub._dump(out)
                    else :
                        out.write(repr(sub))
                    if i < len(child) - 1 :
                        out.write(",\n")
                out.write("}")
            else :
                out.write(repr(child))
            if field != self._fields[-1] :
                out.write(",\n")
        out.write(")")
    def dump (self) :
        out = io.StringIO()
        self._dump(out)
        if autopep8 is None :
            return out.getvalue()
        else :
            return autopep8.fix_code(out.getvalue(), options={"aggressive": 1})

##
## record which net element is to blame for an error in the code
##

class Blame (_Record) :
    _fields = []

class ArcBlame (Blame) :
    _fields = ["source", "target", "label"]
    def __str__ (self) :
        return "label of arc %r -> %r: %r" % (self.source, self.target, self.label)

class TokenBlame (Blame) :
    _fields = ["place", "token"]
    def __str__ (self) :
        return "token in place %r: %r" % (self.place, self.token)

class PlaceBlame (Blame) :
    _fields = ["place", "marking"]
    def __str__ (self) :
        return "marking of place %r: %r" % (self.place, self.marking)

class GuardBlame (Blame) :
    _fields = ["trans", "guard"]
    def __str__ (self) :
        return "guard of transition %r: %r" % (self.trans, self.guard)

class ContextBlame (Blame) :
    _fields = ["code"]
    def __str__ (self) :
        return "declaration: %r" % self.code

##
##
##

class AST (_Record) :
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
    def blame (self, line, column) :
        for node in reversed(self.locate(line, column)) :
            if hasattr(node, "BLAME") :
                return node.BLAME

"""
Module(name, body=[
    # context declared for the net
    Context(source),
    # marking structure
    DefineMarking(places),
    # for each transition
    DefSuccProc(name=SuccProcName(trans), marking, succ, body=[
        IfInput(marking, places, body=[
            IfToken(marking, place, token, body=[
                ForeachToken(marking, place, variable, body=[
                    IfGuard(guard, body=[
                        IfType(place, token, body=[
                            AddSuccIfEnoughTokens(succ, old, sub, add)])])])])])]),
    DefSuccFunc(name=SuccFuncName(trans), marking, body=[
        InitSucc(name),
        CallSuccProc(name=SuccProcName(trans), marking, succ),
        ReturnSucc(name)]),
    ...
    ...
    # once for all
    DefSuccProc(name=SuccProcName(), marking, succ, body=[
        # for each transition
        CallSuccProc(name=SuccProcName(trans), marking, succ),
        ...]),
    # once for all
    DefSuccFunc(name=SuccFuncName(), marking, body=[
        InitSucc(name),
        CallSuccProc(SuccProcName(), marking, succ),
        ReturnSucc(name)]),
    DefInitFunc(name=InitName(), marking),
    SuccProcTable(),
    SuccFuncTable()])
"""

class Module (AST) :
    _fields = ["name", "body"]

class Context (AST) :
    _fields = ["source"]

class DefineMarking (AST) :
    _fields = ["places"]

class SuccProcName (AST) :
    _fields = ["trans"]

class SuccFuncName (AST) :
    _fields = ["trans"]

class InitName (AST) :
    _fields = []

class Expr (AST) :
    _fields = ["source"]
    def __hash__ (self) :
        return hash(self.source) ^ hash(self.__class__.__name__)
    def __eq__ (self, other) :
        try :
            return (self.__class__ == other.__class__) and (self.source == other.source)
        except :
            return False
    def __ne__ (self, other) :
        return not self.__eq__(other)
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.source)

class Var (Expr) :
    _fields = ["source"]

class Val (Expr) :
    _fields = ["source"]

class DefSuccProc (AST) :
    _fields = ["name", "marking", "succ", "body"]

class DefSuccFunc (AST) :
    _fields = ["name", "marking", "body"]

class DefInitFunc (AST) :
    _fields = ["name", "marking"]

class IfInput (AST) :
    _fields = ["marking", "places", "body"]

class IfToken (AST) :
    _fields = ["marking", "place", "token", "body"]

class ForeachToken (AST) :
    _fields = ["marking", "place", "variable", "body"]

class IfGuard (AST) :
    _fields = ["guard", "body"]

class IfType (AST) :
    _fields = ["place", "token", "body"]

class AddSuccIfEnoughTokens (AST) :
    _fields = ["succ", "old", "sub", "add"]

class InitSucc (AST) :
    _fields = ["name"]

class CallSuccProc (AST) :
    _fields = ["name", "marking", "succ"]

class ReturnSucc (AST) :
    _fields = ["name"]

class SuccProcTable (AST) :
    _fields = []

class SuccFuncTable (AST) :
    _fields = []

class PlaceMarking (AST) :
    _fields = ["place", "tokens"]

##
##
##

class Indent (object) :
    def __init__ (self, gen) :
        self.gen = gen
    def __enter__ (self) :
        self.gen._indent += 1
    def __exit__ (self, exc_type, exc_val, exc_tb) :
        self.gen._indent -= 1

class CodeGenerator (object) :
    def __init__ (self, output) :
        self.output = output
        self.succfunc = {}
        self.succproc = {}
        self.initfunc = None
        self._indent = 0
        self._line = 0
        self._column = 0
    def indent (self) :
        return Indent(self)
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
        span = self.output.tell()
        handler(node)
        node.loc = (loc, (self._line, self._column))
        node.span = (span, self.output.tell())
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
    def visit_Context (self, node) :
        if node.source :
            self.fill(node.source + "\n")
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
