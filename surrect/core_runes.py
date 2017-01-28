import html

from typing import List
from .rune import escape, rune, mkrune, mkdata, mknull, RuneNode, RuneType


def clamp(mn, n, mx):
    return mn if mn > n else mx if mx < n else n


def flatten_tree(nodes: List[RuneNode]) -> List[RuneNode]:
    flatree = []
    for node in nodes:
        flatree.append(node)
        if len(node.nodes) > 0:
            flatree += flatten_tree(node.nodes)
    return [RuneNode(n.kind, n.data, None, n.attributes) for n in flatree]


@escape("html")
def escape_html(string, context=None):
    """Escapes HTML,"""
    return html.escape(string)


@rune("heading")
def heading(hl, hd, nodes=None, attrs=None, context=None):
    """Produces a simple heading."""
    return [mkdata("{pad} {title} {pad}".format(pad="="*hl, title=hd))]


@rune("heading", "html")
def heading_html(hl, hd, nodes=None, attrs=None, context=None):
    """Formats a HTML heading."""
    return [mkdata("<h{n}>{title}</h{n}>".format(n=clamp(1, hl, 6), title=hd))]


@rune("root")
def root(nodes=None, attrs=None, context=None):
    """Flattens the node tree and returns it."""
    return flatten_tree(nodes)


@rune("root", "html")
def root_html(nodes=None, attrs=None, context=None):
    """HTML root node processor. Joins data nodes with the 'collate' attribute."""
    tree = []
    niter = iter(flatten_tree(nodes))
    for node in niter:
        collated = []
        while "collate" in node.attributes:
            collated.append(node)
            try:
                node = next(niter)
            except StopIteration:
                break

        if len(collated) > 0:
            collation = " ".join(coln.data.strip() for coln in collated if coln.kind is RuneType.DATA)
            tree.append(mkdata("<p>" + collation + "</p>"))
        tree.append(node)

    return tree


@rune("link")
def link_rune(*args, nodes=None, attrs=None, context=None):
    """Link text. Arguments are in the form [name] url."""
    text = "(none)"
    if len(args) == 1:
        text = "[{0}]".format(args[0])
    elif len(args) == 2:
        text = "{0} [{1}]".format(args[0], args[1])
    return [mkdata(text)]

@rune("link", "html")
def link_rune_html(*args, nodes=None, attrs=None, context=None):
    """A hyperlink. Arguments are in the form [name] url."""
    url = "#"
    name = "here"
    if len(args) == 1:
        url = args[0]
        name = html.escape(args[0])
    elif len(args) == 2:
        url = args[1]
        name = html.escape(args[0])
    return [mkdata('<a href="{0}">{1}</a>'.format(url, name))]


@rune("list")
def list_rune(*args, nodes=None, attrs=None, context=None):
    """Creates an unordered list."""
    lines = [" - " + node.data for node in nodes if node.kind is RuneType.Data]
    return [mkdata("\n".join(lines))]


@rune("list", "html")
def list_rune_html(*args, nodes=None, attrs=None, context=None):
    """Creates an unordered list."""
    tags = []
    tags.append("<ul>")
    for node in nodes:
        if node.kind is RuneType.DATA:
            tags.append("<li>{0}</li>".format(node.data))
    tags.append("</ul>")
    return [mkdata("".join(tags))]


@rune("section")
def section_rune(*args, nodes=None, attrs=None, context=None):
    """Adds a newline after some nodes."""
    return nodes + [mkdata("\n")]


@rune("section", "html")
def section_rune(*args, nodes=None, attrs=None, context=None):
    """Wraps an indented section in <section> tags."""
    return [mkdata("<section>")] + nodes + [mkdata("</section>")]


@rune("small", "html")
def small_rune(*args, nodes=None, attrs=None, context=None):
    """Wraps an indented section in <small> tags."""
    stext = html.escape(" ".join(args))
    return [mkdata("<small>" + stext + "</small>")]
