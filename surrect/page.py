"""
page - Contains classes and functions for handling pages.
"""

from .scroll import tree
from . import render
from . import rune
from . import scroll


class Page:
    """Page class"""

    def __init__(self, fmt, filepath, linkpath):
        self.fmt = fmt
        self.filepath = filepath
        self.linkpath = linkpath
        self.context = {}
        self.tree = None

    def read_metadata(self):
        """
        Reads metadata from a scroll file.
        Metadata exists as special scroll comments,
        consisting of three hashes at the start of a file.
        Metadata comments are key-value pairs.
        Regular comments are ignored.
        Reading stops after the first non-comment token.
        """
        with open(self.filepath, "r") as source:
            lexer = scroll.lex(source)
            for token, value in lexer:
                if token is not scroll.lexer.TOKEN_COMMENT:
                    break
                # One of the hashes is removed by the lexer.
                elif value.startswith("##"):
                    key, _, value = value[2:].partition(":")
                    self.context[key.strip()] = value.strip()
            lexer.close()

    def read_scroll(self):
        """
        Reads and builds an entire scroll tree from a scroll file.
        """
        with open(self.filepath, "r") as source:
            self.tree = scroll.parse(scroll.lex(source))

    def build_main(self):
        ntree = self.tree.deepcopy()
        rune.inscribe(ntree, self.context.copy())
        tree.collate(ntree)
        yield from render.render(ntree)
