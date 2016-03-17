"""
scroll - module for understanding scrolls and catfiles.

Scroll is a simple markup language for summon.

Syntax:
A scroll represents a heriachial n-tree of nodes with types and values.
Each node in the tree can have any number of any type of descendents.


Any line type can be indented, including comments.
Indentation is done with groups of four spaces.
After processing any indentation, the first character of a line
determines what kind of node it forms.
 - "="  = Heading marker.
 - ":"  = Rune specifier.
 - "#"  = Comment.
 - "!"  = Raw line.
 - "\n" or just whitespace = Separator
 - Anything else: Normal line.

BNF:
<scroll> ::= <node> | <scroll> "\\n" <node>
<node> ::= <rune> | <raw> | <heading> | <text> | <comment>
<indent> ::= "" | "    " | <indent> "    "

<rune> ::= <indent> ":" <identifier> "(" <argstr> ")"
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

from string import whitespace
from collections import namedtuple
from .tree import Node, NODE_ROOT, NODE_RUNE, NODE_RAW, \
    NODE_HEADING, NODE_TEXT, NODE_BLANK


# Escape sequences.
ESCAPE_MAP = {
    "n": "\n",  # LF (line feed)
    "r": "\r",  # CR (carriage return)
    "t": "\t",  # tab (horizontal)
    "v": "\v",  # tab (vertical)
    "a": "\a",  # bell
    "b": "\b",  # backspace
    "f": "\f",  # FF (form feed)
}


def eat_string(string, sentinel, escape="\\", escmap=ESCAPE_MAP):
    """
    Read characters from an iterable until a sentinel is met.
    Supports arbitrary escape characters. Both the sentinel
    and the escape can be escaped.
    Returns a list of characters read.
    """
    charlst = []
    escaped = False
    for char in string:
        if char == escape:
            escaped = True
        elif char == sentinel and not escaped:
            break
        else:
            if escaped and char in escmap:
                char = escmap[char]
            charlst.append(char)
    return charlst


def interpret_str(string):
    """Interpret a string representation of a string."""
    charsrc = iter(string)
    for char in charsrc:
        if char == "\"" or char == "\'":
            return "".join(eat_string(charsrc, char))
    else:
        return "".join(eat_string(string, None))


def interpret_strlist(argstr):
    """
    Turns a string representing a list of strings, into a list of strings.
    Strings are either "quoted" or 'quoted', and are comma separated.
    Understands most c/python escape codes within strings.
    See also: ESCAPE_MAP
    """
    argv = []
    curarg = []
    # strterm == None means we're not in a quoted string.
    strterm = None
    argstr = iter(argstr)
    for char in argstr:
        if char == "\"" or char == "\'":
            strterm = char
        elif char == ",":
            argv.append("".join(curarg))
            curarg = []
            # Ignore anything else.

        if strterm is not None:
            curarg += eat_string(argstr, strterm)
            strterm = None
    argv.append("".join(curarg))
    return argv


BOOLEAN_STRINGS = {
    "on": True,
    "true": True,
    "1": True,
    "yes": True,
    "off": False,
    "false": False,
    "0": False,
    "no": False
}


def interpret_bool(string, string_table=BOOLEAN_STRINGS):
    """Interpret a boolean string."""
    value = None
    string = string.strip().lower()
    if string in string_table:
        value = string_table[string]
    return value


def gensplit(src, sep):
    """Generator version of str.split"""
    while src:
        sub, _, src = src.partition(sep)
        yield sub


def charcount(string, char):
    """counts occurances of c at the start of s."""
    i = 0
    while i < len(string) and string[i] == char:
        i += 1
    return i


# Token symbols
TOKEN_INDENT = "<indent>"
TOKEN_RUNE = "<rune>"
TOKEN_RAW = "<raw>"
TOKEN_HEADING = "<heading>"
TOKEN_TEXT = "<text>"
TOKEN_BLANK = "<blank>"
TOKEN_COMMENT = "<comment>"


def lex(source):
    """Process scroll source code into a series of named tokens."""
    if isinstance(source, str):
        source = gensplit(source, "\n")

    for line in source:
        # Strip newline.
        line = line.rstrip("\n")

        # Grab indentation.
        while line.startswith("    "):
            line = line[4:]
            yield (TOKEN_INDENT, None)

        # identify line type.
        if line.startswith("!"):
            # Raw lines are unstripped.
            yield (TOKEN_RAW, line[1:])

        elif line.startswith("="):
            level = charcount(line, "=")
            yield TOKEN_HEADING, (level, line.strip("=" + whitespace))

        elif line.startswith(":"):
            # Runes have the form:
            # ":" || <rune id> || "(" || args || ")"
            runeid, _, enil = line[1:].partition("(")
            args, _, _, = enil.rpartition(")")
            yield TOKEN_RUNE, (runeid, interpret_strlist(args))

        elif line.startswith("#"):
            # This is a comment.
            yield TOKEN_COMMENT, line[1:]

        else:
            line = line.strip()
            if len(line) > 0:
                yield TOKEN_TEXT, line
            else:
                yield TOKEN_BLANK, None


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
    root = Node(NODE_ROOT, None)
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

        node = Node(NODE_TOKEN_MAP[toksym], tokval)
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
