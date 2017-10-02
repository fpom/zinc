import io, tokenize, token

def isvar (name) :
    found = False
    for tok in tokenize.tokenize(io.BytesIO(name.encode()).readline) :
        if found :
            if tok.type == token.ENDMARKER :
                return True
            else :
                return False
        elif tok.start == tok.end :
            pass
        elif tok.type == token.NAME :
            found = True
        else :
            return False
