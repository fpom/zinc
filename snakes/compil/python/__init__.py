import io, types, re

from . import codegen as _codegen

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
    exec(gen.output.getvalue(), ctx)
    ctx["__succfunc__"] = gen.succfunc
    ctx["__succproc__"] = gen.succproc
    ctx["__initfunc__"] = gen.initfunc
    mod = types.ModuleType(name)
    mod.__dict__.update(ctx)
    return mod
