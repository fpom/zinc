from . import Plugin
plug = Plugin("zinc.nets",
              depends=["zinc.plugins.status"])

from .. import ConstraintError

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
    def __or__ (self, other) :
        # parallel
        pass
    def __and__ (self, other) :
        # sequence
        pass
    def __add__ (self, other) :
        # choice
        pass
    def __mul__ (self, other) :
        # iteration
        pass
    def __div__ (self, other) :
        # buffer hiding
        pass
