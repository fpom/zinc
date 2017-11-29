import os, os.path, subprocess, re

def walk (root='libs/js') :
    for dirpath, dirnames, filenames in os.walk(root) :
        for name in filenames :
            if name.endswith('.coffee') :
                yield os.path.relpath(os.path.join(dirpath, name), root)

class Test (object) :
    def __init__ (self, path, lineno, src, out) :
        self.path = path
        self.lineno = lineno
        self.src = src
        self.out = out
    @classmethod
    def require (cls, root, path) :
        base = os.path.splitext(path)[0]
        name = os.path.basename(base)
        full = os.path.join(".", root, base)
        return cls(path, 0, "%s = require %r" % (name, full), [])
    @classmethod
    def bunch (cls, root, path, bunch) :
        return [cls.require(root, path)] + bunch
    def codegen (self, out) :
        out.write("console.log '+++ %s:%s +++'\n" % (self.path, self.lineno))
        out.write(self.src + "\n")
        out.write("console.log '--- %s:%s ---'\n" % (self.path, self.lineno))
        if self.lineno > 0 :
            return "%s:%s" % (self.path, self.lineno)
    def _fail (self, out) :
        print("\n#### %s:%s" % (self.path, self.lineno))
        print("%s" % self.src)
        print("## expected:")
        print("\n".join(self.out))
        print("## obtained:")
        print("\n".join(out))
    def check (self, out) :
        if self.src.startswith and out and out[-1] == "undefined" :
            del out[-1]
        if out and out[0].startswith("[stdin]:") :
            self._fail(out)
            return False
        elif any("..." in s for s in self.out) :
            o = re.sub(r"\s", "", "".join(out))
            e = re.sub(r"\s", "", "".join(self.out))
            e = re.escape(e).replace(r"\.\.\.", ".*?")
            if re.match("^%s$" % e, o) :
                return True
            else :
                self._fail(out)
                return False
        elif not self.out or out == self.out :
            return True
        else :
            self._fail(out)
            return False

def extract (root, path) :
    bunch = []
    src = delim = None
    out = []
    for num, line in enumerate(open(os.path.join(root, path))) :
        stripped = line.strip()
        if stripped == delim :
            if src is not None :
                bunch.append(Test(path, *src, out))
                out, src = [], None
            if bunch :
                yield Test.bunch(root, path, bunch)
            delim = None
            bunch = []
        elif stripped in ("'''", '"""') :
            delim = stripped
        elif delim and stripped.startswith("coffee>") :
            if src is not None :
                bunch.append(Test(path, *src, out))
                out, src = [], None
            src = (num + 1, stripped[7:].strip())
        elif delim :
            out.append(stripped)
    if bunch :
        yield Test.bunch(root, path, bunch)

def codegen (tests, path) :
    d = {}
    with open(path, "w") as out :
        for t in tests :
            key = t.codegen(out)
            if key :
                d[key] = t
    return d

def run (src) :
    try :
        out = subprocess.check_output(["coffee", "-i"],
                                      stdin=open(src),
                                      stderr=subprocess.STDOUT)
        out = out.decode().splitlines()
    except subprocess.CalledProcessError as err :
        out = err.output.decode().splitlines()
    for line in out :
        while line.startswith("coffee> ") :
            line = line[8:]
        if line.strip() :
            yield line.rstrip()

def check_output (out, tests) :
    passed = failed = 0
    tid = None
    tout = []
    skip = False
    for line in out :
        if skip :
            skip = False
        elif line.startswith("+++") :
            tid = line.split()[1]
            tout = []
            skip = True
        elif line.startswith("---") :
            skip = True
            assert line.split()[1] == tid
            if tid not in tests :
                continue
            t = tests[tid]
            if t.check(tout) :
                passed += 1
            else :
                failed += 1
        else :
            tout.append(line)
    return passed, failed

if __name__ == "__main__" :
    root = "libs/js"
    passed, failed = 0, 0
    nl = False
    for path in walk(root) :
        base = os.path.basename(os.path.splitext(path)[0])
        for num, tests in enumerate(extract(root, path)) :
            if nl :
                print()
                nl = False
            print("+ %s: %s tests" % (os.path.join(root, path), len(tests) - 1))
            src = ",test-%s-%04u.coffee" % (base, num)
            tests = codegen(tests, src)
            out = run(src)
            p, f = check_output(out, tests)
            passed += p
            failed += f
            nl = f > 0
            os.unlink(src)
    if failed :
        print()
    print("= %s tests failed (out of %s)" % (failed, failed+passed))
