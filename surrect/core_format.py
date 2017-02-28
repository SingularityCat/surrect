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
    ref = path.relpath(src.destination, path.dirname(cur.destination))
    if path is not posixpath:
        trtbl = str.maketrans({path.sep: posixpath.sep, path.altsep: posixpath.sep})
        ref = pth.translate(trtbl)
    return ref
