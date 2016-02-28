from sys import path
from configparser import SafeConfigParser as ConfigParser

from . import rune 
from . import scroll
from . import tree


def collect_nodes(first, gen):
    collected = [first]
    tail = None
    for node in gen:
        if node.kind is not first.kind:
            tail = node
            break
        else:
            collected.append(node)
    return collected, tail


default_collators = {
    tree.NODE_TEXT: (" ", lambda n: n.strip()),
    tree.NODE_RAW:  ("\n", lambda n: n)
}


def collate(node, collators=default_collators):
    """Node collator."""
    collated = node.copy()

    nodegen = iter(collated.nodes)
    collated.nodes = []

    try:
        node = next(nodegen).copy()
        while True:
            collated.nodes.append(node)
            if node is not None and node.kind in collators:
                adjns, next_node = collect_nodes(node, nodegen)
                jc, fn = collators[node.kind]
                node.value = jc.join(fn(n.value) for n in adjns)
            else:
                next_node = next(nodegen)
            if next_node is None:
                node = None
            else:
                node = next_node.copy()
    except StopIteration:
        pass

    return collated


DEFAULT_CONFIG = {
    "summon": {
        "root dir": "root",
        "rune dir": "runes"
    },
    "page": {
        "page order": "header main nav footer"
    },
    "nav": {
        "nav init": "<nav id=\"leftnav\">",
        "nav fini": "</nav>",
        "cat": "<h1>{name}</h1>",
        "indexed cat": "<a href=\"{link}\"><h1>{name}</h1></a>",
        "ref init": "<ul>",
        "ref": "<li><a href={link}>{name}</a></li>",
        "ref cur": "<li><a href=\"{link}\">{name}</a></li>",
        "ref fini": "</ul>"
    },
    "header": {
        "format": ""
    },
    "footer": {
        "format": ""
    }
}


def make_default_config():
    cfg = ConfigParser()
    for sect, opts in DEFAULT_CONFIG.items():
        cfg.add_section(sect)
        for opt, val in opts.items():
            cfg[sect][opt] = val
    return cfg


