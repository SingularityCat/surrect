"""
page - Contains classes and functions for handling pages.
"""

from . import rune
from . import scroll
from . import tree
from . import render


class Page:
    """Page class"""

    def __init__(self, filepath, linkpath):
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
                if token is not scroll.TOKEN_COMMENT:
                    break
                elif value.startswith("###"):
                    key, _, value = value[3:].strip().partition("=")
                    self.context[key] = value
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
        #tree.flatten(ntree)
        tree.collate(ntree)
        return render.render(ntree)
