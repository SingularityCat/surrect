from enum import Enum

Sym = Enum("Sym", ["CODE", "HREF", "STRIKE", "EMPHASIS", "STRONG"])

# Table of symbol beginnings to symbol terminals.
EXCLUSIVE_SYMBOLS = {
    "`": "`",
    "[": "]"
}

SYMTAB = {
    "`": Sym.CODE,
    "[": Sym.HREF,
    "]": Sym.HREF,
    "~": Sym.STRIKE,
    "_": Sym.EMPHASIS,
    "*": Sym.STRONG
}



def style_lex(s, heirarchy=True):
    bits = []
    stk = []
    buf = []

    s = iter(s)

    for c in s:
        if c in SYMTAB:
            if buf:
                bits.append("".join(buf))
                buf.clear()
            if c in EXCLUSIVE_SYMBOLS:
                t = EXCLUSIVE_SYMBOLS[c]
                bits.append(SYMTAB[c])
                c = next(s)
                while c != t:
                    buf.append(c)
                    c = next(s)
                bits.append("".join(buf))
                buf.clear()
                bits.append(SYMTAB[t])
            else:
                if heirarchy:
                    if c in stk:
                        wind = stk[stk.index(c) + 1:]
                        bits.extend(SYMTAB[q] for q in reversed(wind))
                        bits.append(SYMTAB[c])
                        bits.extend(SYMTAB[q] for q in wind)
                        stk.remove(c)
                    else:
                        bits.append(SYMTAB[c])
                        stk.append(c)
                else:
                    bits.append(SYMTAB[c])
        else:
            buf.append(c)
    if buf:
        bits.append("".join(buf))
    return bits
