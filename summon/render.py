import html

from .tree import NODE_RAW, NODE_HEADING, NODE_TEXT


def html_heading(node):
    hlv, hdg = node.values
    hlv = max(1, min(6, hlv))
    hdg = html.escape(hdg)
    return "<h{n}>{title}</h{n}>".format(n=hlv, title=hdg)


def html_paragraph(node):
    return "<p>" + html.escape(node.para) + "</p>"


def html_unknown(*stuff):
    return html.escape(str(stuff[0] if len(stuff) == 1 else stuff))


HTML_RENDERFUNCS = {
    NODE_HEADING: html_heading,
    NODE_TEXT: html_paragraph,
    NODE_RAW: lambda node: node.value,
    None: html_unknown
}


def render_node(node, renderfuncs=HTML_RENDERFUNCS):
    if node.kind in renderfuncs:
        rendered = renderfuncs[node.kind](node)
    else:
        rendered = renderfuncs[None](node)
    return rendered


def render(ntree, renderfuncs=HTML_RENDERFUNCS):
    body = []
    for node in ntree.nodes:
        body.append(render_node(node, renderfuncs))
    return "".join(body)
