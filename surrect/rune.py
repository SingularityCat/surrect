
"""
rune - module containing the rune decorator,
and some built in runes.

A rune is a python function that returns a
list or tuple of 0 or more nodes.

All runes have a specific signature:
    function(args*, nodes=[list of nodes], context={dict of context})
"""

from .scroll.tree import ScrollNode, NODE_RUNE, NODE_TYPES

runes = {None: {}}


def register(runeid, runetype, runefunc):
    """Registers a rune function. Returns the rune function."""
    if runetype not in runes:
        runes[runetype] = {}
    runes[runetype][runeid] = runefunc
    return runefunc


def lookup(runeid, runetype):
    """Find a rune function."""
    if runetype not in runes:
        runetype = None
    if runeid not in runes[runetype]:
        runeid = "noop"
    return runes[runetype][runeid]


def describe():
    """Return a list of rune names and docstrings."""
    return [("%s:%s" % (rtype, rname), func.__doc__) for rtype, typedrunes in runes.items()
            for rname, func in typedrunes.items()]


def rune(runeid, runetype=None):
    """Rune decorator function."""
    return lambda runefunc: register(runeid, runetype, runefunc)


def load(fpath):
    """Load a rune module."""
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune,
            "ScrollNode": ScrollNode
        }
        runescope.update(NODE_TYPES)
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)


def inscribe(node, rtype, context):
    """
    Inscribe all runes in a tree.
    This function works by rewrite sections of the tree
    with the output of rune functions.
    Note that the rune function can return rune nodes - this allows
    for both loops and recursion and should be used with care.
    """
    nodes = node.nodes
    i = 0
    while i < len(nodes):
        # Runes are allowed to evaluate to 0 -> n arbitrary nodes.
        # Other nodes may only evaluate to themselves.
        # As runes can produce runes, they need to be reeavaluated.
        # This allows for some nifty recursion.
        if nodes[i].kind is NODE_RUNE:
            nodes[i:i+1] = inscribe(nodes[i], context)
        else:
            inscribe(nodes[i], context)
            i += 1
    if node.kind is NODE_RUNE:
        rid, rargs = node.value
        runefunc = lookup(rid, rtype)
        return runefunc(*rargs, nodes=nodes, context=context)


@rune("noop", None)
def noop_rune(*args, nodes=None, context=None):
    """Rune that returns it's argument nodes."""
    return nodes
