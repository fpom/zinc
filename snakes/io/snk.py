import ast, collections

from snakes import nets, ParseError, SNAKESError
from snakes.io import snkparse
from snakes.data import flatten

class TupleParser (object) :
    def __init__ (self) :
        self.p = snkparse.snkParser()
    def parse (self, source) :
        return self.p.parse(source, "tailtuple", semantics=self)
    def tuple (self, st) :
        def _tuple (l) :
            if isinstance(l, list) :
                return tuple(_tuple(x) for x in l)
            else :
                return l
        return _tuple(st[1][::2])
    def tailtuple (self, st) :
        return st
    def code (self, st) :
        return "".join(flatten(st))[1:-1].strip()
    def string (self, st) :
        return "".join(flatten(st))
    def text (self, st) :
        if st.name :
            return st.name
        elif st.string :
            return ast.literal_eval(st.string)
        elif st.code :
            return st.code

class Parser (TupleParser) :
    def __init__ (self, module=nets) :
        self.n = module
        self.p = snkparse.snkParser()
        self.t = TupleParser()
    def parse (self, source, path) :
        self._s = source.rstrip() + "\n"
        self._p = path
        self._l = {}
        return self.p.parse(self._s, "spec", semantics=self)
    def spec (self, st) :
        try :
            net = self.n.PetriNet(st.net, st.lang)
        except SNAKESError as err :
            raise ParseError(str(err), None, None, self._p)
        for decl in st.declare :
            net.declare(decl)
        for node, *rest in st.nodes :
            if isinstance(node, self.n.Place) :
                try :
                    net.add_place(node)
                except SNAKESError as err :
                    raise ParseError(err, rest[0], None, self._p)
            else :
                lineno, inputs, outputs = rest
                try :
                    net.add_transition(node)
                except SNAKESError as err :
                    raise ParseError(err, lineno, None, self._p)
                for place, label in inputs.items() :
                    try :
                        if len(label) == 1 :
                            net.add_input(place, node.name, label[0])
                        else :
                            net.add_input(place, node.name, self.n.MultiArc(*label))
                    except SNAKESError as err :
                        raise ParseError(err, self._l[place, node.name], None, self._p)
                for place, label in outputs.items() :
                    try :
                        if len(label) == 1 :
                            net.add_output(place, node.name, label[0])
                        else :
                            net.add_output(place, node.name, self.n.MultiArc(*label))
                    except SNAKESError as err :
                        raise ParseError(err, self._l[node.name, place], None, self._p)
        return net
    def decl (self, st) :
        return st.source
    def place (self, st) :
        return (self.n.Place(st.name, (st.tokens or [])[::2], st.type),
                st.parseinfo.line+1)
    def placetype (self, st) :
        if st.text :
            return st.text
        elif st.tuple :
            return st.tuple
    def placetuple (self, st) :
        def mktuple (content) :
            if isinstance(content, list) :
                return tuple(mktuple(c) for c in content[1][::2])
            else :
                return content
        return mktuple(st)
    def token (self, st) :
        if st.number :
            return self.n.Token(st.number)
        elif st.text :
            return self.n.Token(st.text)
    def trans (self, st) :
        inputs, outputs = collections.defaultdict(list), collections.defaultdict(list)
        for isin, place, label, lineno in st.arcs :
            if isin :
                inputs[place].append(label)
                self._l[place, st.name] = lineno
            else :
                outputs[place].append(label)
                self._l[st.name, place] = lineno
        return (self.n.Transition(st.name, st.guard.strip()),
                st.parseinfo.line+1, inputs, outputs)
    def guard (self, st) :
        if st.text :
            return st.text
        elif st.raw :
            return st.raw
    def _mkarc (self, st) :
        _arc = {"val" : self.n.Value,
                "var" : self.n.Variable,
                "expr" : self.n.Expression,
                "flush" : self.n.Flush,
                "fill" : self.n.Fill}
        def mktuple (kind, label) :
            if isinstance(kind, tuple) :
                if not (isinstance(label, tuple) and len(kind) == len(label)) :
                    raise ParseError("unmatched tuples %r and %r" % (kind, label),
                                     st.parseinfo.line+1, None, self._p)
                return self.n.Tuple(*(mktuple(k, l) for k, l in zip(kind, label)))
            else :
                return _arc[kind](label)
        if isinstance(st.kind, tuple) :
            try :
                lbl = self.t.parse(st.label)
            except Exception as err :
                raise ParseError(str(err), st.parseinfo.line+1, None, self._p)
            label = mktuple(st.kind, lbl)
        elif st.kind in _arc :
            label = _arc[st.kind](st.label.strip())
        if st.mod :
            if st.mod.kind == "?" :
                label = self.n.Test(label)
            elif st.mod.kind == "!" :
                label = self.n.Inhibitor(label, st.mod.guard)
        return st.way == "<", st.place, label, st.parseinfo.line+1
    def arc (self, st) :
        try :
            return self._mkarc(st)
        except SNAKESError as err :
            raise ParseError(str(err), st.parseinfo.line+1, None, self._p)

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
