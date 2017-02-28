"""
registries - module containing format-related registries, lookup functions and decorators.

=== escape ===
The escape registry holds escape functions.
Escape functions should have the signature: (str, dict) -> str
The parameters are:
    - The text to escape
    - A set of context
And it should return:
    - an escaped version of the text, suitable for inclusion anywhere in the document.

=== referencer ===
The 'referencer' registry holds referencer functions.
Referencer functions should have the signature: (Source, Source) -> dict
The parameters are:
    - The source entity being referred to.
    - The source entity needing the reference.
And it should return:
    - a string, appropriately formatted for typical references of the type.
"""

import inspect

from os import path

from .util import path_attributes

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


### Referencer function handling. ###
def default_referencer(src, cur):
    """Reference function that creates a generic fragment dict from path names."""
    return src


referencer_funcs = {None: default_referencer}


def referencer_register(reftype, reffunc):
    """Registers a referencer function."""
    referencer_funcs[reftype] = reffunc


def referencer_lookup(reftype):
    """Find an escape function."""
    return referencer_funcs.get(reftype, referencer_funcs[None])


def referencer(reftype):
    """Referencer decorator function."""
    return lambda reffunc: referencer_register(reftype, reffunc)
