"""
scroll.lexer:
"""

from string import whitespace
from .utils import charcount, gensplit, interpret_strlist

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