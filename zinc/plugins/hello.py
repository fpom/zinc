"""An example plugin that allows instances of `PetriNet` to say hello.

The source code can be used as a starting example:
1. Import `zinc.plugins.Plugin`
2. Create an instance of it, passing:
    * the modules that are extended
    * the conflicts (if any)
    * the dependencies (if any)
3. This instance will serve as:
    * a decorator for each class or function that should be included
      in the extended module
    * classes or functions to extend are retreived as its attributes
"""

from . import Plugin
plug = Plugin("zinc.nets")

@plug
class PetriNet (plug.PetriNet) :
    def hello (self, name="world") :
        print("hello %s from %s" % (name, self.name))
