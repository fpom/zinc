import snakes.io.snk, sys
from . import build, CompilationError

net = snakes.io.snk.load(open(sys.argv[-1]))
ast = net.__ast__()
try :
    build(net.lang, ast, None)
except CompilationError as err :
    print(err.message())
