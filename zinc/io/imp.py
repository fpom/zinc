import pathlib, logging, inspect
from .. import CompileError, nets
from . import metaparse, BaseParser
from .meta import Compiler as BaseCompiler, node as decl

class Parser (BaseParser) :
    class __parser__ (metaparse.MetaParser) :
        __compound__ = [["if", "*elif", "?else"],
                        ["for", "?else"],
                        ["while", "?else"],
                        ["try", "except"],
                        ["def"],
                        ["task"]]

parse = Parser.make_parser()

class Context (dict) :
    def __call__ (self, **args) :
        d = self.copy()
        d.update(args)
        return d
    def __getattr__ (self, key) :
        return self[key]
    def __setattr__ (self, key, val) :
        self[key] = val

class Compiler (BaseCompiler) :
    def __init__ (self, module=nets) :
        self.n = module
    def __call__ (self, source) :
        self.p = Parser()
        tree = self.parser.parse(source)
        self._tasks = {}
        return self.visit(tree, Context(_path=pathlib.Path("/")))
    def _get_pos (self, node) :
        if "_pos" in node :
            return (self.p.parser._p_get_line(node._pos),
                    self.p.parser._p_get_col(node._pos) - 1)
        else :
            return None, None
    def warn (self, node, message) :
        lno, cno = self._get_pos(node)
        if lno is not None :
            message = "[%s] %s" % (":".join([self.p.path, str(lno)]), message)
        logging.warn(message)
    def _check (self, node, cond, error) :
        lno, cno = self._get_pos(node)
        raise CompileError(error, lno=lno, cno=cno, path=self.p.path)
    def build_seq (self, seq, ctx) :
        net = self.visit(seq[0], ctx)
        for other in seq[1:] :
            n = self.visit(other, ctx)
            if n is not None :
                net &= n
        return net
    def visit_model (self, node, ctx) :
        return self.visit_seq(node.body, ctx)
    def visit_task (self, node, ctx) :
        pass
    def visit_def (self, node, ctx) :
        self._check(node, node.deco is None, "decorators are not supported")
        self._check(node, node.largs, "missing parameters NAME")
        self._check(node, node.largs[0].type == "name",
                    "invalid function name %r (%s)" % (node.largs[0].value,
                                                       node.largs[0].type))
        for a in node.largs[1:] :
            self._check(node, a.kind == "name", "invalid parameter %s (%s)"
                        % (a.value, a.kind))
        for a, v in node.kargs.items() :
            self._check(node, v.kind in ("int", "code", "str"),
                        "invalid defaut value for parameter %s: %r (%s)"
                        % (a, v.value, v.kind))
        name = node.largs[0].value
        if name in ctx :
            self.warn(node, "previous declaration of %r is masked" % name)
        path = ctx._path / name
        flag = inspect.Parameter.POSITIONAL_OR_KEYWORD
        sig = inspect.Signature([inspect.Parameter(a.value, flag)
                                 for a in node.largs[1:]]
                                + [inspect.Parameter(a, flag, default=v.value)
                                   for a, v in node.kargs.items()])
        ctx[name] = decl(kind="function", args=sig)        
        body = self.build_seq(node.body, ctx(_path=path,
                                             **{a : decl(kind="variable")
                                                for a in sig.parameters}))
        # TODO: add initial transition that gets all the arguments and store them into
        # buffer places + terminal transition that flush these places and return
        # the value
        call = ret = None
        net = (call & body & ret) / tuple(sig.parameters)
        self._tasks[path] = net.task(name)
    def visit_assign (self, node, ctx) :
        tgt = node.target
        val = node.value
        self._check(node, tgt not in ctx or ctx[tgt].kind == "variable",
                    "cannot assign to previously declared %s %r"
                    % (ctx[tgt].kind, tgt))
        if val.tag == "call" :
            net = self.visit(val)
            if tgt not in net :
                net.add_place(self.n.Place(tgt, status=self.n.buffer(tgt)))
            if tgt in ctx :
                net.add_input(tgt, "_w", self.n.Variable("_"))
            net.add_output(tgt, "_w", self.n.Variable("_r"))
        else :
            net = self.n.PetriNet("[%s:%s] %s" % (self._get_pos(node) + (node._src,)))
            net.add_transition(self.n.Transition("_t"))
            net.add_place(self.n.Place(tgt, status=self.n.buffer(tgt)))
            net.add_place(self.n.Place("_e", status=self.n.entry))
            net.add_place(self.n.Place("_x", status=self.n.exit))
            net.add_input("_e", "_t", self.n.Value(self.n.dot))
            net.add_output("_x", "_t", self.n.Value(self.n.dot))
            if tgt in ctx :
                net.add_input(tgt, "_t", self.n.Variable("_"))
            if val.tag == "name" :
                net.add_place(self.n.Place(tgt.value))
                net.add_input(tgt.value, "_t", self.n.Test(self.n.Variable("_v")))
                net.add_output(tgt, "_t", self.n.Variable("_v"))
            elif val.tag in ("int", "str") :
                net.add_output(tgt, "_t", self.n.Value(repr(val.value)))
            elif val.tag == "code" :
                net.add_output(tgt, "_t", self.n.Expression(val.value))
            else :
                self._check(node, False, "unsupported assignment %r" % node._src)
        ctx[tgt] = decl(kind="variable")
        return net
    def visit_call (self, node, ctx) :
        self._check(node, node.name in ctx, "undeclared function %r" % node.name)
        self._check(node, ctx[node.name].kind == "function",
                    "%s %s is not a function" % (ctx[node.name].kind, node.name))
        try :
            argmap = ctx[node.name].args.bind(*node.largs, **node.kwargs)
            argmap.apply_defaults()
        except Exception as err :
            self._check(node, False, str(err))
        net = self.n.PetriNet("[%s:%s] %s" % (self._get_pos(node) + (node._src,)))
        net.add_place(self.n.Place("_e", status=self.n.entry))
        net.add_place(self.n.Place("_i", status=self.n.internal))
        net.add_place(self.n.Place("_x", status=self.n.exit))
        net.add_transition(self.n.Transition("_c"))
        net.add_transition(self.n.Transition("_w"))
        net.add_input("_e", "_t", self.n.Value(self.n.dot))
        net.add_output("_i", "_t", self.n.Value(self.n.dot))
        net.add_input("_i", "_w", self.n.Value(self.n.dot))
        net.add_output("_x", "_w", self.n.Variable("_s"))
        label = []
        for arg, val in argmap.arguments :
            if val.kind == "name" :
                if not net.has_place(val.value) :
                    net.add_place(self.n.Place(val.value, status=self.n.entry))
                net.add_input(val.value, "_c", self.n.Test(self.n.Variable(val.value)))
                label.append(self.n.Variable(val.value))
            elif val.kind in ("int", "str") :
                label.append(self.n.Value(repr(val.value)))
            elif val.kind == "code" :
                label.append(self.n.Expression(val.value))
        net.add_place(self.n.Place("call_" + node.name))
        net.add_output("call_" + node.name, "_c", self.n.Tuple(self.n.dot,
                                                               self.n.Tuple(*label)))
        net.add_place(self.n.Place("ret_" + node.name))
        net.add_input("ret_" + node.name, "_w", self.n.Tuple(self.n.Variable("_s"),
                                                             self.n.Variable("_r")))
        return net
    def visit_if (self, node, ctx) :
        pass
    def visit_for (self, node, ctx) :
        pass
    def visit_while (self, node, ctx) :
        pass
    def visit_try (self, node, ctx) :
        pass
