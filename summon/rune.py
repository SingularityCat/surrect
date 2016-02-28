
"""
rune - module containing the rune decorator,
and some built in runes.

A rune is a python function that returns a
list or tuple of 0 or more nodes.

All runes have a specific signature:
    function(args*, nodes=[list of nodes], context={dict of context})
"""

runes = {}


def register(runeid, runefunc):
    runes[runeid] = runefunc


def lookup(runeid):
    return runes[runeid]


def rune(runeid):
    """Rune decorator function."""
    def regrune(runefunc):
        register(runeid, runefunc)
    return regrune


def load(fpath):
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune
        }
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)
