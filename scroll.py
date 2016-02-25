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
     - ";"  = Comment.
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
<node> ::= <rune> | <raw> | <heading> | <text> | <comment>
<indent> ::= "" | "    " | <indent> "    "

<rune> ::= <indent> ":" <identifier> "(" <argstr> ")"
<raw> ::= <indent> "!" <string>
<heading> ::= <indent> "#" <string>
<text> ::= <indent> <string>
<comment> ::= <indent> ";" <string>

<argstr> ::= <quoted string> | <argstr> "," <quoted string>
"""

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


# Token symbols
class Token:
    indent = 0
    rune = 1
    raw = 2
    heading = 3
    text = 4
    blank = 5
    comment = 6


def lex(source):
    if isinstance(source, str):
        source = gensplit(source, "\n")

    for line in source:
        # Strip newline.
        line = line.rstrip("\n")

        # Grab indentation.
        while line.startswith("    "):
            line = line[4:]
            yield (Token.indent, None)

        # identify line type.
        if line.startswith("!"):
            # Raw lines are unstripped.
            yield (Token.raw, line[1:])

        elif line.startswith("#"):
            level = charcount(line, "#")
            yield Token.heading, (level, line.strip("#" + whitespace))

        elif line.startswith(":"):
            # Runes have the form:
            # ":" || <rune id> || "(" || args || ")"
            runeid, _, enil = line[1:].partition("(")
            args, _, _, = enil.rpartition(")")
            yield Token.rune, (runeid, lex_argstr(args))

        elif line.startswith(";"):
            # This is a comment.
            yield Token.comment, line[1:]

        else:
            line = line.strip()
            if len(line) > 0:
                yield Token.text, line
            else:
                yield Token.blank, None


class Node:
    # Kinds of node.
    root = 0
    rune = 1
    raw = 2
    heading = 3
    text = 4
    blank = 5

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
        self.nodes = []


# Map of tokens to corresponding nodes.
parser_token_map = {
    Token.rune:     Node.rune,
    Token.raw:      Node.raw,
    Token.heading:  Node.heading,
    Token.text:     Node.text,
    Token.blank:    Node.blank
}


def parse(tokens):
    indent = 0
    prev_indent = 0
    root = Node(Node.root, None)
    scope_stack = []
    scope_cur = root
    prev_node = root

    for toksym, tokval in tokens:
        # Determine indentation level.
        if toksym is Token.indent:
            # Ignore extra indents.
            indent += 0 if indent > prev_indent else 1
            continue

        # Construct a node from a token symbol, if possible.
        node = None
        if toksym in parser_token_map:
            node = Node(parser_token_map[toksym], tokval)

        if node.kind is Node.blank:
            # Blank nodes should not affect the scope.
            indent = prev_indent
            # Consecutive blank nodes sould not be emitted.
            if prev_node.kind is Node.blank:
                node = None

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


def print_tree(node, depth=0):
    idnt = depth - 1
    bnch = 0 if idnt < 0 else 1
    print(" |  " * idnt + " |->" * bnch, node.kind, node.value)
    for n in node.nodes:
        print_tree(n, depth + 1)
