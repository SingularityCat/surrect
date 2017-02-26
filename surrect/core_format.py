import html
import urllib.parse

from os import path
import posixpath

from .registries import escape, referencer
from .util import path_attributes


@escape("html")
def escape_html(string, context=None):
    """Escapes HTML"""
    return html.escape(string)

@referencer("html")
def reference_html(src, cur):
    pth = path.relpath(src.destination, path.dirname(cur.destination))
    if path is not posixpath:
        trtbl = str.maketrans({path.sep: posixpath.sep, path.altsep: posixpath.sep})
        pth = pth.translate(trtbl)
    frags = src.metadata.copy()
    frags.update((k, urllib.parse.quote_plus(v, safe="/")) for k, v in path_attributes(pth).items())
    return frags
