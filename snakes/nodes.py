from snakes.data import mset, record

class Node (object) :
    pass

class Place (Node) :
    def __init__ (self, name, tokens=[], props={}) :
        self.name = name
        self.tokens = mset(tokens)
        self.props = record(props)
    def __iter__ (self) :
        return iter(self.tokens)
    def is_empty (self) :
        return bool(self.tokens)

class Transition (Node) :
    def __init__ (self, name, guard=None) :
        self.name = name
        self.guard = guard
        self._input = {}
        self._output = {}
    def add_input (self, place, label) :
        self._input[place] = label
    def add_output (self, place, label) :
        self._output[place] = label
    def input (self) :
        return self._input.items()
    def output (self) :
        return self._output.items()
