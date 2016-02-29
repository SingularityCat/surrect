from sys import path
from configparser import SafeConfigParser as ConfigParser

from . import rune 
from . import scroll
from . import tree


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

