"""
tree: Contains scroll/summon intermediate representation tree code.

Node constants, class and functions used for
"""

# Kinds of node.
NODE_ROOT = "root"
NODE_RUNE = "rune"
NODE_RAW = "raw"
NODE_HEADING = "heading"
NODE_TEXT = "text"
NODE_BLANK = "blank"


# Dict of node types, for inclusion in namespaces and simple tests.
NODE_TYPES = {
    "NODE_ROOT": NODE_ROOT,
    "NODE_ROOT": NODE_RUNE,
    "NODE_RAW": NODE_RAW,
    "NODE_HEADING": NODE_HEADING,
    "NODE_TEXT": NODE_TEXT,
    "NODE_BLANK": NODE_BLANK
}


class NodeError(Exception):
    """Error raised when there's a problem with a tree node."""


class Node:
    """A node in a tree."""
    def __init__(self, kind, value):
        if kind not in NODE_TYPES.values():
            raise NodeError("Not a valid node type.")
        self.kind = kind
        self.value = value
        self.nodes = []

    def copy(self):
        """Create a shallow copy of a node."""
        node = Node(self.kind, self.value)
        node.nodes = self.nodes[:]
        return node

    def deepcopy(self):
        """Create a deep copy of a node."""
        node = Node(self.kind, self.value)
        node.nodes = [node.deepcopy() for node in self.nodes]
        return node


def print_tree(nodeish, depth=0):
    """Print a tree of nodes."""
    idnt = depth - 1
    bnch = 0 if idnt < 0 else 1
    if isinstance(nodeish, Node):
        kind, value = nodeish.kind, nodeish.value
        nodes = nodeish.nodes
    else:
        kind, value = "(not a node)", None
        nodes = nodeish

    print(" |  " * idnt + " |->" * bnch, kind, value)
    for node in nodes:
        print_tree(node, depth + 1)

