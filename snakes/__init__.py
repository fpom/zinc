class SNAKESError (Exception) :
    pass

class ConstraintError (SNAKESError) :
    pass

class LanguageError (SNAKESError) :
    pass

class TypingError (SNAKESError) :
    pass

class ParseError (SNAKESError) :
    def __init__ (self, msg, lno=None, cno=None, path=None) :
        loc = ":".join(str(p) for p in (path, lno, cno) if p is not None)
        if loc :
            msg = "%s: %s" % (loc, msg)
        SNAKESError.__init__(self, msg)
