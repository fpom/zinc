from . import Plugin
plug = Plugin("zinc.nets",
              depends=["zinc.plugins.status"])

from .. import ConstraintError
from itertools import product

@plug
class Place (plug.Place) :
    def __init__ (self, name, tokens=[], type=None, **options) :
        status = self.options.pop("status", self.__plugmod__.Status(None))
        if status.is_flow() :
            if type is None :
                type = self.__plugmod__.BlackToken
            if type is not self.__plugmod__.BlackToken :
                raise ConstraintError("invalid type for control-flow place: %r" % type)
        super().__init__(name, tokens, type, status=status, **options)

@plug
class PetriNet (plug.PetriNet) :
    def _flow_glue (self, other, op) :
        if self.land.name != other.lang.name :
            raise ConstraintError("cannot combine nets with different languages")
        net = self.__class__("[%s%s%s]" % (self.name, op, other.name), self.lang.name)
        def rename (n) :
            return "[%s%s]" % (n, op)
        for child in (self, other) :
            net._status_copy(child, rename)
            def rename (n) :
                return "[%s%s]" % (op, n)
        for status, places in net.status.items() :
            if status.named() and len(places) > 1 :
                self.merge_places("[%s]" % op.join(places), places)
                for p in places :
                    self.remove_place(p)
        return net
    def __or__ (self, other) :
        # parallel
        return self._flow_glue(other, "|")
    def __and__ (self, other) :
        # sequence
        net = self._flow_glue(other, "&")
        X1 = self.status[self.__plugmod__.exit]
        E2 = other.status[self.__plugmod__.entry]
        for x, e in product(X1, E2) :
            net.merge_places("[%s&%s]" % (x.name, e.name),
                             ["[%s&]" % x.name, "[&%s]" % e.name])
        for x in X1 :
            net.remove_place("[%s&]" % x)
        for e in E2 :
            net.remove_place("[&%s]" % e)
        return net
    def __add__ (self, other) :
        # choice
        net = self._flow_glue(other, "+")
        E1 = self.status[self.__plugmod__.entry]
        X1 = self.status[self.__plugmod__.exit]
        E2 = other.status[self.__plugmod__.entry]
        X2 = other.status[self.__plugmod__.exit]
        for e1, e2 in product(E1, E2) :
            net.merge_places("[%s&%s]" % (e1.name, e2.name),
                             ["[%s&]" % e1.name, "[&%s]" % e2.name])
        for x1, x2 in product(X1, X2) :
            net.merge_places("[%s&%s]" % (x1.name, x2.name),
                             ["[%s&]" % x1.name, "[&%s]" % x2.name])
        for p in X1 | E1 :
            net.remove_place("[%s&]" % p)
        for p in X2 | E2 :
            net.remove_place("[&%s]" % p)
        return net
    def __mul__ (self, other) :
        # iteration
        net = self._flow_glue(other, "*")
        E1 = self.status[self.__plugmod__.entry]
        X1 = self.status[self.__plugmod__.exit]
        E2 = other.status[self.__plugmod__.entry]
        for e1, x1, e2 in product(E1, X1, E2) :
            net.merge_places("[%s*%s*%s]" % (e1.name, x1.name, e2.name),
                             ["[%s*]" % e1.name, "[%s*]" % x1.name, "[*%s]" % e2.name])
        for p in X1 | E1 :
            net.remove_place("[%s*]" % p)
        for p in E2 :
            net.remove_place("[*%s]" % p)
        return net
