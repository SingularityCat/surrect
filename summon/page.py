"""
page - Contains classes and functions for handling pages.
"""

import html

from . import rune
from . import scroll
from . import tree


class Page:
    """Page class"""

    def __init__(self, filepath):
        self.filepath = filepath
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

    def read_tree(self):
        """
        Reads and builds an entire scroll tree from a scroll file.
        """
        with open(self.filepath, "r") as source:
            self.tree = scroll.parse(scroll.lex(source))

    def build_page(self):
        tree = self.tree.deepcopy()
        evaluate_tree(tree, self.context.copy())
        #flatten(self.tree)
        collate(tree)
        return render(tree)


def evaluate_tree(node, context):
    nodes = node.nodes
    i = 0
    while i < len(nodes):
        if nodes[i].kind is tree.NODE_RUNE:
            nodes[i:i+1] = evaluate_tree(nodes[i], context)
        else:
            i += 1
    if node.kind is tree.NODE_RUNE:
        rid, rargs = node.value
        runefunc = rune.lookup(rid)
        return runefunc(*rargs, nodes=nodes, context=context)


def collect_nodes(first, gen):
    collected = [first]
    tail = None
    for node in gen:
        if node.kind is not first.kind:
            tail = node
            break
        else:
            collected.append(node)
    return collected, tail


DEFAULT_COLLATORS = {
    tree.NODE_TEXT: (" ", lambda n: n.strip()),
    tree.NODE_RAW:  ("\n", lambda n: n)
}


def collate(coll, collators=DEFAULT_COLLATORS):
    """Node collator."""
    nodegen = iter(coll.nodes)
    coll.nodes = []

    node = next(nodegen, None)
    while node is not None:
        coll.nodes.append(node)
        if node.kind in collators:
            adjns, next_node = collect_nodes(node, nodegen)
            jc, fn = collators[node.kind]
            node.value = jc.join(fn(n.value) for n in adjns)
        else:
            next_node = next(nodegen, None)
        node = next_node


def render(tree):
    body = []
    for node in tree:
        if node.kind is tree.NODE_RAW:
            body.append(node.value)
        elif node.kind is tree.NODE_HEADING:
            hn, hd = node.value
            hn = max(1, min(6, hn))
            body.append("<h{n}>{title}</h{n}>".format(n=hn, title=hd))
        elif node.kind is tree.NODE_TEXT:
            body.append("<p>" + html.escape(node.value) + "</p>")
    return "".join(body)

