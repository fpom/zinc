import os, os.path, subprocess

def walk(root='libs/go/src/zn') :
    for dirpath, dirnames, filenames in os.walk(root) :
        for name in filenames :
            if name.endswith('.go') :
                yield os.path.relpath(os.path.join(dirpath, name), root)

class Test (object) :
    idx = {}
    def __init__ (self, path, lineno, source, expected=[]) :
        self.path = path
        self.lineno = lineno
        self.idx[path, lineno] = self
        self.source = source
        self.expected = list(expected)
        self.pychecks = []
    def codegen (self, outfile, indent="  ") :
        if self.path in self.idx :
            outfile.write('  ' + '\n  '.join(self.idx[self.path]) + '\n')
        outfile.write('  fmt.Println("### %s:%s")\n' % (self.path, self.lineno))
        if len(self.source) > 1 :
            outfile.write('  ' + '\n  '.join(self.source[:-1]) + '\n')
        outfile.write('  fmt.Println(%s)\n' % self.source[-1])
    def check (self, output) :
        if self.source[-1] == "nil" and output[-1] == "<nil>" :
            output.pop(-1)
        if self.expected and self.expected != output :
            print("\n#### %s:%s" % (self.path, self.lineno))
            print("\n".join(self.source))
            print("## expected:")
            print("\n".join(self.expected))
            print("## obtained:")
            print("\n".join(output))
            return 1
        elif self.pychecks :
            env = {"out": "\n".join(output)}
            def assign(**data) :
                env.update(data)
                return True
            env["assign"] = assign
            ret = 0
            for check in self.pychecks :
                try :
                    res = eval(check, env)
                except Exception as err :
                    res = "raised %s: %s" % (err.__class__.__name__, err)
                if res is not True :
                    ret = 1
                    print("\n#### %s:%s" % (self.path, self.lineno))
                    print("\n".join(self.source))
                    if res is False :
                        print("## failed")
                    else :
                        print("## failed with:")
                        print(str(res).rstrip())
            return ret
        return 0

def extract (root, path) :
    package = None
    imports = set()
    tests = []
    declare = []
    for num, line in enumerate(open(os.path.join(root, path))) :
        if line.startswith('package ') :
            package = line.split()[-1]
        elif line.startswith('//+++ ') :
            tests.append(Test(path, num+1, [line[6:].rstrip()], ['true']))
        elif line.startswith('//--- ') :
            tests.append(Test(path, num+1, [line[6:].rstrip()], ['false']))
        elif line.startswith('//### ') :
            tests.append(Test(path, num+1, [line[6:].rstrip()]))
        elif line.startswith('//... ') :
            tests[-1].source.append(line[6:].rstrip())
        elif line.startswith('//=== ') :
            tests[-1].expected.append(line[6:].rstrip())
        elif line.startswith('//>>> ') :
            tests[-1].pychecks.append(line[6:].rstrip())
        elif line.startswith('//*** ') :
            if path not in Test.idx :
                Test.idx[path] = []
            Test.idx[path].append(line[6:].rstrip())
        elif line.startswith("//$$$ ") :
            imports.update(line[6:].strip().split())
        elif line.startswith("//%%% ") :
            declare.append(line[6:].rstrip())
    print("+ %s (%s) = %s tests" % (path, package, len(tests)))
    return package, declare, imports, tests

def codegen (packages, declare, imports, tests, out) :
    funcs = []
    out.write('package main\n\nimport "fmt"\n')
    for p in packages :
        out.write('import "%s"\n' % p)
    for p in imports - packages :
        out.write('import "%s"\n' % p)
    out.write("\n")
    for d in declare :
        out.write("%s\n" % d)
    out.write("\n")
    for i, t in enumerate(tests) :
        name = "test%03u" % i
        funcs.append(name)
        out.write("func %s () {\n" % name)
        t.codegen(out, "  ")
        out.write("}\n\n")
    out.write('\nfunc main () {\n')
    for name in funcs :
        out.write("  %s()\n" % name)
    out.write('}')

def getlmap(path) :
    m = {}
    loc = None
    for n, l in enumerate(open(path)) :
        if l.strip().startswith('fmt.Println("### ') :
            loc = l.split("### ")[-1].split('"')[0]
        elif loc is None :
            m[n] = "%s:%s" % (path, n+1)
        else :
            m[n] = loc
    return m

def run (gopath, binpath=None, outpath=None) :
    if binpath is None :
        binpath = os.path.splitext(gopath)[0]
    if outpath is None :
        outpath = binpath + ".out"
    try :
        subprocess.check_output(["go", "build", gopath], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err :
        tr = getlmap(gopath)
        out = err.output.decode()
        for line in out.splitlines() :
            try :
                path, lineno, message = line.split(":", 2)
                if path.endswith(gopath) :
                    print("%s:%s" % (tr[int(lineno)], message))
                else :
                    print(line)
            except ValueError :
                print(line)
        sys.exit()
    if os.system("%s > %s" % (os.path.join("./", binpath), outpath)) != 0 :
        sys.exit()
    return outpath

def check (tests, outfile) :
    current = None
    output = []
    failed = 0
    for line in open(outfile) :
        if line.startswith("###") :
            if current is not None :
                failed += current.check(output)
            path, lineno = line.split(None, 1)[-1].strip().split(":", 1)
            current = Test.idx[path, int(lineno)]
            output = []
        else :
            output.append(line.rstrip())
    if current is not None :
        failed += current.check(output)
    return failed

if __name__ == "__main__" :
    import sys
    try :
        root, gofile = sys.argv[-2], sys.argv[-1]
    except :
        print("usage: gotest ROOT GOFILE\n")
        sys.exit(1)
    if not gofile.endswith(".go") :
        gofile += ".go"
    packages, declare, imports, tests = set(), [], set(), []
    for path in walk(root) :
        p, d, i, t = extract(root, path)
        packages.add(p)
        declare.extend(d)
        imports.update(i)
        tests.extend(t)
    codegen(packages, declare, imports, tests, open(gofile, "w"))
    print("= %s tests" % len(tests))
    output = run(gofile)
    failed = check(tests, output)
    if failed :
        print()
    print("= %s tests failed (out of %s)" % (failed, len(tests)))
