
"""
rune - module containing the rune decorator,
and some built in runes.

A rune is a python function that returns a
list or tuple of 0 or more nodes.

All runes have a specific signature:
    function(args*, nodes=[list of nodes], context={dict of context})
"""

from .tree import Node, NODE_RUNE, NODE_TYPES

runes = {}


def register(runeid, runefunc):
    """Registers a rune function. Returns the rune function."""
    runes[runeid] = runefunc
    return runefunc


def lookup(runeid):
    """Find a rune function."""
    if runeid not in runes:
        runeid = "noop"
    return runes[runeid]


def rune(runeid):
    """Rune decorator function."""
    return lambda runefunc: register(runeid, runefunc)


def load(fpath):
    """Load a rune module."""
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune,
            "Node": Node
        }
        runescope.update(NODE_TYPES)
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)


def inscribe(node, context):
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
        runefunc = lookup(rid)
        return runefunc(*rargs, nodes=nodes, context=context)


@rune("noop")
def noop_rune(*args, nodes=None, context=None):
    """Rune that returns an empty list."""
    return []
