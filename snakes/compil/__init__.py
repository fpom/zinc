import importlib

def getlang (name) :
    modname = "snakes.compil." + name
    return importlib.import_module(modname)

class CompilationError (Exception) :
    def __init__ (self, msg, blame) :
        Exception.__init__(self, msg)
        self.blame = blame
