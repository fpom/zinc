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

parse = Parser.make_parser()
