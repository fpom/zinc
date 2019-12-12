from . import metaparse, BaseParser

class Parser (BaseParser) :
    class __parser__ (metaparse.MetaParser) :
        __compound__ = [["if", "then", "?else"],
                        ["choose", "+either"],
                        ["parallel", "+besides"],
                        ["race", "+against"],
                        ["retry"],
                        ["negate"],
                        ["task"]]

def parse (source) :
    if isinstance(source, str) :
        return Parser().parse(source, "<string>")
    else :
        return Parser().parse(source.read(), getattr(source, "name", "<string>"))
