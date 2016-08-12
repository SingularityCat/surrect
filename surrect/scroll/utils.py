def gensplit(src, sep):
    """Generator version of str.split"""
    while src:
        sub, _, src = src.partition(sep)
        yield sub


def charcount(string, char):
    """counts occurrences of c at the start of s."""
    i = 0
    while i < len(string) and string[i] == char:
        i += 1
    return i


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
