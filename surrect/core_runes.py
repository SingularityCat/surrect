import html

from typing import List

from .rune import rune, mkrune, mkdata, mknull, isdata, RuneNode, RuneType


def clamp(mn, n, mx):
    return mn if mn > n else mx if mx < n else n


def flatten_tree(nodes: List[RuneNode]) -> List[RuneNode]:
    flatree = []
    for node in nodes:
        flatree.append(node)
        if len(node.nodes) > 0:
            flatree += flatten_tree(node.nodes)
    return [RuneNode(n.kind, n.data, None, n.attributes) for n in flatree]


@rune("heading")
def heading(hl, hd, nodes, attrs, context):
    """Produces a simple heading."""
    return [mkdata("{pad} {title} {pad}\n".format(pad="="*hl, title=hd))]


@rune("heading", "html")
def heading_html(hl, hd, nodes, attrs, context):
    """Formats a HTML heading."""
    return [mkdata("<h{n}>{title}</h{n}>".format(n=clamp(1, hl, 6), title=hd))]


@rune("root")
def root(nodes, attrs, context):
    """Flattens the node tree and returns it."""
    return flatten_tree(nodes)


@rune("root", "html")
def root_html(*, nodes, attrs, context):
    """HTML root node processor. Joins data nodes with the 'collate' attribute."""
    tree = []
    niter = iter(flatten_tree(nodes))
    eon = False
    for node in niter:
        collated = []
        while "collate" in node.attributes:
            collated.append(node)
            try:
                node = next(niter)
            except StopIteration:
                eon = True
                break

        if len(collated) > 0:
            collation = " ".join(coln.data.strip() for coln in collated if coln.kind is RuneType.DATA)
            tree.append(mkdata("<p>" + collation + "</p>"))
        if not eon:
            tree.append(node)

    return tree


@rune("link")
def link_rune(*args, nodes, attrs, context):
    """Link text. Arguments are in the form [name] url."""
    text = "(none)"
    if len(args) == 1:
        text = "[{0}]".format(args[0])
    elif len(args) == 2:
        text = "{0} [{1}]".format(args[0], args[1])
    return [mkdata(text)]


@rune("link", "html")
def link_rune_html(*args, nodes, attrs, context):
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
def list_rune(*args, nodes, attrs, context):
    """Creates an unordered list."""
    style = " - " if len(args) < 1 else args[0]

    def list_recurse(s, i, n):  # style, indent, nodes
        for node in n:
            if isdata(node):
                yield i + s + node.data
            if len(node.nodes) > 0:
                yield from list_recurse(s, i + len(s)*" ", node.nodes)
    return [mkdata("\n".join(list_recurse(style, "", nodes)))]


@rune("list", "html")
def list_rune_html(*args, nodes, attrs, context):
    """Creates an unordered list."""
    def list_recurse(n):  # nodes
        yield "<ul>"
        for node in n:
            yield "<li>"
            if isdata(node):
                yield node.data
            if len(node.nodes) > 0:
                yield from list_recurse(node.nodes)
            yield "</li>"
        yield "</ul>"

    return [mkdata("".join(list_recurse(nodes)))]


@rune("section")
def section_rune(*args, nodes, attrs, context):
    """Adds a newline after some nodes."""
    return nodes + [mkdata("\n")]


@rune("section", "html")
def section_rune_html(*args, nodes, attrs, context):
    """Wraps nodes in <section> tags."""
    return [mkdata("<section>")] + nodes + [mkdata("</section>")]


@rune("code", "html")
def code_rune_html(*args, nodes, attrs, context):
    """"""
    return [mkdata("<code>")] + nodes + [mkdata("</code>")]


@rune("small")
def small_rune(*args, nodes, attrs, context):
    """Does nothing to it's arguments"""
    return [mkdata(" ".join(args))]

@rune("small", "html")
def small_rune_html(*args, nodes, attrs, context):
    """Wraps it's arguments in <small> tags."""
    stext = html.escape(" ".join(args))
    return [mkdata("<small>" + stext + "</small>")]
