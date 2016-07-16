import html

from .rune import rune
from .tree import Node, NODE_BLANK, NODE_HEADING, NODE_RAW, NODE_TEXT
from . import render


@rune("link")
def link_rune(*args, nodes=None, context=None):
    """Link text. Arguments are in the form [name] url."""
    text = "(none)"
    if len(args) == 1:
        text = "[{0}]".format(args[0])
    elif len(args) == 2:
        text = "{0} [{1}]".format(args[0], args[1])
    return [Node(NODE_RAW, text)]

@rune("link", "html")
def link_rune_html(*args, nodes=None, context=None):
    """A hyperlink. Arguments are in the form [name] url."""
    url = "#"
    name = "here"
    if len(args) == 1:
        url = args[0]
        name = html.escape(args[0])
    elif len(args) == 2:
        url = args[1]
        name = html.escape(args[0])
    return [Node(NODE_RAW, '<a href="{0}">{1}</a>'.format(url, name))]


@rune("list")
def list_rune(*args, nodes=None, context=None):
    """Creates an unordered list."""
    lines = []
    for node in nodes:
        if node.kind in {NODE_TEXT, NODE_RAW}:
            lines.append(" - " + node.value)
    return [Node(NODE_RAW, lines.join("\n"))]


@rune("list", "html")
def list_rune_html(*args, nodes=None, context=None):
    """Creates an unordered list."""
    tags = []
    tags.append("<ul>")
    for node in nodes:
        if node.kind is NODE_TEXT:
            tags.append("<li>{0}</li>".format(html.escape(node.value)))
        elif node.kind is NODE_RAW:
            tags.append("<li>{0}</li>".format(node.value))
    tags.append("</ul>")
    return [Node(NODE_RAW, "".join(tags))]


@rune("section")
def section_rune(*args, nodes=None, context=None):
    """Adds a newline after some nodes."""
    return nodes + [Node(NODE_RAW, "\n")]


@rune("section", "html")
def section_rune(*args, nodes=None, context=None):
    """Wraps an indented section in <section> tags."""
    return [Node(NODE_RAW, "<section>")] \
           + nodes + \
           [Node(NODE_RAW, "</section>")]


@rune("small", "html")
def small_rune(*args, nodes=None, context=None):
    """Wraps an indented section in <small> tags."""
    stext = html.escape(" ".join(args))
    return [Node(NODE_RAW, "<small>" + stext + "</small>")]
