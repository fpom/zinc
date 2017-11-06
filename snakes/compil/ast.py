import time, io, inspect

from snakes.data import mset, iterate, record
from snakes.arcs import Tuple
from snakes.nodes import Place

try:
    import autopep8
except :
    autopep8 = None

##
##
##

class _Record (object) :
    def __init__ (self, *l, **k) :
        sign = inspect.signature(self.__init__)
        args = sign.bind(*l, **k).arguments
        self._fields = []
        for name, value in args.items() :
            # name, "=", value, "as", sign.parameters[name].annotation)
            param = sign.parameters[name]
            if param.kind == param.VAR_KEYWORD :
                for n, v in value.items() :
                    setattr(self, n, v)
            elif (param.annotation == sign.empty
                  or (value is None and None in iterate(param.annotation))
                  or any(isinstance(value, a) for a in iterate(param.annotation))) :
                if not value and param.annotation in (list, tuple, dict, set, mset) :
                    value = param.annotation()
                setattr(self, name, value)
                self._fields.append(name)
            else :
                raise TypeError("unexpected type %r for argument %r of %s"
                                % (value.__class__.__name__, name,
                                   self.__class__.__name__, ))
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
    pass

class ArcBlame (Blame) :
    def __init__ (self, source:str, target:str, label, **extra) :
        Blame.__init__(self, source, target, label, **extra)
    def __str__ (self) :
        return "label of arc %r -> %r: %r" % (self.source, self.target, self.label)

class TokenBlame (Blame) :
    def __init__ (self, place:str, token:str, **extra) :
        Blame.__init__(self, place, token, **extra)
    def __str__ (self) :
        return "token in place %r: %r" % (self.place, self.token)

class PlaceBlame (Blame) :
    def __init__ (self, place:str, marking:list, **extra) :
        Blame.__init__(self, place, marking, **extra)
    def __str__ (self) :
        return "marking of place %r: %r" % (self.place, self.marking)

class GuardBlame (Blame) :
    def __init__ (self, trans:str, guard:str, **extra) :
        Blame.__init__(self, trans, guard, **extra)
    def __str__ (self) :
        return "guard of transition %r: %r" % (self.trans, self.guard)

class ContextBlame (Blame) :
    def __init__ (self, code:str, **extra) :
        Blame.__init__(self, code, **extra)
    def __str__ (self) :
        return "declaration: %r" % self.code

class TransitionBlame (Blame) :
    def __init__ (self, transition:str, **extra) :
        Blame.__init__(self, transition, **extra)
    def __str__ (self) :
        return "transition: %r" % self.transition

##
##
##

class AST (_Record) :
    def __str__ (self) :
        raise TypeError("cannot coerce %s to str" % self.__class__.__name__)
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

class Module (AST) :
    def __init__ (self, name:str, body:list=[], **extra) :
        AST.__init__(self, name, body, **extra)

class Context (AST) :
    def __init__ (self, source:str, **extra) :
        AST.__init__(self, source, **extra)

class DefineMarking (AST) :
    def __init__ (self, places:list, **extra) :
        AST.__init__(self, places, **extra)

class SuccProcName (AST) :
    def __init__ (self, trans:str="", **extra) :
        AST.__init__(self, trans, **extra)

class SuccFuncName (AST) :
    def __init__ (self, trans:str="", **extra) :
        AST.__init__(self, trans, **extra)

class InitName (AST) :
    def __init__ (self, **extra) :
        AST.__init__(self, **extra)

class Expr (AST) :
    def __init__ (self, source:str, **extra) :
        AST.__init__(self, source, **extra)

class TrueConst (Expr) :
    def __init__ (self, **extra) :
        AST.__init__(self, **extra)

class FalseConst (Expr) :
    def __init__ (self, **extra) :
        AST.__init__(self, **extra)

class Assign (AST) :
    def __init__ (self, variable:str, expr:Expr, **extra) :
        AST.__init__(self, variable, expr, **extra)

class AssignItem (AST) :
    def __init__ (self, variable:str, container:str, path:list, **extra) :
        AST.__init__(self, variable, container, path, **extra)

class DefSuccProc (AST) :
    def __init__ (self, name:SuccProcName, marking:str, succ:str,
                  body:list=[], **extra) :
        AST.__init__(self, name, marking, succ, body, **extra)

class DefSuccFunc (AST) :
    def __init__ (self, name:SuccFuncName, marking:str, body:list=[], **extra) :
        AST.__init__(self, name, marking, body, **extra)

class DefInitFunc (AST) :
    def __init__ (self, name:InitName, marking:list, **extra) :
        AST.__init__(self, name, marking, **extra)

