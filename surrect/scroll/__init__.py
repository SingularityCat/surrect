"""
scroll - module for understanding scrolls and catfiles.

Scroll is a simple markup language for surrect.

Syntax:
A scroll represents a hierarchical n-tree of nodes with types and values.
Each node in the tree can have any number of any type of descendants.


Any line type can be indented, including comments.
Indentation is done with groups of four spaces.
After processing any indentation, the first character of a line
determines what kind of node it forms.
 - "="  = Heading marker.
 - ":"  = Rune specifier.
 - "@"  = Neru specifier.
 - "#"  = Comment.
 - "!"  = Raw line.
 - "\n" or just whitespace = Separator
 - Anything else: Normal line.

BNF:
<scroll> ::= <node> | <scroll> "\\n" <node>
<node> ::= <rune> | <neru> | <raw> | <heading> | <text> | <comment>
<indent> ::= "" | "    " | <indent> "    "

<rune> ::= <indent> ":" <identifier> "(" <argstr> ")"
<neru> ::= <indent> "@" <identifier> "(" <argstr> ")"
<raw> ::= <indent> "!" <string>
<heading> ::= <indent> "=" <string>
<text> ::= <indent> <string>
<comment> ::= <indent> "#" <string>

<argstr> ::= <quoted string> | <argstr> "," <quoted string>


Catfiles are simple key, value pair files, designed to hold
information about a category and how it sould be constructed.

Parsed catfiles have 5 valid keys, "name", "index",
"page", "link" and "exclude".

Catfiles have the from:
<catfile> ::= <kvp> | <catfile> "\\n" <kvp>

<kvp> ::= <key> : <value>
<key> ::= "name" | "index" | "page" | "link" | "exclude"
<value> ::= <argstr>

"""

from collections import namedtuple
from . import lexer, parser
from .util import interpret_bool, interpret_str, interpret_strlist

# Functions for lexing/parsing 'catfiles'.

CatEntry = namedtuple("CatEntry", ["kind", "name", "path"])


def catlex(source):
    for cfl in source:
        k, _, v = cfl.partition(":")
        yield k.strip(), v.strip()


def catparse(tokens):
    catdict = {}
    entries = []
    exclude = set()
    for k, v in tokens:
        if k in {"name", "index"}:
            catdict[k] = interpret_str(v)
        elif k in {"scan"}:
            catdict[k] = interpret_bool(v)
        elif k in {"subcat", "page", "link", "resource", "secret"}:
            # These types are all "kind: [name] path"
            vn = interpret_strlist(v)[:2]
            if len(vn) > 0:
                if len(vn) == 1:
                    # Move value along, set name to None.
                    vn.append(vn[0])
                    vn[0] = None
                entries.append(CatEntry(k, *vn))
        elif k == "exclude" or k == "ignore":
            exclude.add(v)
    catdict["entries"] = entries
    catdict["exclude"] = exclude
    return catdict
