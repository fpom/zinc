from . import Plugin
plug = Plugin("zinc.nets")

import collections

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
