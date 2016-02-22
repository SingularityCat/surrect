from enum import Enum

"""
# Scroll #
Simple markup language for summon

## Syntax: ##
The first character of each line is important.
:list()
     - "#"  = Heading marker. Multiple may be present.
     - ":"  = Rune specifier.
     - "\n" = Paragraph separator
     - Anything else: Paragraph line.

A rune specifier may be followed by zero or more indented lines.
Lines are indented with 4 spaces. This is removed from each line.
Indented lines have the same syntax as unindented ones.

## Example: ##
Quux, nested inside baz, nested inside bar, nested inside foo.

:code()
     :foo()
         :bar()
             :baz()
                 :quux()


Tokens:


BNF:
<scroll> ::= <node> | <scroll> <node>
<node> ::= <paragraph> | <rune> | <heading>
<indent> ::= "" | "    " | <indent> "    "

<heading> ::= <indent> "#" <string> "\n"
<rune> ::= <indent> ":" <identifier> "(" <string> ")" "\n"
<paragraph> ::= <indent> <string> "\n" | <indent> <string> "\n" <paragraph>
"""


def gensplit(src, sep):
    """Generator version of str.split"""
    while src:
        sub, _, src = src.partition(sep)
        yield sub


def charcount(s, c):
    i = 0
    while i < len(s) and s[i] == c:
        i += 1
    return i


class token(Enum):
    root = 0
    indent = 1
    heading = 2
    rune = 3
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
        if line.startswith("#"):
            level = charcount(line, "#")
            yield (token.heading, (level, line.strip("# ")))

        elif line.startswith(":"):
            # Runes have the form:
            # ":" || <rune id> || "(" || args || ")"
            runeid, _, enil = line[1:].partition("(")
            args, _, _, = enil.rpartition(")")
            yield (token.rune, (runeid, args))

        elif len(line) > 0:
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
    root = ScrollNode(token.root, None)
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
