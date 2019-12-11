from .. import nets
from . import znparse, BaseParser

class Parser (BaseParser) :
    __parser__ = znparse.ZnParser
    def __init__ (self, module=nets) :
        self.n = module
    def init (self, parser) :
        parser.n = self.n

def loads (source, module=nets) :
    return Parser(module).parse(source, "<string>")

def load (stream, module=nets) :
    return Parser(module).parse(stream.read(), getattr(stream, "name", "<string>"))

if __name__ == "__main__" :
    import sys
    net = load(open(sys.argv[-1]))
    print(repr(net))
    for place in net.place() :
        print(place)
    for trans in net.transition() :
        print(trans)
        for place, label in trans.input() :
            print("<", place.name, label)
        for place, label in trans.output() :
            print(">", place.name, label)
