import re

elements = {
    "comment" : "|".join("(%s)" % s for s in [
        r"//(.*?)\n",
        r"/(\\\n)?[*](.|\n)*?[*](\\\n)?/"]),
    "string" : "|".join("(%s)" % s for s in [
        r"""'(\\['"\\abfnrtv]|\\x[0-9a-fA-F]{2}|\\[0-7]{1,3}"""
        r"""|\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|[^\\])'""",
        r"`[^`]*`",
        r'"(\\\\|\\"|[^"])*"']),
    "keyword" : "|".join("break     default      func    interface  select"
                         "case      defer        go      map        struct"
                         "chan      else         goto    package    switch"
                         "const     fallthrough  if      range      type"
                         "continue  for          import  return     var"
                         .split()),
    "name" : r"[^\W\d]\w*",
    "dot" : r"\."}

lexer = re.compile("|".join("(?P<%s>%s)" % pair for pair in elements.items()),
                   re.DOTALL|re.MULTILINE)

def _tokenize (text) :
    pos = 0
    for match in lexer.finditer(text) :
        s, e = match.span()
        if s > pos :
            yield "text", text[pos:s]
        for name, value in match.groupdict().items() :
            if value :
                yield name, value
                break
        pos = e

def rename (text, tr) :
    def ren() :
        dot = False
        for typ, txt in _tokenize(text) :
            if typ == "name" and not dot :
                yield tr.get(txt, txt)
            else :
                yield txt
            dot = typ == "dot"
    return "".join(ren())
