from collections import Mapping

def brace_lex(glob: str):
    tok = []
    escape = False
    globiter = iter(glob)
    for char in globiter:
        if escape:
            if char != "{":
                tok.append("\\")
            tok.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char == "{":
            yield "".join(tok)
            tok = []
            items = []
            escape = False
            char = next(globiter)
            while char != "}":
                if escape:
                    if char != "}" and char != ",":
                        tok.append("\\")
                    tok.append(char)
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == ",":
                    items.append("".join(tok))
                    tok = []
                else:
                    tok.append(char)
                char = next(globiter)
            else:
                items.append("".join(tok))
            yield tuple(items)
            tok = []
        else:
            tok.append(char)
    yield "".join(tok)


def brace_expand(glob: str):
    """Do brace expansion."""
    terminals = [""]
    for part in brace_lex(glob):
        if isinstance(part, tuple):
            terminals = [terminal + enu for enu in part for terminal in terminals]
        else:
            terminals = [terminal + part for terminal in terminals]
    return terminals


def flatten(d: Mapping, p: tuple=(), visited: set=None):
    if visited is None:
        visited = {d}
    else:
        visited.add(d)
    for k, v in d.items():
        if v in visited:
            continue
        elif isinstance(v, Mapping):
            yield from flatten(v, p=(*p, k), visited=visited)
        else:
            yield (*p, k), v
