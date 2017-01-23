"""
scroll.tree: Contains scroll AST code.

Node constants, class and functions used for scroll syntax representation.
"""

# Kinds of node.
NODE_ROOT = "root"
NODE_RUNE = "rune"
NODE_NERU = "neru"
NODE_RAW = "raw"
NODE_HEADING = "heading"
NODE_TEXT = "text"
NODE_BLANK = "blank"


# Dict of node types, for inclusion in namespaces and simple tests.
NODE_TYPES = {
    "NODE_ROOT": NODE_ROOT,
    "NODE_RUNE": NODE_RUNE,
    "NODE_NERU": NODE_NERU,
    "NODE_RAW": NODE_RAW,
    "NODE_HEADING": NODE_HEADING,
    "NODE_TEXT": NODE_TEXT,
    "NODE_BLANK": NODE_BLANK
}


class ScrollNodeError(Exception):
    """Error raised when there's a problem with a tree node."""


class ScrollNode:
    """A scroll node."""
    def __init__(self, kind, value):
        if kind not in NODE_TYPES.values():
            raise ScrollNodeError("Not a valid node type.")
        self.kind = kind
        self.value = value
        self.nodes = []

    def copy(self):
        """Create a shallow copy of a node."""
        node = type(self)(self.kind, self.value)
        node.nodes = self.nodes[:]
        return node

    def deepcopy(self):
        """Create a deep copy of a node."""
        node = type(self)(self.kind, self.value)
        node.nodes = [node.deepcopy() for node in self.nodes]
        return node

    def __eq__(self, n):
        """Test for equality"""
        eq = self.kind == n.kind and self.value == n.value
        return eq and self.nodes == n.nodes

    def print(self, depth=0):
        """Print this node and all descendants."""
        idnt = depth - 1
        bnch = 0 if idnt < 0 else 1
        kind, value = self.kind, self.value
        nodes = self.nodes

        print(" |  " * idnt + " |->" * bnch, kind, value)
        for node in nodes:
            node.print(depth + 1)


# ### ScrollNode collation functions ###
# Code related to collecting and combining nodes.


def collect_nodes(kind, collection, gen):
    """
    Collects nodes with a given kind from a generator,
    and puts them in the provided list.
    Returns the first node from the generator that does not
    match the provided kind.
    """
    tail = None
    for node in gen:
        if node.kind is not kind:
            tail = node
            break
        else:
            collection.append(node)
    return tail

# Default collation actions
# - text gets stripped and joined on space,
# - raw gets combined on newline.
DEFAULT_COLLATORS = {
    NODE_TEXT: (" ", lambda n: n.strip()),
    NODE_RAW:  ("\n", lambda n: n)
}


def collate(root, collators=DEFAULT_COLLATORS):
    """
    ScrollNode collator. Modifies tree in place.
    Takes two arguments, a root node, and a dict of collation functions.
    Each key in this dict is a node kind,
    and each value is a string, function pair.
    The string being the joining string (see str.join) and the function
    turning a given node into a string.
    """
    nodegen = iter(root.nodes)
    root.nodes = []

    node = next(nodegen, None)
    while node is not None:
        root.nodes.append(node)
        if node.kind in collators:
            adjns = [node]
            next_node = collect_nodes(node.kind, adjns, nodegen)
            jc, fn = collators[node.kind]
            node.value = jc.join(fn(n.value) for n in adjns)
        else:
            next_node = next(nodegen, None)
        node = next_node
