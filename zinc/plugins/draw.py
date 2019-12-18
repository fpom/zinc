from . import Plugin
plug = Plugin("zinc.nets")

import subprocess, tempfile, json, io, ast, pathlib

class GV (object) :
    _arrowhead = {
        "Fill" : "diamond",
        "Flush" : "diamond",
        "Inhibitor" : "odot",
        "Test" : "none",
    }
    def __init__ (self) :
        self.graph = {"splines" : True}
        self.nodes = {}
        self.edges = {}
        self.nid = {}
    def __getitem__ (self, node) :
        return tuple(ast.literal_eval(c) for c in self.nodes[node]["pos"].split(","))
    def __setitem__ (self, node, pos) :
        x, y = pos
        self.nodes[node]["pos"] = "%s,%s" % pos
    @classmethod
    def from_net (cls, net,
                  net_attr=None, place_attr=None, trans_attr=None, arc_attr=None) :
        self = cls()
        if net_attr is not None :
            net_attr(net, self.graph)
        self.graph = {"splines" : True}
        if net_attr is not None :
            net_attr(net, self.graph)
        self.nodes = {}
        self.edges = {}
        self.nid = {}
        for place in net.place() :
            attr = {"label" : "%s\n%s" % (place, place.tokens),
                    "shape" : "circle"}
            if place_attr is not None :
                place_attr(place, attr)
            nid = self.nid[place.name] = len(self.nid)
            self.nodes[nid] = attr
        for trans in net.transition() :
            attr = {"label" : "%s\n%s" % (trans, trans.guard),
                    "shape" : "rectangle"}
            if trans_attr is not None :
                trans_attr(trans, attr)
            nid = self.nid[place.name] = len(self.nid)
            self.nodes[nid] = attr
            for place, label in trans.input() :
                attr = {"label" : str(label),
                        "arrowhead" : self._arrowhead.get(label.__class__.__name__,
                                                          "normal")}
                if arc_attr is not None :
                    arc_attr(label, attr)
                self.edges[self.nid[place], nid] = attr
            for place, label in trans.output() :
                attr = {"label" : str(label),
                        "arrowhead" : self._arrowhead.get(label.__class__.__name__,
                                                          "normal")}
                if arc_attr is not None :
                    arc_attr(label, attr)
                self.edges[nid, self.nid[place]] = attr
        return self
    def write (self, stream, data=True) :
        stream.write("digraph {\n")
        for node, attr in self.nodes.items() :
            stream.write("  %s [\n" % node)
            for key, val in attr.items() :
                stream.write('    %s = "%s"\n' % (key, str(val).replace('"', r'\"')))
            stream.write("  ];\n")
        for edge, attr in self.edges.items() :
            stream.write("  %s -> %s [\n" % edge)
            for key, val in attr.items() :
                stream.write('    %s = "%s"\n' % (key, str(val).replace('"', r'\"')))
            stream.write("  ];\n")
        stream.write("}\n")
    @classmethod
    def read_json (cls, stream) :
        self = cls()
        for key, val in json.load(stream).items() :
            if key == "objects" :
                for node in val :
                    self.nodes[node.pop("_gvid")] = node
            elif key == "edges" :
                for edge in val :
                    self.edges[edge.pop("head"),edge.pop("tail")] = edge
            else :
                self.graph[key] = val
        return self
    @classmethod
    def read (cls, stream) :
        with tempfile.NamedTemporaryFile(mode="w") as dot :
            dot.write(stream.read())
            dot.flush()
            out = subprocess.check_output(["dot", "-Tdot_json", "-q",
                                           "-Kneato", "-n2",
                                           dot.name], encoding="utf-8")
        return cls.read_json(io.StringIO(out))
    def dot (self, engine="dot", scale=72.0, landscape=False) :
        with tempfile.NamedTemporaryFile(mode="w") as dot :
            self.write(dot)
            dot.flush()
            out = subprocess.check_output(["dot", "-Tdot_json", "-q",
                                           "-K%s" % engine,
                                           "-s%s" % scale]
                                          + (["-y"] if landscape else [])
                                          + [dot.name], encoding="utf-8")
        return self.read(io.StringIO(out))
    def draw (self, path, engine="dot", scale=72.0, landscape=False) :
        fmt = pathlib.Path(path).suffix.lstrip(".")
        with tempfile.NamedTemporaryFile(mode="w") as dot :
            self.write(dot)
            dot.flush()
            subprocess.check_call(["dot", "-q",
                                   "-T%s" % fmt,
                                   "-K%s" % engine,
                                   "-s%s" % scale,
                                   "-o%s" % path]
                                  + (["-y"] if landscape else [])
                                  + [dot.name])

@plug
class PetriNet (plug.PetriNet) :
    def draw (self, path, engine="dot",
              graph_attr=None, place_attr=None, trans_attr=None, arc_attr=None) :
        pass
