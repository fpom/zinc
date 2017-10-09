import tokenize, token, io

TEXT = 0
NAME = 1
DOT = 2

def _gap (lines, start, end) :
    def get () :
        l0, c0, l1, c1 = start[0] - 1, start[1], end[0] - 1, end[1]
        if l0 == l1 :
            yield lines[l0][c0:c1]
        else :
            yield lines[l0][c0:]
            for lno in range(l0+1, l1) :
                yield lines[lno]
            yield lines[l1][:c1]
    return b"".join(get()).decode()

def _tokenize (text) :
    if isinstance(text, str) :
        text = text.encode()
    lines = text.splitlines(True)
    last = None
    for tok in tokenize.tokenize(io.BytesIO(text).readline) :
        if tok.start == tok.end :
            continue
        if last is not None and last.end != tok.start :
            yield TEXT, _gap(lines, last.end, tok.start)
        last = tok
        if tok.type == token.NAME :
            yield NAME, tok.string
        elif tok.string == "." :
            yield DOT, "."
        else :
            yield TEXT, tok.string

def rename (text, tr) :
    def ren() :
        dot = False
        for typ, txt in _tokenize(text) :
            if typ == NAME and not dot :
                yield tr.get(txt, txt)
            else :
                yield txt
            dot = typ == DOT
    return "".join(ren())
