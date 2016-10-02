"""
page - Contains classes and functions for handling pages.
"""

from copy import deepcopy

from . import rune
from . import scroll


class Page:
    """Page class"""

    def __init__(self, fmt, filepath, linkfmt, ctx):
        self.filepath = filepath
        self.context = deepcopy(ctx)
        # Read metadata from a scroll file.
        # Metadata exists as series of special comments, each starting with
        # three hashes, optionally interleaved with regular comments.
        # Metadata comments are key-value pairs.
        # Reading stops after the first non-comment token.
        with open(filepath, "r") as source:
            lexer = scroll.lex(source)
            for token, value in lexer:
                if token is not scroll.lexer.TOKEN_COMMENT:
                    break
                # One of the hashes is removed by the lexer.
                elif value.startswith("##"):
                    key, _, value = value[2:].partition(":")
                    self.context[key.strip()] = value.strip()
            lexer.close()
        self.linkpath = linkfmt.vformat([], self.context)
        self.tree = None

    def read_scroll(self):
        """Reads and builds an entire scroll tree from a scroll file."""
        with open(self.filepath, "r") as source:
            self.tree = scroll.parse(scroll.lex(source))

    def build_main(self, fmt):
        rtree = rune.assemble(self.tree, fmt)
        procnodes = rune.inscribe(rtree, fmt, deepcopy(self.context))
        yield from (rnode.data for rnode in procnodes)
