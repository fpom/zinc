import inspect

def autorepr (cls=None, **defaults) :
    def wrapper (cls) :
        sig = inspect.signature(cls.__init__)
        def __repr__ (self) :
            parts = []
            for i, (arg, info) in enumerate(sig.parameters.items()) :
                if i > 0 :
                    val = getattr(self, arg)
                    if info.default is inspect._empty :
                        parts.append(repr(val))
                    elif val != info.default and val != defaults.get(arg, val) :
                        parts.append("%s=%r" % (arg, val))
            return "%s(%s)" % (self.__class__.__name__, ", ".join(parts))
        cls.__repr__ = __repr__
        return cls
    if cls is not None :
        assert not defaults, "invalid use of @autorepr"
        return wrapper(cls)
    else :
        return wrapper
