from . import BaseParser
from . import metaparse

class Parser (BaseParser) :
    def __init__ (self, spec) :
        class MP (metaparse.MetaParser) :
            __compound__ = spec
        self.__parser__ = MP

parse = Parser.make_parser()
Compiler = metaparse.Compiler
node = metaparse.node
