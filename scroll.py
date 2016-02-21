"""
# Scroll #
Simple markup language for summon

## Syntax: ##
The first character of each line is important.
::list()
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


BNF:
<scroll> ::= <node> | <scroll> <node>
<node> ::= <paragraph> | <rune> | <title>
<indent> ::= "" | "    " | <indent> "    "

<title> ::= <indent> "#" <string> "\n"
<rune> ::= <indent> ":" <identifier> "(" <string> ")" "\n"
<paragraph> ::= <indent> <string> "\n" | <indent> <string> "\n" <paragraph>
"""

def gensplit(src, sep):
    while src:
        sub, _, src = src.partition(sep)
        yield sub

class ScrollParser:
    def __init__(self, source):
        if isinstance(source, str):
            self.source = gensplit(source, "\n")
        elif isinstance(source, file):
            self.source = source

    def tokenize

class ScrollNode:
    def __init__(self, 
