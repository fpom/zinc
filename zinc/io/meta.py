from . import BaseParser
from . import metaparse

class Parser (BaseParser) :
    def __init__ (self, spec) :
        class MP (metaparse.MetaParser) :
            __compound__ = spec
        self.__parser__ = MP

def parse (source, spec) :
    if isinstance(source, str) :
        return Parser(spec).parse(source, "<string>")
    else :
        return Parser(spec).parse(source.read(), getattr(source, "name", "<string>"))
