import argparse, io, pkgutil, ast, importlib
import zinc, zinc.compil, zinc.io.zn

class ListBackends (argparse.Action) :
    def __call__ (self, parser, namespace, values, option_string=None):
        names = []
        for _, name, ispkg in pkgutil.walk_packages(zinc.compil.__path__) :
            if ispkg :
                names.append(name)
        names.sort()
        width = max(len(n) for n in names)
        for name in names :
            try :
                lang = zinc.compil.getlang(name)
                print("".join([name.ljust(width + 4), lang.DESCRIPTION]))
                for opt, (descr, default) in sorted(lang.OPTIONS.items()) :
                    print(" ", ("--%s=%r" % (opt, default)).ljust(14), "  ", descr)
            except :
                pass
        parser.exit()

parser = argparse.ArgumentParser(prog="zn", description="zinc is the net compiler")
parser.add_argument("-o", metavar="PATH", dest="output", default=None,
                    help="output code to PATH")
parser.add_argument("-n", metavar="NAME", dest="name", default="net",
                    help="name of the generated module")
parser.add_argument("-m", metavar="NAME", dest="module", default=None,
                    help="load SOURCE as a module and use NAME as net variable")
parser.add_argument("-l", nargs=0, action=ListBackends,
                    help="show available backends and exit")
parser.add_argument("source", metavar="SOURCE",
                    help="source file for the net to compile")

usage = io.StringIO()
parser.print_usage(usage)
parser.usage = usage.getvalue().strip() + " [--OPT=VAL ...]"
parser.epilog = "arguments --OPT=VAL add backend specific options"

args, opts = parser.parse_known_args()
options = {}
for o in opts :
    if not o.startswith("--") :
        parser.error("expected --OPT=VAL, got %r" % o)
    try :
        key, val = o[2:].split("=", 1)
    except :
        parser.error("expected --OPT=VAL, got %r" % o)
    try :
        options[key] = ast.literal_eval(val)
    except :
        options[key] = val

if args.module :
    mod = importlib.import_module(args.source)
    net = getattr(mod, args.module)
else :
    try :
        src = open(args.source)
    except Exception as err :
        parser.error("could not open %r (%s: %s)"
                     % (args.source, err.__class__.__name__, err))
    net = zinc.io.zn.load(src)

net.build(name=args.name, saveto=args.output, **options)
