from snakes.compil import BaseDeclare
from snakes.compil.go.rename import rename

NONETYPE = False
BOOL = "bool"

class Declare (BaseDeclare) :
    _levels = ["import", "decl"]
    _default = "decl"

def ast2code (tree, output=None) :
    pass

def load (tree, name="net") :
    pass
