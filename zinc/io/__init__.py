# coding: utf-8

import io, re

##
## insert INDENT/DEDENT
##

_indent = re.compile(r"^\s*")

def indedent (text, indent="↦", dedent="↤") :
    "insert INDENT/DEDENT tokens into text"
    stack = [0]
    src = io.StringIO(text.rstrip() + "\n")
    out = io.StringIO()
    for i, line in enumerate(src) :
        if line.rstrip() :
            width = _indent.match(line).end()
            if width > stack[-1] :
                out.write(indent)
                stack.append(width)
            elif width < stack[-1] :
                while width < stack[-1] :
                    out.write(dedent)
                    stack.pop()
                if width != stack[-1] :
                    raise IndentationError("line %s" % (i+1))
        out.write(line)
    while stack[-1] > 0 :
        out.write(dedent)
        stack.pop()
    return out.getvalue()
