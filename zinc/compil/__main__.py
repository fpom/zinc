import zinc.io.zn, sys
from . import build, CompilationError

net = zinc.io.zn.load(open(sys.argv[-1]))
ast = net.__ast__()
try :
    build(net.lang, ast, None)
except CompilationError as err :
    print(err.message())
