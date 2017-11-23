import importlib, string, collections, io, tempfile, os, os.path

from snakes import LanguageError

def getlang (name) :
    name = name.lower()
    try :
        module = importlib.import_module("snakes.compil." + name)
    except ImportError :
        raise LanguageError("unsupported language %r" % name)
    module.name = name
    return module

def build (lang, tree, saveto) :
    if saveto is None :
        out = io.StringIO()
    elif isinstance(saveto, str) :
        out = open(str, "w+")
    else :
        try :
            saveto.write("hello world!")
            saveto.seek(0)
            if saveto.read(12) != "hello world!" :
                raise IOError()
            saveto.seek(0)
            saveto.truncate()
            saveto.flush()
            if not os.path.exists(saveto.name) :
                raise IOError()
        except :
            raise ValueError("%r object does not have expected file-like feature"
                             % saveto.__class__.__name__)
        out = saveto
    gen = lang.codegen.CodeGenerator(out)
    gen.visit(tree)
    out.flush()
    out.seek(0)
    if lang.INMEM :
        mod = lang.build(tree, out, tree.name + lang.EXT)
    elif saveto is None :
        try :
            tmp = tempfile.NamedTemporaryFile(mode="w+", suffix=lang.EXT, delete=False)
            tmp.write(out.read())
            tmp.close()
            mod = lang.build(tree, tmp.name, tree.name + lang.EXT)
        finally :
            os.unlink(tmp.name)
    else :
        mod = lang.build(tree, out.name, os.path.basename(out.name))
    if mod is not None :
        mod.__ast__ = tree
    return mod

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
    def __init__ (self, ast, path, msg, loc=None, details=None) :
        if loc is None :
            short = "%s: %s" % (path, msg.strip())
            self.blame = None
        elif not isinstance(loc, tuple) :
            short = "%s[%s]: %s" % (path, loc, msg.strip())
            self.blame = ast.blame(int(loc) - 1, 0)
        else :
            short = "%s[%s:%s]: %s" % (path, loc[0] - 1, loc[1], msg.strip())
            self.blame = ast.blame(*loc)
        Exception.__init__(self, short)
        self.ast = ast
        self.path = path
        self.loc = loc
        self.details = details
    def message (self) :
        msg = ["[ERROR] %s" % self]
        if self.blame is not None :
            msg.append("[BLAME] %s" % self.blame)
        msg.append(self.details)
        return "\n".join(msg)

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
