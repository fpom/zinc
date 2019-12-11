# coding: utf-8

import io, re
from .. import ParseError

##
## insert INDENT/DEDENT
##

_indent = re.compile(r"^\s*")

def indedent (text, indent="↦", dedent="↤") :
    "insert INDENT/DEDENT tokens into text"
    stack = [0]
    src = io.StringIO(text.rstrip() + "\n")
    out = io.StringIO()
    for i, line in enumerate(src) :
        if line.rstrip() :
            width = _indent.match(line).end()
            if width > stack[-1] :
                out.write(indent)
                stack.append(width)
            elif width < stack[-1] :
                while width < stack[-1] :
                    out.write(dedent)
                    stack.pop()
                if width != stack[-1] :
                    raise IndentationError("line %s" % (i+1))
        out.write(line)
    while stack[-1] > 0 :
        out.write(dedent)
        stack.pop()
    return out.getvalue()

##
## base parser
##

_errre = re.compile(r"^.*?error at line ([0-9]+), col ([0-9]+):[ \t]*"
                    "((.|\n)*)$", re.I|re.A)

class BaseParser (object) :
    def init (self, parser) :
        pass
    def parse (self, source, path) :
        parser = self.__parser__(indedent(source))
        self.init(parser)
        try :
            do_parse = getattr(parser, parser.__default__, "INPUT")
            result = do_parse()
            if result is parser.NoMatch or parser.p_peek() is not None:
                parser.p_raise()
            return result
        except parser.ParserError as err :
            self._raise(err, path)
    def _raise (self, error, path=None) :
        message = str(error)
        match = _errre.match(message)
        if match :
            raise ParseError(match.group(3),
                             lno=int(match.group(1)),
                             cno=int(match.group(2)),
                             path=path)
        else :
            raise ParseError(message, path=path)
