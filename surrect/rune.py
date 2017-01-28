
"""
rune - module containing the rune decorator, some registries
and some built in runes.

A rune is a python function that returns a
list or tuple of 0 or more nodes.

All runes have a specific signature:
    function(args*, nodes=[list of nodes], attrs={set of attributes}, context={dict of context})
If a rune function does not accept all of the required keyword args, it is wrapped.

This module also defines the 'escape' decorator + registry.
"""

import inspect

from collections import namedtuple
from enum import Enum
from typing import List, Set, Sequence

from .scroll.tree import ScrollNode, NODE_BLANK, NODE_RAW, NODE_ROOT, NODE_RUNE, NODE_NERU, NODE_HEADING, NODE_TEXT


### Escape function handling. ###
def noop_escape(string, context=None):
    """Escape function that does no transformation on the string."""
    return string


escape_funcs = {None: noop_escape}


def escape_register(esctype, escfunc):
    """Registers an escape function."""
    sig = inspect.signature(escfunc)
    if "context" not in {n.name for n in sig.parameters.values()}:
        def wrap(string, context=None):
            escfunc(string)
        escfunc = wrap
    escape_funcs[esctype] = escfunc


def escape_lookup(esctype):
    """Find an escape function."""
    return escape_funcs.get(esctype, escape_funcs[None])


def escape(esctype):
    """Escape decorator function."""
    return lambda escfunc: escape_register(esctype, escfunc)


### Rune function handling. ###
def noop_rune(*args, nodes=None, context=None, attrs=None):
    """Rune that returns it's argument nodes."""
    return nodes


runes = {None: {"noop": noop_rune}}


def argfilter(func, forbidden):
    """Remove a set of keyword arguments."""
    def wrapper(*args, **kwargs):
        for k in forbidden:
            if k in kwargs:
                del kwargs[k]
        return func(*args, *kwargs)
    return wrapper


def register(runeid, runetype, runefunc):
    """Registers a rune function. Returns the rune function."""
    sig = inspect.signature(runefunc)
    kset = {"nodes", "attrs", "context"}
    pset = set()
    for n in sig.parameters.values():
        if n.kind is inspect.Parameter.VAR_KEYWORD:
            break
        elif n.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD or n.kind is inspect.Parameter.KEYWORD_ONLY:
            pset.add(n.name)
            if pset >= kset:
                break
    else:
        runefunc = argfilter(runefunc, kset - pset)

    if runetype not in runes:
        runes[runetype] = {}
    runes[runetype][runeid] = runefunc
    return runefunc


def lookup(runeid, runetype=None):
    """Find a rune function."""
    if runetype not in runes:
        runetype = None
    if runeid not in runes[runetype]:
        runetype = None
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
RuneType = Enum("RuneType", ("RUNE", "NERU", "TEXT", "DATA", "NULL"))


def mkrune(r: str, a: Sequence[object], nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a RuneNode referencing a rune."""
    return RuneNode(RuneType.RUNE, (r, a),
        [] if nodes is None else nodes,
        set() if attrs is None else attrs
    )


def mkdata(d: str, nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a data RuneNode."""
    return RuneNode(RuneType.DATA, d,
        [] if nodes is None else nodes,
        set() if attrs is None else attrs
    )


def mknull(nodes: List[RuneNode]=None, attrs: Set[str]=None) -> RuneNode:
    """Create a null RuneNode"""
    return RuneNode(RuneType.NULL, None,
        [] if nodes is None else nodes,
        set() if attrs is None else attrs
    )


def assemble(scroll_node: ScrollNode) -> RuneNode:
    """Assembles a rune tree from a scroll tree."""
    attrs = set()
    if scroll_node.kind == NODE_TEXT:
        kind = RuneType.TEXT
        data = scroll_node.value
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
    elif scroll_node.kind == NODE_NERU:
        rune, args = scroll_node.value
        kind = RuneType.NERU
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
    nodes = [assemble(sn) for sn in scroll_node.nodes]
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
    if node.kind is RuneType.NERU:
        rid, rargs = node.data
        runefunc = lookup(rid, rtype)
        return runefunc(*rargs, nodes=nodes, attrs=node.attributes, context=context)
    i = 0
    while i < len(nodes):
        # Runes are allowed to evaluate to 0 -> n arbitrary nodes.
        # Other nodes may only evaluate to themselves.
        # As runes can produce runes, they need to be reevaluated.
        # This allows for some nifty recursion.
        if nodes[i].kind in {RuneType.RUNE, RuneType.NERU, RuneType.TEXT}:
            nodes[i:i+1] = inscribe(nodes[i], rtype, context)
        else:
            inscribe(nodes[i], rtype, context)
            i += 1
    if node.kind is RuneType.RUNE:
        rid, rargs = node.data
        runefunc = lookup(rid, rtype)
        return runefunc(*rargs, nodes=nodes, attrs=node.attributes, context=context)
    if node.kind is RuneType.TEXT:
        escfunc = escape_lookup(rtype)
        escdata = escfunc(node.data, context=context)
        return [RuneNode(RuneType.DATA, escdata, node.nodes, node.attributes)]
