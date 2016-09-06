
"""
rune - module containing the rune decorator,
and some built in runes.

A rune is a python function that returns a
list or tuple of 0 or more nodes.

All runes have a specific signature:
    function(args*, nodes=[list of nodes], context={dict of context})
"""
from collections import namedtuple
from enum import Enum
from typing import List, Set, Sequence

from .scroll.tree import ScrollNode, NODE_BLANK, NODE_RAW, NODE_ROOT, NODE_RUNE, NODE_HEADING, NODE_TEXT


def noop_rune(*args, nodes=None, context=None):
    """Rune that returns it's argument nodes."""
    return nodes


runes = {None: {"noop": noop_rune}}


def register(runeid, runetype, runefunc):
    """Registers a rune function. Returns the rune function."""
    if runetype not in runes:
        runes[runetype] = {}
    runes[runetype][runeid] = runefunc
    return runefunc


def lookup(runeid, runetype=None):
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
            "RuneNode": RuneNode,
            "RuneType": RuneType,
            "mkrune": mkrune,
            "mkdata": mkdata,
            "mknull": mknull,
        }
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)


RuneNode = namedtuple("RuneNode", ("kind", "data", "nodes", "attributes"))
RuneType = Enum("RuneType", ("RUNE", "DATA", "NULL"))


def mkrune(r: str, a: Sequence[object], nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a RuneNode referencing a rune."""
    return RuneNode(RuneType.RUNE, (r, a), nodes, attrs)


def mkdata(d: str, nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a data RuneNode."""
    return RuneNode(RuneType.DATA, d, nodes, attrs)


def mknull(nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a null RuneNode"""
    return RuneNode(RuneType.NULL, None, nodes, attrs)


def assemble(scroll_node: ScrollNode, format: str) -> RuneNode:
    """Assembles a rune tree from a scroll tree."""
    attrs = set()
    if scroll_node.kind == NODE_TEXT:
        kind = RuneType.RUNE
        data = ("escape", (scroll_node.value,))
        attrs.add("collate")
    elif scroll_node.kind == NODE_BLANK:
        kind = RuneType.NULL
        data = None
    elif scroll_node.kind == NODE_RAW:
        kind = RuneType.DATA
        data = scroll_node.value
    elif scroll_node.kind == NODE_RUNE:
        rune, args = scroll_node.value
        kind = RuneType.RUNE
        data = (rune, tuple(args))
    elif scroll_node.kind == NODE_HEADING:
        kind = RuneType.RUNE
        data = ("heading", tuple(scroll_node.value))
    elif scroll_node.kind == NODE_ROOT:
        kind = RuneType.RUNE
        data = ("root", tuple())
    else:
        kind = RuneType.NULL
        data = None
    nodes = [assemble(sn, format) for sn in scroll_node.nodes]
    return RuneNode(kind, data, nodes, attrs)


def inscribe(node: RuneNode, rtype: str, context: dict) -> List[RuneNode]:
    """
    Inscribe all runes in a tree.
    This function works by rewriting sections of the tree
    with the output of rune functions.
    Note that the rune function can return rune nodes - this allows
    for both loops and recursion and should be used with care.
    """
    nodes = node.nodes
    i = 0
    while i < len(nodes):
        # Runes are allowed to evaluate to 0 -> n arbitrary nodes.
        # Other nodes may only evaluate to themselves.
        # As runes can produce runes, they need to be reevaluated.
        # This allows for some nifty recursion.
        if nodes[i].kind is RuneType.RUNE:
            nodes[i:i+1] = inscribe(nodes[i], rtype, context)
        else:
            inscribe(nodes[i], rtype, context)
            i += 1
    if node.kind is RuneType.RUNE:
        rid, rargs = node.data
        runefunc = lookup(rid, rtype)
        return runefunc(*rargs, nodes=nodes, context=context)
