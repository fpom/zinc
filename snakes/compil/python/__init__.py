import io, types, ast

from . import codegen as _codegen

def isvar (name) :
    try :
        tree = ast.parse(name, mode="eval")
        if not isinstance(tree, ast.Expression) :
            return False
        elif not isinstance(tree.body, ast.Name) :
            return False
        return tree.body.id == name
    except :
        return False

def isexpr (code) :
    try :
        ast.parse(code, mode="eval")
        return True
    except :
        return False

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
