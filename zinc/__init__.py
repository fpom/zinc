class ZINCError (Exception) :
    pass

class ConstraintError (ZINCError) :
    pass

class LanguageError (ZINCError) :
    pass

class TypingError (ZINCError) :
    pass

class ParseError (ZINCError) :
    def __init__ (self, msg, lno=None, cno=None, path=None) :
        loc = ":".join(str(p) for p in (path, lno, cno) if p is not None)
        if loc :
            msg = "[%s] %s" % (loc, msg)
        ZINCError.__init__(self, msg)

class CompileError (ParseError) :
    pass
