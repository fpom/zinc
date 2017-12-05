import subprocess, os.path, os, inspect
import zinc
from zinc.compil import BaseDeclare, CompilationError
from zinc.compil.go.rename import rename
from . import codegen

DESCRIPTION = "Golang backend (http://golang.org)"
OPTIONS = {}

NONETYPE = False
BOOL = "bool"
EXT = ".go"
INMEM = False

class Declare (BaseDeclare) :
    _levels = ["import", "decl"]
    _default = "decl"

def update_gopath () :
    # TODO: fix this wrt installation path
    path = os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(zinc))),
                        "libs", "go")
    if "GOPATH" not in os.environ :
        os.environ["GOPATH"] = path
    elif path not in os.environ["GOPATH"].split(":") :
        os.environ["GOPATH"] = ":".join([path, os.environ["GOPATH"]])

def build (ast, src, name, **options) :
    update_gopath()
    try :
        subprocess.check_output(["go", "build", src], stderr=subprocess.STDOUT)
    except Exception as err :
        out = err.output.decode()
        for line in out.splitlines() :
            try :
                path, lineno, message = line.split(":", 2)
                if path.endswith(src) :
                    raise CompilationError(ast, name, message.strip(), int(lineno), out)
            except ValueError :
                continue
        raise CompilationError(ast, name, out)