class Declare (AST) :
    def __init__ (self, variables:dict, **extra) :
        AST.__init__(self, variables, **extra)

class Eq (Expr) :
    def __init__ (self, left:Expr, right:Expr, **extra) :
        AST.__init__(self, left, right, **extra)

class And (Expr) :
    def __init__ (self, items:list, **extra) :
        AST.__init__(self, items, **extra)

class Pattern (AST) :
    def __init__ (self, arc:Tuple, matcher:tuple, placetype:tuple, **extra) :
        AST.__init__(self, arc, matcher, placetype, **extra)

class IfInput (AST) :
    def __init__ (self, marking:str, places:set, body:list=[], **extra) :
        AST.__init__(self, marking, places, body, **extra)

class IfToken (AST) :
    def __init__ (self, marking:str, place:Place, token:str, body:list=[], **extra) :
        AST.__init__(self, marking, place, token, body, **extra)

class IfPlace (AST) :
    def __init__ (self, marking:str, place:Place, variable:str, body:list=[], **extra) :
        AST.__init__(self, marking, place, variable, body, **extra)

class GetPlace (AST) :
    def __init__ (self, variable:str, marking:str, place:Place, **extra) :
        AST.__init__(self, variable, marking, place, **extra)

class IfAllType (AST) :
    def __init__ (self, place:Place, variable:str, body:list=[], **extra) :
        AST.__init__(self, place, variable, body, **extra)

class IfNoToken (AST) :
    def __init__ (self, marking:str, place:Place, token:str, body:list=[], **extra) :
        AST.__init__(self, marking, place, token, body, **extra)

class IfNoTokenSuchThat (AST) :
    def __init__ (self, marking:str, place:Place, variable:str, guard:Expr,
                  body:list=[], **extra) :
        AST.__init__(self, marking, place, variable, guard, body, **extra)

class ForeachToken (AST) :
    def __init__ (self, marking:str, place:Place, variable:str, body:list=[], **extra) :
        AST.__init__(self, marking, place, variable, body, **extra)

class Break (AST) :
    pass

class If (AST) :
    def __init__ (self, guard:Expr, body:list=[], **extra) :
        AST.__init__(self, guard, body, **extra)

class IfType (AST) :
    def __init__ (self, place:[Place, record], token:str, body:list=[], **extra) :
        AST.__init__(self, place, token, body, **extra)

class IfTuple (AST) :
    def __init__ (self, place:[Place, record], token:str, body:list=[], **extra) :
        AST.__init__(self, place, token, body, **extra)

class AddSuccIfEnoughTokens (AST) :
    def __init__ (self, succ:str, old:str, test:dict, sub:dict, add:dict, **extra) :
        AST.__init__(self, succ, old, test, sub, add, **extra)

class InitSucc (AST) :
    def __init__ (self, name:str, **extra) :
        AST.__init__ (self, name, **extra)

class CallSuccProc (AST) :
    def __init__ (self, name:SuccProcName, marking:str, succ:str, **extra) :
        AST.__init__(self, name, marking, succ, **extra)

class ReturnSucc (AST) :
    def __init__ (self, name:str, **extra) :
        AST.__init__(self, name, **extra)

class SuccProcTable (AST) :
    def __init__ (self, **extra) :
        AST.__init__(self, **extra)

class SuccFuncTable (AST) :
    def __init__ (self, **extra) :
        AST.__init__(self, **extra)

class PlaceMarking (AST) :
    def __init__ (self, place:str, tokens:list, **extra) :
        AST.__init__(self, place, tokens, **extra)

##
##
##

class Indent (object) :
    def __init__ (self, gen, inc=1) :
        self.gen = gen
        self.inc = inc
    def __enter__ (self) :
        self.gen._indent += self.inc
    def __exit__ (self, exc_type, exc_val, exc_tb) :
        self.gen._indent -= self.inc

class CodeGenerator (object) :
    def __init__ (self, output) :
        self.output = output
        self.succfunc = {}
        self.succproc = {}
        self.initfunc = None
        self._indent = 0
        self._line = 0
        self._column = 0
    def indent (self, inc=1) :
        return Indent(self, inc)
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
        if not node.trans :
            name = "addsucc"
        elif node.trans not in self.succproc :
            name = "addsucc_%03u" % (len(self.succproc) + 1)
        else :
            name = self.succproc[node.trans]
        self.succproc[node.trans] = name
        self.write(name)
    def visit_SuccFuncName (self, node) :
        if not node.trans :
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

if __name__ == "__main__" :
    from snakes.io.snk import load
    net = load(open("test/simple-python.snk"))
    print(net.__ast__().dump())
