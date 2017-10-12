import importlib, string

def getlang (name) :
    modname = "snakes.compil." + name
    return importlib.import_module(modname)

class CompilationError (Exception) :
    def __init__ (self, msg, blame) :
        Exception.__init__(self, msg)
        self.blame = blame

class Context (object) :
    def __init__ (self, **attrs) :
        self._ast = importlib.import_module("snakes.compil.ast")
        self._fields = list(attrs)
        for name, value in attrs.items() :
            setattr(self, name, value)
    def __getattr__ (self, name) :
        if name[0] not in string.ascii_uppercase :
            raise AttributeError("context has no attribute %r" % name)
        def wrapper (*l, **k) :
            k.update({f.upper() : getattr(self, f) for f in self._fields})
            return getattr(self._ast, name)(*l, CTX=self, **k)
        return wrapper
    def update (self, **attrs) :
        if any(a in self._fields for a in attrs) :
            raise ValueError("duplicated fields")
        self._fields.extend(attrs)
        for name, value in attrs.items() :
            setattr(self, name, value)
