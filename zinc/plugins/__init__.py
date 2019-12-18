import importlib, types, sys, inspect

from .. import ZINCError

class PluginError (ZINCError) :
    pass

class Plugin (object) :
    modname = "zn"
    plugins = []
    modules = []
    def __init__ (self, *extends, conflicts=[], depends=[]) :
        # check conflicts
        for p in conflicts :
            if p in self.plugins :
                raise PluginError("plugin conflicts with %r" % p)
        # load dependencies
        for p in depends :
            try :
                return importlib.import_module(p)
            except :
                try :
                    return importlib.import_module("zinc.plugins." + p)
                except :
                    raise PluginError("could not load %r from '.'  or 'zinc.plugins'" % p)
        # create result module
        if self.modname not in sys.modules :
            sys.modules[self.modname] = types.ModuleType(self.modname)
        self._mod = sys.modules[self.modname]
        # load extended modules
        for base in extends :
            if base not in self.modules :
                mod = importlib.import_module(base)
                self._mod.__dict__.update(mod.__dict__)
                self.modules.append(base)
        # record loaded plugin
        stack = inspect.stack()
        caller = inspect.getmodule(stack[1][0])
        self.plugins.append(caller.__name__)
    def __getattr__ (self, name) :
        return getattr(self._mod, name)
    def __call__ (self, obj) :
        setattr(self._mod, obj.__name__, obj)
        setattr(obj, "__plugmod__", self._mod)
        return obj
    @classmethod
    def reset_plugins (cls, name="zn") :
        for p in cls.plugins + cls.modules + [cls.modname] :
            del sys.modules[p]
        cls.modname = name
        cls.plugins = []
        cls.modules = []
