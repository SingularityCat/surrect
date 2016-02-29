
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
    if runeid not in runes:
        runeid = "noop"
    return runes[runeid]


def rune(runeid):
    """Rune decorator function."""
    return lambda runefunc: register(runeid, runefunc)


def load(fpath):
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune
        }
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)


@rune("noop")
def noop(*args, nodes=None, context=None):
    return []
