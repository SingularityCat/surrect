"""
# Scroll #
Simple markup language for summon

## Syntax: ##
A scroll is composed of a heriachial tree of runes.
Each node in the tree can have any number of descendents.


Any line type can be indented.
Indentation is done with groups of four spaces.
After processing any indentation, the first character of a line
determines what kind of node it forms.
:list()
     - "#"  = Heading marker.
     - ":"  = Rune specifier.
     - "!"  = Raw line.
     - "\n" or just whitespace = Separator
     - Anything else: Normal line.

## Example: ##
Quux, nested inside baz, nested inside bar, nested inside foo.

:code()
    !:foo()
    !    :bar()
    !        :baz()
    !            :quux()


BNF:
<scroll> ::= <node> | <scroll> "\\n" <node>
<node> ::= <rune> | <raw> | <heading> | <text>
<indent> ::= "" | "    " | <indent> "    "

<rune> ::= <indent> ":" <identifier> "(" <argstr> ")"
<raw> ::= <indent> "!" <string>
<heading> ::= <indent> "#" <string>
<text> ::= <indent> <string>

<argstr> ::= <quoted string> | <argstr> "," <quoted string>
"""

from enum import Enum
from string import whitespace


# Escape sequences.
escape_map = {
    "n": "\n",  # LF (line feed)
    "r": "\r",  # CR (carriage return)
    "t": "\t",  # tab (horizontal)
    "v": "\v",  # tab (vertical)
    "a": "\a",  # bell
    "b": "\b",  # backspace
    "f": "\f",  # FF (form feed)
    "\"": "\"",
    "\'": "\'",
    "\\": "\\",
}


def lex_argstr(argstr):
    """
    Turns a string representing a list of strings, into a list of strings.
    Strings are either "quoted" or 'quoted', and are comma separated.
    Understands most c/python escape codes within strings.
    See also: escape_map
    """
    argv = []
    curarg = []
    # strterm == None means we're not in a quoted string.
    strterm = None
    escaped = False
    for char in argstr:
        if strterm is None:
            if char == "\"" or char == "\'":
                strterm = char
            elif char == ",":
                argv.append("".join(curarg))
                curarg = []
            # Ignore anything else.
        elif char == "\\":
            escaped = True
        else:
            if char == strterm and not escaped:
                strterm = None
            else:
                if escaped and char in escape_map:
                    char = escape_map[char]
                curarg.append(char)
    if strterm is not None:
        argv.append("".join(curarg))
    return argv


def gensplit(src, sep):
    """Generator version of str.split"""
    while src:
        sub, _, src = src.partition(sep)
        yield sub


def charcount(s, c):
    """counts occurances of c at the start of s."""
    i = 0
    while i < len(s) and s[i] == c:
        i += 1
    return i


class token(Enum):
    rune = 0
    indent = 1
    raw = 2
    heading = 3
    text = 4
    blank = 5


def lex(source):
    if isinstance(source, str):
        source = gensplit(source, "\n")

    for line in source:
        # Strip newline.
        line = line.rstrip("\n")

        # Grab indentation.
        while line.startswith("    "):
            line = line[4:]
            yield (token.indent, None)

        # identify line type.
        if line.startswith("!"):
            # Raw lines are unstripped.
            yield (token.raw, line[1:])

        elif line.startswith("#"):
            level = charcount(line, "#")
            yield token.heading, (level, line.strip("#" + whitespace))

        elif line.startswith(":"):
            # Runes have the form:
            # ":" || <rune id> || "(" || args || ")"
            runeid, _, enil = line[1:].partition("(")
            args, _, _, = enil.rpartition(")")
            yield token.rune, (runeid, lex_argstr(args))

        else:
            line = line.strip()
            if len(line) > 0:
                yield (token.text, line)
            else:
                yield (token.blank, None)


class ScrollNode:
    def __init__(self, toktype, tokval):
        self.toktype = toktype
        self.tokval = tokval
        self.nodes = []


def parse(tokens):
    indent = 0
    prev_indent = 0
    root = ScrollNode(token.rune, ("root", None))
    scope_stack = []
    scope_cur = root
    prev_node = root

    for toktype, tokval in tokens:
        # Determine indentation level.
        if toktype == token.indent:
            # Ignore extra indents.
            indent += 0 if indent > prev_indent else 1
            continue

        node = ScrollNode(toktype, tokval)

        # Blank tokens should not affect the scope.
        if toktype == token.blank:
            indent = prev_indent

        elif indent > prev_indent:
            # Push current scope to the scope stack.
            scope_stack.append(scope_cur)
            scope_cur = prev_node

        elif indent < prev_indent:
            # Pop from the scope stack.
            scope_cur = scope_stack.pop()

        scope_cur.nodes.append(node)
        prev_node = node
        prev_indent = indent
        indent = 0

    return root


def print_tree(node, depth=0):
    idnt = depth - 1
    bnch = 0 if idnt < 0 else 1
    print(" |  " * idnt + " |->" * bnch, node.toktype, node.tokval)
    for n in node.nodes:
        print_tree(n, depth + 1)
