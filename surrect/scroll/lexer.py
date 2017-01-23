"""
scroll.lexer:
"""

from string import whitespace
from .util import charcount, gensplit, interpret_strlist

# Token symbols
TOKEN_INDENT = "<indent>"
TOKEN_RUNE = "<rune>"
TOKEN_NERU = "<neru>"
TOKEN_RAW = "<raw>"
TOKEN_HEADING = "<heading>"
TOKEN_TEXT = "<text>"
TOKEN_BLANK = "<blank>"
TOKEN_COMMENT = "<comment>"


def extract_brackets(line):
    """Splits a scroll 'call line' into identifier + suffix."""
    ident, _, enil = line[1:].partition("(")
    thing, _, _, = enil.rpartition(")")
    return ident, thing


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

        elif line.startswith(":") or line.startswith("@"):
            # Runes have the form:
            # ":" || <rune id> || "(" || args || ")"
            runeid, args = extract_brackets(line)
            yield TOKEN_RUNE, (runeid, interpret_strlist(args))

        elif line.startswith("@"):
            # Nerus have the form:
            # "@" || <rune id> || "(" || args || ")"
            neruid, args = extract_brackets(line)
            yield TOKEN_RUNE, (neruid, interpret_strlist(args))

        elif line.startswith("#"):
            # This is a comment.
            yield TOKEN_COMMENT, line[1:]

        else:
            line = line.strip()
            if len(line) > 0:
                yield TOKEN_TEXT, line
            else:
                yield TOKEN_BLANK, None