import html

from .rune import rune
from .tree import Node, NODE_BLANK, NODE_HEADING, NODE_RAW
from . import render


@rune("link")
def link_rune(*args, nodes=None, context=None):
    """A hyperlink. Arguments are in the form [name] url."""
    url = "#"
    name = "here"
    if len(args) == 1:
        url = arg[0]
        name = html.escape(arg[0])
    elif len(args) == 2:
        url = arg[1]
        name = html.escape(arg[0])
    return [Node(NODE_RAW, '<a href="{0}">{1}</a>'.format(url, name))]


@rune("list")
def list_rune(*args, nodes=None, context=None):
    tags = []
    tags.append("<ul>")
    for node in nodes:
        if node.kind is NODE_TEXT:
            tags.append("<li>{0}</li>".format(html.escape(node.value)))
        elif node.kind is NODE_RAW:
            tags.append("<li>{0}</li>".format(node.value))
        elif node.kind is NODE_HEADING:
            tags.append("<li>{0}</li>".format(render.html_heading(node)))
    tags.append("</ul>")
    return [Node(NODE_RAW, "".join(tags))]
