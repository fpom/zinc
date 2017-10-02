import importlib

def getlang (name) :
    modname = "snakes.compil." + name
    return importlib.import_module(modname)
