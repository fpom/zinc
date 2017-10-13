import ast, collections
from snakes.tokens import Marking, mset

def load_state (text) :
    return Marking({p : mset(t) for p, t in ast.literal_eval(text).items()})

def load (infile) :
    g = {}
    last = None
    for line in infile :
        try :
            head, text = line.split(None, 1)
        except :
            raise ValueError("invalid line %r" % line)
        state = load_state(text)
        if head == "INIT" :
            g[0] = state
        elif head.startswith("[") :
            if state in g :
                print("duplicate state", state)
            else :
                g[state] = set()
            last = state
        elif head == ">>>" :
            if state in g[last] :
                print("duplicate succ", state)
            g[last].add(state)
        else :
            raise ValueError("invalid line %r" % line)
    return g

def compare (left, right) :
    if left[0] != right[0] :
        print("not same initial state:")
        print(" ", left[0])
        print(" ", right[0])
        return
    print("let's go (%s states vs %s)" % (len(left) - 1, len(right) - 1))
    todo = collections.deque([left[0]])
    seen = set(todo)
    while todo :
        state = todo.popleft()
        todo.extend(left[state] - seen)
        seen.update(left[state])
        if state not in right :
            print("missing", state)
            return
        elif left[state] != right[state] :
            print("not same successors for", state)
            for s in left[state] - right[state] :
                print(" -", s)
            for s in right[state] - left[state] :
                print(" +", s)
            return
    print("no difference found")

if __name__ == "__main__" :
    import sys
    print("loading %r and %r..." % tuple(sys.argv[-2:]))
    compare(load(open(sys.argv[-2])), load(open(sys.argv[-1])))
