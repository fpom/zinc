import ast, collections

from snakes import nets, ParseError, SNAKESError
from snakes.io import snkparse
from snakes.data import flatten

class Parser (object) :
    def __init__ (self, module=nets) :
        self.n = module
        self.p = snkparse.snkParser()
    def parse (self, source, path) :
        self._s = source
        self._p = path
        self._l = {}
        return self.p.parse(source, "spec", semantics=self)
    def spec (self, st) :
        try :
            net = self.n.PetriNet(st.net, st.lang)
        except SNAKESError as err :
            raise ParseError(str(err), None, None, self._p)
        for decl in st.declare :
            net.declare(decl)
        for node in st.nodes :
            if isinstance(node, self.n.Place) :
                net.add_place(node)
            else :
                trans, inputs, outputs = node
                net.add_transition(trans)
                for place, label in inputs.items() :
                    try :
                        if len(label) == 1 :
                            net.add_input(place, trans.name, label[0])
                        else :
                            net.add_input(place, trans.name, self.n.MultiArc(*label))
                    except SNAKESError as err :
                        raise ParseError(err, self._l[place, trans.name], None, self._p)
                for place, label in outputs.items() :
                    try :
                        if len(label) == 1 :
                            net.add_output(place, trans.name, label[0])
                        else :
                            net.add_output(place, trans.name, self.n.MultiArc(*label))
                    except SNAKESError as err :
                        raise ParseError(err, self._l[trans.name, place], None, self._p)
        return net
    def decl (self, st) :
        return st.source
    def place (self, st) :
        return self.n.Place(st.name, (st.tokens or [])[::2], st.type)
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
        return self.n.Transition(st.name, st.guard.strip()), inputs, outputs
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
            for k, l in zip(kind, label) :
                if k in _arc :
                    yield _arc[k](l)
                else :
                    yield self.n.Tuple(*mktuple(k, l))
        if st.tuple :
            label = self.n.Tuple(*mktuple(st.tuple, st.label))
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
    def tuple (self, st) :
        return tuple(st[1][::2])
    def code (self, st) :
        return self._s[st.parseinfo.pos:st.parseinfo.endpos]
    def string (self, st) :
        return "".join(flatten(st))
    def text (self, st) :
        if st.name :
            return st.name
        elif st.string :
            return ast.literal_eval(st.string)
        elif st.code :
            return st.code

def loads (source, module=nets) :
    return Parser(module).parse(source, "<string>")

def load (stream, module=nets) :
    return Parser(module).parse(stream.read(), getattr(stream, "name", "<string>"))

if __name__ == "__main__" :
    import sys
    net = Parser().parse(sys.argv[-1])
    print(repr(net))
    for place in net.place() :
        print(place)
    for trans in net.transition() :
        print(trans)
        for place, label in trans.input() :
            print("<", place.name, label)
        for place, label in trans.output() :
            print(">", place.name, label)
