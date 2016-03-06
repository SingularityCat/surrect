from .rune import rune
from . import render


@rune("list")
def list_rune(*args, nodes=None, context=None):
    for node in nodes:
        if node.kind is not NODE_BLANK:
            if node.kind is not NODE_RAW:
                pass
