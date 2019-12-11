# coding: utf-8

import ast
import fastidious

class node (object) :
    def __init__ (self, tag, **children) :
        self.__dict__.update(tag=tag, **children)
        self._fields = list(children)
    def __setitem__ (self, key, val) :
        setattr(self, key, val)
        if key not in self._fields :
            self._fields.append(key)
    def __getitem__ (self, key) :
        return getattr(self, key)
    def __iter__ (self) :
        for name in self._fields :
            yield name, self[name]
    def __repr__ (self) :
        return "\n".join(self._repr())
    def _repr (self, indent=0) :
        TAB = " |   " * indent
        if not self._fields :
            yield TAB + self.tag
        else :
            yield TAB + "%s :" % self.tag
            for name, child in self :
                if name.startswith("_") :
                    pass
                elif isinstance(child, node) :
                    for i, line in enumerate(child._repr(indent + 1)) :
                        if i == 0 :
                            yield TAB + " + %s = %s" % (name, line.lstrip(" |"))
                        else :
                            yield line
                elif isinstance(child, list) and child and isinstance(child[0], node) :
                    for n, c in enumerate(child) :
                        for i, line in enumerate(c._repr(1)) :
                            if i == 0 :
                                l = line.lstrip("| ")
                                yield TAB + " + %s[%s] = %s" % (name, n, l)
                            else :
                                yield TAB + line
                else :
                    yield TAB + " + %s = %r" % (name, child)

class Nest (object) :
    def __init__ (self, blocks) :
        self.pred = {}
        self.succ = {}
        self.rep = {}
        self.opt = {}
        self.first = {}
        self.last = {}
        for spec in blocks :
            _spec = []
            first = True
            for name in spec :
                _name = name.lstrip("*?")
                self.rep[_name] = name.startswith("*") or name.startswith("+")
                self.opt[_name] = name.startswith("?") or name.startswith("*")
                self.succ[_name] = set()
                self.pred[_name] = set()
                _spec.append(_name)
                self.first[_name] = first
                first = first and self.opt[_name]
            last = True
            for name in reversed(_spec) :
                self.last[name] = last
                last = last and self.opt[name]
            for one, two in zip(_spec, _spec[1:]) :
                if self.rep[two] :
                    self.pred[two].update({one, two} | self.pred[one])
                elif self.opt[two] :
                    self.pred[two].update({one} | self.pred[one])
                else :
                    self.pred[two].add(one)
        for two, preds in self.pred.items() :
            for one in preds :
                self.succ[one].add(two)

class MetaParser (fastidious.Parser) :
    __compound__ = []
    __default__ = "INPUT"
    __grammar__ = r"""
    INPUT     <- NL? :model {@model}
    NL        <- ~"([\t ]*(#.*)?\n)+" {_drop}
    _         <- ~"[\t ]+"? {_drop}
    COLON     <- _ ":" _ {_drop}
    COMMA     <- _ "," _ {p_flatten}
    AT        <- _ "@" _ {p_flatten}
    EQ        <- _ "=" _ {p_flatten}
    LP        <- _ "(" _ {p_flatten}
    RP        <- _ ")" _ {p_flatten}
    LSB       <- _ "[" _ {p_flatten}
    RSB       <- _ "]" _ {p_flatten}
    LCB       <- _ "{" _ {p_flatten}
    RCB       <- _ "}" _ {p_flatten}
    INDENT    <- _ "↦" NL? _ {_drop}
    DEDENT    <- _ "↤" NL? _ {_drop}
    NUMBER    <- _ ~"[+-]?[0-9]+" {_number}
    NAME      <- _ ~"[a-z][a-z0-9_]*"i _ {p_flatten}
    atom      <- :name / num:NUMBER / :code / :string {_first}
    name      <- name:NAME {_name}
    code      <- codec / codeb {_code}
    codec     <- LCB (~"([^{}\\\\]|[{}])+" / codec)* RCB {p_flatten}
    codeb     <- LSB (~"([^\\[\\]\\\\]|[\\[\\]])+" / codeb)* RSB {p_flatten}
    string    <- _ ( ~"'{3}.*?'{3}"s
                   / ~'"{3}.*?"{3}'s
                   / ~"'([^'\\\\]|\\.)*'"
                   / ~'"([^"\\\\]|\\.)*"' ) _ {_string}
    """
    def _drop (self, match) :
        return ""
    def _number (self, match) :
        return node("const", value=int(self.p_flatten(match)), type="int")
    def _name (self, match, name) :
        return node("const", value=name, type="name")
    def _code (self, match) :
        return node("const", value=self.p_flatten(match).strip()[1:-1], type="code")
    def _string (self, match) :
        return node("const", value=ast.literal_eval(self.p_flatten(match).strip()),
                    type="str")
    def _tuple (self, match) :
        lst = []
        for m in match :
            if isinstance(m, list) :
                lst.extend(i[1] for i in m)
            else :
                lst.append(m)
        return tuple(lst)
    def _first (self, match, **args) :
        for k, v in args.items() :
            if v is not self.NoMatch :
                if isinstance(v, node) :
                    return v
                else :
                    return node(k, value=v)
        return self.NoMatch
    __grammar__ += r"""
    model   <- stmt:stmt+
    stmt    <- :call / :block {_first}
    call    <- name:NAME :args NL
    args    <- LP ( pos:posargs
                  / kw:kwargs
                  / pos:posargs COMMA kw:kwargs )? RP
    posargs <- atom (COMMA atom)* {_tuple}
    kwargs  <- kwa (COMMA kwa) {_tuple}
    kwa     <- name:NAME "EQ" :atom
    block   <- deco:deco? name:NAME args:args? COLON NL INDENT stmt:stmt+ DEDENT
    deco    <- AT name:NAME args:args? NL
    """
    def _glue (self, stmt) :
        n = self.nest
        s = []
        l = None
        for child in stmt :
            if child.tag == "call" :
                s.append(child)
                l = None
            elif n.pred[child.tag] :
                if l in n.pred[child.tag] :
                    s[-1][child.tag] = child
                elif l and n.last[l] and n.first[child.tag] :
                    l = child.tag
                    s.append(child)
                elif l :
                    self.p_parse_error("invalid block %r after %r" % (child.tag, l),
                                       child._pos)
                else :
                    self.p_parse_error("unexpected block %r" % child.tag,
                                       child._pos)
            else :
                if l and not n.last[l] :
                    self.p_parse_error("invalid block %r after %r" % (child.tag, l),
                                       child._pos)
                if not n.first[child.tag] :
                    self.p_parse_error("unexpected block %r" % child.tag,
                                       child._pos)
                l = child.tag
                s.append(child)
        return s
    def on_model (self, match, stmt) :
        return node("model", body=self._glue(stmt), _pos=self.pos)
    def on_call (self, match, name, args) :
        return node("call", name=name, largs=args.l, kargs=args.k, _pos=self.pos)
    def on_args (self, match, pos=None, kw=None) :
        if pos is self.NoMatch or not pos :
            pos = []
        if kw is self.NoMatch or not kw :
            kw = {}
        return node("args", l=list(pos), k=dict(kw))
    def on_kwa (self, name, atom) :
        return name, atom
    def on_block (self, match, name, stmt, args=None, deco=None) :
        if args is self.NoMatch or not args :
            args = None
        if deco is self.NoMatch or not deco :
            deco = None
        return node(name, body=self._glue(stmt), args=args, deco=deco, _pos=self.pos)
    def on_deco (self, match, name, args=[]) :
        return node("deco", name=name, args=args)
    def __INIT__ (self) :
        self.nest = Nest(self.__compound__)
