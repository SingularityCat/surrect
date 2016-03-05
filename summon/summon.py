from os import listdir, path
from collections import OrderedDict
from configparser import SafeConfigParser as ConfigParser

from . import rune
from . import scroll
from . import tree
from . import page


def scroll_html_pfunc(pth):
    return path.splitext(pth)[0] + ".html"


def scan_category(cpath, pageset, phy_root, pathfunc=scroll_html_pfunc):
    cfpath = cpath
    if path.isdir(cpath):
        cfpath = path.join(cpath, "cat")
    else:
        cpath = path.dirname(cpath)

    catcfg = {
        "name": path.basename(cpath).title(),
        "index": None,
        "scan": True,
        "entries": []
    }
    exclude = set()
    catdict = OrderedDict()

    if path.exists(cfpath):
        with open(cfpath, "r") as catfile:
            cc, ex = scroll.catparse(scroll.catlex(catfile))
            catcfg.update(cc)
            exclude.union(ex)

    if catcfg["scan"]:
        for p in listdir(cpath):
            rp = path.join(cpath, p)
            if path.isdir(rp):
                sce = scroll.CatEntry("subcat", None, p)
                catcfg["entries"].append(sce)
            elif rp.endswith(".scroll"):
                sce = scroll.CatEntry("page", None, p)
                catcfg["entries"].append(sce)

    # Deal with explicit items first.
    for ent in catcfg["entries"]:
        ename = ent.name
        inpath = path.join(cpath, ent.path)
        outpath = pathfunc(inpath)

        if ent.kind == "subcat":
            cn2, cd2 = scan_category(inpath, pageset, phy_root, pathfunc)
            if ename is None:
                ename = cn2
            catdict[ename] = cd2
            exclude.add(ent.path)
        elif ent.kind == "page" and path.exists(inpath):
            p = page.Page(inpath)
            p.read_metadata()
            pageset[outpath] = p
            # Name from catfile overrides page context
            if ename is None:
                if "name" in p.context:
                    ename = p.context["name"]
                else:
                    ename = path.splitext(path.basename(ent.path))[0].title()
            catdict[ename] = path.relpath(outpath, phy_root)
            exclude.add(ent.path)
        elif ent.kind == "link":
            if ename is None:
                ename = ent.path
            catdict[ename] = ent.path
    return catcfg["name"], catdict

DEFAULT_CONFIG = {
    "summon": {
        "root dir": "root",
        "rune dir": "runes",
        "prefix": "/",
        "build dir": "build"
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


