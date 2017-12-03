import re

elements = {
    "comment" : r"(#[^\n].*[\n\r]|###.*?###)",
    "string" : "|".join("(%s)" % s for s in [
        r"'([^\'\\]|\\[^\n])*'",
        r'"([^\"\\]|\\[^\n])*"',
        r"'''.*?'''",
        r'""".*?"""',
    ]),
    "keyword" : "|".join(
        """case default function var void with const let enum export import
        native __hasProp __extends __slice __bind __indexOf implements else
        interface package private protected public static yield true false
        null this new delete typeof in arguments eval instanceof return throw
        break continue debugger if else switch for while do try catch finally
        class extends super undefined then unless until loop of by when and or
        is isnt not yes no on off""".split()),
    "name" : r"[\w$_](?<!\d)[\w$_]*",
    "dot_at" : r"[.@]"}

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
        dot_at = False
        for typ, txt in _tokenize(text) :
            if typ == "name" and not dot_at :
                yield tr.get(txt, txt)
            else :
                yield txt
            dot_at = typ == "dot_at"
    return "".join(ren())
