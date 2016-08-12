"""
scroll.parser:
"""

from .lexer import TOKEN_BLANK, TOKEN_COMMENT, TOKEN_HEADING, \
    TOKEN_INDENT, TOKEN_RAW, TOKEN_RUNE, TOKEN_TEXT
from .tree import ScrollNode, NODE_ROOT, NODE_RUNE, NODE_RAW, \
    NODE_HEADING, NODE_TEXT, NODE_BLANK


# Map of tokens to corresponding nodes.
NODE_TOKEN_MAP = {
    TOKEN_RUNE:     NODE_RUNE,
    TOKEN_RAW:      NODE_RAW,
    TOKEN_HEADING:  NODE_HEADING,
    TOKEN_TEXT:     NODE_TEXT,
    TOKEN_BLANK:    NODE_BLANK
}


def parse(tokens):
    """Parse a series of tokens into a scroll tree."""
    indent = 0
    prev_indent = 0
    root = ScrollNode(NODE_ROOT, None)
    scope_stack = []
    scope_cur = root
    prev_node = root

    for toksym, tokval in tokens:
        # Determine indentation level.
        if toksym is TOKEN_INDENT:
            # Ignore extra indents.
            indent += 0 if indent > prev_indent else 1
            continue

        # Construct a node from a token symbol, if possible.
        node = None
        if toksym not in NODE_TOKEN_MAP:
            continue

        node = ScrollNode(NODE_TOKEN_MAP[toksym], tokval)
        # Special handling for blank nodes.
        if node.kind is NODE_BLANK:
            # Blank nodes should not affect the scope.
            indent = prev_indent

        elif indent > prev_indent:
            # Push current scope to the scope stack.
            scope_stack.append(scope_cur)
            scope_cur = prev_node

        elif indent < prev_indent:
            # Pop from the scope stack.
            scope_cur = scope_stack.pop()

        if node is not None:
            scope_cur.nodes.append(node)
            prev_node = node

        prev_indent = indent
        indent = 0

    return root
