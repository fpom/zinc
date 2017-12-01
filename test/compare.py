import collections

from snakes.nets import Marking, mset, dot, hdict

event = collections.namedtuple("event", ["trans", "mode", "state"])

def dumps (obj) :
    if isinstance(obj, Marking) :
        if getattr(obj, "ident", None) is None :
            return "{%s}" % ", ".join("%s: %s" % (p, list(sorted(t)))
                                      for p, t in sorted(obj.items()))
        else :
            return "[%s] {%s}" % (obj.ident,
                                  ", ".join("%s: %s" % (p, list(sorted(t)))
                                            for p, t in sorted(obj.items())))
    elif isinstance(obj, event) :
        return "%s %s => %s" % (obj.trans, dumps(obj.mode), dumps(obj.state))
    elif isinstance(obj, dict) :
        return "{%s}" % ", ".join("%s: %s" % i for i in sorted(obj.items()))
    else :
        return str(obj)

def load_code (text) :
    return eval(text, {"dot": dot, "mset": mset})

def load_state (text, ident=None) :
    m = Marking({place : mset(dot if t == {} else t for t in tokens)
                 for place, tokens in load_code(text).items()})
    if ident is not None :
        m.ident = ident
    return m

def load (infile) :
    g = {}
    for line in infile :
        try :
            head, text = line.split(None, 1)
        except :
            raise ValueError("invalid line %r" % line)
        if head.startswith("[") :
            ident = int(head[1:-1])
            last = load_state(text, ident)
            if last in g :
                print("# duplicated state", dumps(last))
            else :
                g[last] = set()
            if ident == 0 :
                g[0] = last
        elif head == "@" :
            trans, _, text = text.split(None, 2)
            mode = hdict(load_code(text))
            for k, v in mode.items() :
                if isinstance(v, list) :
                    mode[k] = mset(v)
        elif head in "+-" :
            pass
        elif head == ">" :
            i, m = text.split(None, 1)
            g[last].add(event(trans, mode, load_state(m, int(i[1:-1]))))
        else :
            raise ValueError("invalid line %r" % line)
    return g

def diff (left, right) :
    if left[0] != right[0] :
        print("not same initial state:")
        print(" ", dumps(left[0]))
        print(" ", dumps(right[0]))
        return
    print("let's go (%s states vs %s)" % (len(left) - 1, len(right) - 1))
    todo = collections.deque([left[0]])
    seen = set(todo)
    while todo :
        state = todo.popleft()
        succs = set(e.state for e in left[state]) - seen
        todo.extend(succs)
        seen.update(succs)
        if state not in right :
            print("missing", dumps(state))
            return
        elif left[state] != right[state] :
            print("not same successors for [%s] %s" % (state.ident, dumps(state)))
            for s in left[state] - right[state] :
                print(" -", dumps(s))
            for s in right[state] - left[state] :
                print(" +", dumps(s))
            return
    print("no difference found")

def states (g) :
    d = {}
    for s in g :
        if isinstance(s, int) :
            continue
        d[dumps(s)] = s
    for k, s in sorted(d.items()) :
        print(dumps(s))

if __name__ == "__main__" :
    import sys
    print("loading %r and %r..." % tuple(sys.argv[-2:]))
    left = load(open(sys.argv[-2]))
    right = load(open(sys.argv[-1]))

