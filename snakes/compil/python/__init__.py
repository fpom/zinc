import io, types, traceback, sys
from . import codegen as _codegen
from snakes.compil import CompilationError
from snakes.compil.python.rename import rename

NONETYPE = True

def codegen (tree, output=None) :
    if output is None :
        out = io.StringIO()
    elif isinstance(output, str) :
        out = open(output)
    else :
        out = output
    gen = _codegen.CodeGenerator(out)
    gen.visit(tree)
    if output is None :
        return gen

def load (tree, name="net") :
    gen = codegen(tree)
    ctx = {}
    try :
        exec(gen.output.getvalue(), ctx)
    except Exception as err :
        c, v, t = sys.exc_info()
        msg = traceback.format_exception_only(c, v)
        msg.insert(0, "[ERROR] " + msg.pop(-1))
        if hasattr(err, "lineno") and hasattr(err, "offset") :
            line, column = err.lineno - 1, err.offset -1
        else :
            tb = t
            while tb.tb_next :
                tb = tb.tb_next
            line, column = tb.tb_lineno, 0
        blame = tree.blame(line, column)
        if blame :
            raise CompilationError("%s[BLAME] %s" % ("".join(msg), blame), blame)
        raise CompilationError("".join(msg).rstrip(), None)
    ctx["__succfunc__"] = gen.succfunc
    ctx["__succproc__"] = gen.succproc
    ctx["__initfunc__"] = gen.initfunc
    mod = types.ModuleType(name)
    mod.__dict__.update(ctx)
    return mod
