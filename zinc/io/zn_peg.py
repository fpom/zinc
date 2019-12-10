# coding: utf-8

from .. import ZINCError
import ast, collections, functools
import fastidious

class ZnParser (fastidious.Parser) :
    __default__ = "INPUT"
    __grammar__ = r"""
    INPUT     <- NL? :spec {@spec}
    NL        <- ~"([\t ]*(#.*)?\n)+" {_drop}
    _         <- ~"[\t ]+"? {_drop}
    TAIL      <- ~".+" {p_flatten}
    COLON     <- _ ":" _ {_drop}
    COMMA     <- _ "," _ {p_flatten}
    AT        <- _ "@" _ {p_flatten}
    EQ        <- _ "=" _ {p_flatten}
    LT        <- _ "<" _ {p_flatten}
    GT        <- _ ">" _ {p_flatten}
    LP        <- _ "(" _ {p_flatten}
    RP        <- _ ")" _ {p_flatten}
    LSB       <- _ "[" _ {p_flatten}
    RSB       <- _ "]" _ {p_flatten}
    LCB       <- _ "{" _ {p_flatten}
    RCB       <- _ "}" _ {p_flatten}
    INDENT    <- _ "↦" NL? _ {_drop}
    DEDENT    <- _ "↤" NL? _ {_drop}
    LANG      <- _ "lang" _ {p_flatten}
    NET       <- _ "net" _ {p_flatten}
    PLACE     <- _ "place" _ {p_flatten}
    TRANS     <- _ "trans" _ {p_flatten}
    VAL       <- _ "val" _ {p_flatten}
    VAR       <- _ "var" _ {p_flatten}
    EXPR      <- _ "expr" _ {p_flatten}
    DECLARE   <- _ "declare" _ {p_flatten}
    FLUSHPLUS <- _ "flush+" _ {p_flatten}
    FLUSH     <- _ "flush" _ {p_flatten}
    FILL      <- _ "fill" _ {p_flatten}
    TEST      <- _ "?" _ {p_flatten}
    BANG      <- _ "!" _ {p_flatten}
    NUMBER    <- _ ~"[+-]?[0-9]+" {_number}
    NAME      <- _ ~"[a-z][a-z0-9_]*"i _ {p_flatten}
    text     <- name:NAME / :code / :string {_first}
    code     <-  codec / codeb {_code}
    codec    <- LCB (~"([^{}\\\\]|\\[{}])+" / codec)* RCB {p_flatten}
    codeb    <- LSB (~"([^\\[\\]\\\\]|\\[\\[\\]])+" / codeb)* RSB {p_flatten}
    string   <- _ ( ~"'{3}.*?'{3}"s
                  / ~'"{3}.*?"{3}'s
                  / ~"'([^'\\\\]|\\.)*'"
                  / ~'"([^"\\\\]|\\.)*"' ) _ {_string}
    """
    def _drop (self, match) :
        return ""
    def _number (self, match) :
        return int(self.p_flatten(match))
    def _code (self, match) :
        return (self.p_flatten(match).strip()[1:-1])
    def _string (self, match) :
        return ast.literal_eval(self.p_flatten(match).strip())
    def _tuple (self, match) :
        """callback to transform matched comma-separated tuples
        <- item (COMMA item)*
        => (item, ...)
        """
        lst = []
        for m in match :
            if isinstance(m, list) :
                lst.extend(i[1] for i in m)
            else :
                lst.append(m)
        return tuple(lst)
    def _tuple1 (self, match) :
        """callback to transform matched comma-separated tuples
        <- DELIM item (COMMA item)* DELIM
        => (item, ...)
        """
        lst = []
        for m in match[1:-1] :
            if isinstance(m, list) :
                lst.extend(i[1] for i in m)
            else :
                lst.append(m)
        return tuple(lst)
    def _first (self, match, **args) :
        for k, v in args.items() :
            if v is not self.NoMatch :
                return v
        return self.NoMatch
    __grammar__ += r"""
    spec <- LANG lang:text NL
            declare:decl*
            NET net:text COLON NL INDENT nodes:(place / trans)+ DEDENT
    """
    def on_spec (self, match, lang, declare, net, nodes) :
        try :
            net = self.n.PetriNet(net, lang)
        except ZINCError as err :
            self.p_parse_error(str(err))
        for lvl, decl in declare :
            net.declare(decl, lvl)
        for pos, node, *rest in nodes :
            if isinstance(node, self.n.Place) :
                try :
                    net.add_place(node)
                except ZINCError as err :
                    self.p_parse_error(str(err), pos)
            else :
                try :
                    net.add_transition(node)
                except ZINCError as err :
                    self.p_parse_error(str(err), pos)
                for arcs, add in zip(rest, (net.add_input, net.add_output)) :
                    for place, arc in arcs.items() :
                        try :
                            pos, label = arc[0]
                            if len(arc) == 1 :
                                add(place, node.name, label)
                            else :
                                add(place, node.name,
                                    self.n.MultiArc(*(lbl for _, lbl in arc)))
                        except ZINCError as err :
                            self.p_parse_error(str(err), pos)
        return net
    __grammar__ += r"""
    decl <- DECLARE (AT level:text)? source:text NL
    """
    def on_decl (self, match, source, level=None) :
        return level, source
    __grammar__ += r"""
    place      <- PLACE name:text type:placetype? (EQ tokens:tokens)? NL
    placetype  <- :text / :placetuple {_first}
    placetuple <- LP placeitem (COMMA placeitem)* RP {_tuple1}
    placeitem  <- :text / :placetuple {_first}
    tokens     <- tok (COMMA tok)* {_tuple}
    tok        <- number:NUMBER / :text {_first}
    """
    def on_place (self, match, name, type=None, tokens=[]) :
        return self.pos, self.n.Place(name, tokens, type)
    __grammar__ += r"""
    trans      <- TRANS name:text guard:(~"[^:]+")? COLON NL INDENT arcs:arc+ DEDENT
    arc        <- way:(LT / GT) place:text mod:arcmod? kind:arckind EQ label:TAIL NL
    arckind    <- VAL / VAR / EXPR / FLUSHPLUS / FLUSH / FILL / arctuple
    arcmod     <- kind:(TEST / BANG) guard:code?
    arctuple <- LP arcitem (COMMA arcitem)* RP {_tuple1}
    arcitem  <- :text / number:NUMBER / :arctuple {_first}
    """
    def on_trans (self, match, name, arcs, guard=None) :
        inputs, outputs = collections.defaultdict(list), collections.defaultdict(list)
        for pos, isin, place, label in arcs :
            if isin :
                inputs[place].append((pos, label))
            else :
                outputs[place].append((pos, label))
        return self.pos, self.n.Transition(name, guard), inputs, outputs
    def on_arc (self, match, way, place, kind, label, mod=None) :
        return self.pos, way == "<", place, self._mkarc(kind, label, mod)
    def _mkarc (self, kind, label, mod) :
        _arc = {"val" : self.n.Value,
                "var" : self.n.Variable,
                "expr" : self.n.Expression,
                "flush" : self.n.Flush,
                "flush+" : functools.partial(self.n.Flush, notempty=True),
                "fill" : self.n.Fill}
        def mktuple (kind, label) :
            if not isinstance(label, tuple) or len(kind) != len(label) :
                self.p_parse_error("unmatched tuples %r and %r" % (kind, label))
            return self.n.Tuple(*(mktuple(k, l) for k, l in zip(kind, label)))
        if isinstance(kind, tuple) :
            lbl = self.p_parse(label, "arctuple")
            label = mktuple(kind, lbl)
        elif kind in _arc :
            label = _arc[kind](label.strip())
        if mod :
            mod_kind, mod_guard = mod
            if mod_kind == "?" :
                label = self.n.Test(label)
            elif mod_kind == "!" :
                label = self.n.Inhibitor(label, mod_guard)
        return label

    def on_arcmod (self, match, kind, guard=None) :
        return kind, guard
