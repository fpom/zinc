from snakes.data import hashable, mutation
from snakes.compil import ast

class Token (object) :
    def __init__ (self, code) :
        self.code = code.strip()
    def __ast__ (self, place) :
        return ast.SourceExpr(self.code,
                              BLAME=ast.TokenBlame(place, self.code))
    def __str__ (self) :
        return "(%s)" % self.code
    def __repr__ (self) :
        return "%s(%r)" % (self.__class__.__name__, self.code)
    def __hash__ (self) :
        return hash(self.code)
    def __eq__ (self, other) :
        try :
            return self.code == other.code
        except AttributeError :
            return False
    def __ne__ (self, other) :
        try :
            return self.code != other.code
        except AttributeError :
            return True
    def __ge__ (self, other) :
        try :
            return self.code >= other.code
        except AttributeError :
            return False
    def __gt__ (self, other) :
        try :
            return self.code >= other.code
        except AttributeError :
            return False
    def __le__ (self, other) :
        return not self.__gt__(other)
    def __lt__ (self, other) :
        return not self.__ge__(other)

class BlackToken (Token) :
    def __init__ (self) :
        pass
    def __str__ (self) :
        return "dot"
    def __repr__ (self) :
        return "%s()" % self.__class__.__name__
    def __new__ (cls) :
        if not hasattr(cls, "dot") :
            cls.dot = object.__new__(cls)
        return cls.dot
    def __hash__ (self) :
        return hash(self.__class__.__name__)

dot = BlackToken()

@hashable
class Marking (dict) :
    def _hash_items (self) :
        return self.items()
    def __call__ (self, place) :
        return self.get(place, mset())
    def copy (self) :
        return self.__class__((k, v.copy()) for k, v in self.items())
    def __add__ (self, other) :
        new = self.copy()
        for k, v in other.items() :
            if k not in new :
                new[k] = v
            else :
                new[k].add(v)
        return new
    def __sub__ (self, other) :
        new = self.copy()
        for k, v in other.items() :
            if new[k] == v :
                del new[k]
            else :
                new[k] -= v
        return new
    def __le__ (self, other) :
        return all(self(k) <= other(k) for k in self.keys())
    def __lt__ (self, other) :
        return (self != other) and (self <= other)
    def __ge__ (self, other) :
        return all(self(k) >= other(k) for k in other.keys())
    def __gt__ (self, other) :
        return (self != other) and (self >= other)
    def __ast__ (self) :
        m = {}
        for place, tokens in self.items() :
            if tokens :
                m[place] = [t.__ast__(place) for t in tokens]
        return ast.NewMarking([
            ast.NewPlaceMarking(place, tokens, BLAME=ast.PlaceBlame(place, tokens))
            for place, tokens in m.items()])

