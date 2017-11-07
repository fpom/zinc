import importlib, string, collections

from snakes import LanguageError

def getlang (name) :
    name = name.lower()
    try :
        module = importlib.import_module("snakes.compil." + name)
    except ImportError :
        raise LanguageError("unsupported language %r" % name)
    module.name = name
    return module

class BaseDeclare (object) :
    _levels = [None]
    _default = None
    def __init__ (self) :
        self._decl = collections.defaultdict(list)
    def __call__ (self, code, level=None) :
        lvl = level or self._default
        if lvl in self._levels :
            self._decl[lvl].append(code)
        else :
            raise ValueError("invalid declaration level %r" % lvl)
    def __iter__ (self) :
        for lvl in self._levels :
            for code in self._decl[lvl] :
                for line in code.splitlines() :
                    yield lvl, line
    def copy (self) :
        new = self.__class__()
        for lvl, code in self._decl.items() :
            new._decl[lvl] = code[:]
        return new

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
