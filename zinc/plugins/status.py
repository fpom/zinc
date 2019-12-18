from . import Plugin
plug = Plugin("zinc.nets")

import collections

from ..data import iterate

@plug
class Status (object) :
    def __init__ (self, kind, name=None) :
        self.kind = kind
        self.name = name
    def __eq__ (self, other) :
        try :
            return self.kind == other.kind and self.name == other.name
        except :
            return False
    def __hash__ (self) :
        return hash((self.__class__.__name__, self.kind, self.name))
    def __str__ (self) :
        if self.name :
            return "%s[%s]" % (self.kind, self.name)
        else :
            return self.kind
    def __repr__ (self) :
        if self.name :
            return "%s(%r, %r)" % (self.kind, self.name)
        else :
            return "%s(%r)" % self.kind
    def copy (self) :
        return self.__class__(self.kind, self.name)
    def named (self) :
        return not self.is_flow() and self.name is not None
    def is_flow (self) :
        return self.name in ("entry", "internal", "exit")

for name in ("entry", "internal", "exit") :
    setattr(Status, name, Status(name))

@plug
class Place (plug.Place) :
    def __init__ (self, name, tokens=[], type=None, **options) :
        self.status = self.options.pop("status", Status(None))
        super().__init__(name, tokens, type, **options)
    def copy (self, name=None, **options) :
        result = super().copy(name, **options)
        result.status = self.status.copy()
        return result
    def __repr__ (self) :
        if self.status.kind is None :
            return super().__repr__()
        else :
            return "%s, status=%s)" % (super().__repr__()[:-1], repr(self.status))

@plug
class PetriNet (plug.PetriNet) :
    def __init__ (self, name, lang="python", **options) :
        super().__init__(name, lang, **options)
        self.status = collections.defaultdict(set)
    def add_place (self, place, **options) :
        super().__init__(place, **options)
        self.status[place.status].add(place.name)
    def remove_place (self, name, **options) :
        place = self.place(name)
        super().remove_place(name, **options)
        self.status[place.status].remove(name)
    def _status_copy (self, net, rename) :
        self.declare.update(net.declare)
        for place in net.place() :
            self.add_place(place.copy(rename(place.name)))
        for trans in net.transition() :
            self.add_transition(trans.copy(rename(trans.name)))
            for place, label in trans.input() :
                self.add_input(rename(place), rename(trans.name), label)
            for place, label in trans.output() :
                self.add_output(rename(place), rename(trans.name), label)
    def __div__ (self, other) :
        # buffer hiding
        op = ",".join(other)
        def rename (n) :
            return "[%s/%s]" (n, op)
        net = self.__class__(rename(self.name), self.lang.name)
        net._status_copy(self, rename)
        hidden = Status("buffer", None)
        for buff in iterate(other) :
            status = Status("buffer", buff)
            places = net.status.pop(status, [])
            for name in places :
                place = net.place(name)
                place.status = hidden
                net.status[hidden].add(name)
        return net
