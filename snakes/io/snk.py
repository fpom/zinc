import tokenize, token, io, ast
import snakes.nets as nets

_tok = next(tokenize.tokenize(io.BytesIO(b"").readline))
token.tok_name[_tok.type] = "BACKQUOTE"

for number, name in token.tok_name.items() :
    if not hasattr(token, name) :
        setattr(token, name, number)


class ParseError (Exception) :
    def __init__ (self, msg, tok) :
        l, c = tok.start
        mesg = ["[%s:%s] %s" % (l, c+1, msg),
                "   " + tok.line.rstrip(),
                "   " + " " * c + "^"]
        Exception.__init__(self, "\n".join(mesg))
        self.tok = tok

class Parser (object) :
    def __init__ (self, source, module=nets) :
        if isinstance(source, str) :
            self._toks = tokenize.tokenize(io.BytesIO(source.encode()).readline)
        elif isinstance(source, bytes) :
            self._toks = tokenize.tokenize(io.BytesIO(source).readline)
        self._nets = module
        self._declare = []
        self._lang = "python"
        self._allowed = {"net", "declare", "lang"}
        self._arcs = {"val" : module.Value,
                      "var" : module.Variable,
                      "expr" : module.Expression}
        arcs = set(self._arcs)
        self._allowed_states = {
            "net" : {"place", "trans"},
            "declare" : {"net", "declare", "lang"},
            "lang" : {"net", "declare", "lang"},
            "place" : {"place", "trans"},
            "trans" : {"place", "trans"} | arcs}
        for a in arcs :
            self._allowed_states[a] = {"place", "trans"} | arcs
    def tail (self, tok, include) :
        t = next(self._toks)
        while t.type != token.NEWLINE :
            t = next(self._toks)
        self._last_tok = t
        if include :
            return tok.line[tok.start[1]:].strip()
        else :
            return tok.line[tok.end[1]:].strip()
    def _next (self) :
        tok = next(self._toks)
        while tok.type in {token.COMMENT, token.INDENT, token.DEDENT,
                           token.BACKQUOTE, token.NL} :
            tok = next(self._toks)
        (self.lineno, self.offset), self.line = tok.end, tok.line
        self._last_tok = tok
        return tok
    def get_next (self, expect=[], skip=[]) :
        tok = self._next()
        while tok.type in skip or tok.string in skip :
            tok = self._next()
        if expect and not (tok.type in expect or tok.string in expect) :
            exp = [token.tok_name.get(e, repr(e)) for e in expect]
            raise ParseError("expected %s but got %r (%s)"
                             % ("|".join(exp), tok.string, token.tok_name[tok.type]),
                             tok)
        return tok
    def get_text (self, tok=None) :
        if tok is None :
            tok = self.get_next([token.NAME, token.STRING])
        if tok.type == token.STRING :
            return ast.literal_eval(tok.string)
        else :
            return tok.string
    def get_code (self, tok) :
        while True :
            if tok.string == "$" :
                break
            elif not tok.string.strip() :
                pass
            tok = next(self._toks)
        pos = tok.end[1]
        close = {"{":"}", "(":")", "[":"]"}.get(tok.line[pos], tok.line[pos])
        try :
            end = tok.line.index(close, pos+1)
        except ValueError :
            raise ParseError("EOL while scanning code block", tok)
        code = tok.line[pos+1:end]
        while tok.end[1] <= end :
            tok = next(self._toks)
        return code
    def parse (self) :
        tok = self.get_next(self._allowed, [token.NEWLINE])
        while tok.type != token.ENDMARKER :
            try :
                handler, args = getattr(self, "parse_" + tok.string), []
            except AttributeError :
                handler, args = self.parse_arc, [tok.string]
            handler(*args)
            self._allowed = self._allowed_states[tok.string] | {token.ENDMARKER}
            tok = self.get_next(self._allowed, [token.NEWLINE])
        try :
            return self.net
        except AttributeError :
            raise ParseError("net description not found", None)
    def parse_declare (self) :
        tok = self.get_next()
        if tok.type == token.STRING :
            decl = self.get_text(tok)
            self.get_next([token.NEWLINE])
        else :
            decl = self.tail(tok, True)
        self._declare.append(decl)
    def parse_lang (self) :
        self._lang = self.get_text()
    def parse_net (self) :
        self._allowed.difference_update({"net", "declare", "lang"})
        self.net = self._nets.PetriNet(self.get_text(), self._lang)
        self.get_next([":"])
        self.get_next([token.NEWLINE])
        for decl in self._declare :
            self.net.declare(decl)
    def parse_place (self) :
        name = self.get_text()
        tok = self.get_next()
        typ_ = None
        if tok.type in {token.NAME, token.STRING} :
            typ_ = self.get_text(tok)
            tok = self.get_next()
        if tok.string == "=" :
            init = self.parse_tokens()
        elif tok.type == token.NEWLINE :
            init = []
        else :
            raise ParseError("expected '=' or NEWLINE, found %s"
                             % token.tok_name[tok.type], tok)
        self.net.add_place(self._nets.Place(name, init, typ_))
    def parse_trans (self) :
        name = self.get_text()
        tok = self.get_next()
        if tok.string == ":" :
            guard = None
        else :
            guard = self.tail(tok, True)
            if not guard.endswith(":") :
                raise ParseError("expected ':' found NEWLINE", self._last_tok)
            guard = guard.rstrip(": \t")
        self._trans = name
        self.net.add_transition(self._nets.Transition(name, guard))
    def parse_arc (self, arc) :
        place = self.get_text()
        tok = self.get_next({"<", ">"})
        isinput = tok.string == ">"
        label = self.tail(tok, False)
        if isinput :
            self.net.add_input(place, self._trans, self._arcs[arc](label))
        else :
            self.net.add_output(place, self._trans, self._arcs[arc](label))
    def parse_tokens (self) :
        tok = self.get_next()
        while True :
            if tok.type in {token.NUMBER, token.NAME} :
                yield self._nets.Token(tok.string)
            elif tok.type == token.STRING :
                yield self._nets.Token(repr(tok.string))
            elif tok.type == token.ERRORTOKEN :
                yield self._nets.Token(self.get_code(tok))
            else :
                raise ParseError("cannot interpret token %r" % tok.string, tok)
            tok = self.get_next()
            if tok.string == "," :
                tok = self.get_next()
            if tok.type == token.NEWLINE :
                break

if __name__ == "__main__" :
    p = Parser(open("test/simple.snk").read())
    net = p.parse()
    for place in net.place() :
        print(place.name, "(%s)" % place.type, "=", place.tokens)
    for trans in net.transition() :
        print(trans.name, "if", repr(trans.guard))
        for place, label in trans.input() :
            print("  ", place.name, ">", label)
        for place, label in trans.output() :
            print("  ", place.name, "<", label)

