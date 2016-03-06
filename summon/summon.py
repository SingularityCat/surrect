from functools import partial
from collections import OrderedDict
from os import listdir, path
from configparser import SafeConfigParser as ConfigParser

from . import rune
from . import scroll
from . import tree
from . import page


def scroll_html_pfunc(pth):
    return path.splitext(pth)[0] + ".html"


def category_get_catcfg(catpath):
    """
    Determines a category configuration.
    A category config is a dict, containing
     - name
     - index : str, physical path to a scroll for use as a category index.
     - scan : bool, is this category configured to do scanning?
     - entries : list of (str, str/None, str) named tuples: type, name, path.
     - exclude : set os str, paths to exclude.
     - catpath : str, the prefix for all physical paths in this category.
    Returns said dict.
    """
    # Normalise the path.
    catpath = path.normpath(catpath)
    # Choose a default name based on the last part of the path.
    default_name = path.basename(catpath).strip().title()
    cfpath = catpath
    if path.isdir(catpath):
        cfpath = path.join(catpath, "cat")
    else:
        catpath = path.dirname(catpath)

    catcfg = {
        "name": default_name,
        "index": None,
        "scan": True,
        "entries": [],
        "exclude": set(),
        "catpath": catpath
    }

    if path.exists(cfpath):
        with open(cfpath, "r") as catfile:
            cc = scroll.catparse(scroll.catlex(catfile))
            catcfg.update(cc)
    return catcfg


def category_scan(catcfg):
    """
    Adds all files in a directory to the end of the
    entries list in a category configuration.
    This does not make use of, or update the 'exclude' set.
    Nor does it honour the 'scan' property.
    """
    catpath = catcfg["catpath"]
    for p in listdir(catpath):
        rp = path.join(catpath, p)
        if path.isdir(rp):
            sce = scroll.CatEntry("subcat", None, p)
            catcfg["entries"].append(sce)
        elif path.exists(rp) and rp.endswith(".scroll"):
            sce = scroll.CatEntry("page", None, p)
            catcfg["entries"].append(sce)


def category_build(catpath, pageset, phy_root, log_root,
                   pathfunc=scroll_html_pfunc):
    # Get the category configuration.
    catcfg = category_get_catcfg(catpath)
    catpath = catcfg["catpath"]
    exclude = catcfg["exclude"]
    # The category dict.
    catdict = OrderedDict()

    if catcfg["scan"]:
        category_scan(catcfg)

    if catcfg["index"] is not None:
        inpath = path.normpath(path.join(catpath, catcfg["index"]))
        outpath = pathfunc(inpath)
        linkpath = path.join(log_root, path.relpath(outpath, phy_root))
        if path.exists(inpath):
            idxpage = page.Page(inpath)
            pageset[outpath] = idxpage
            catdict[None] = linkpath

    for ent in catcfg["entries"]:
        ename = ent.name
        # Category and scroll paths are all relative to thier directory.
        inpath = path.normpath(path.join(catpath, ent.path))
        outpath = pathfunc(inpath)
        linkpath = path.join(log_root, path.relpath(outpath, phy_root))
        if ent.path in exclude:
            continue

        if ent.kind == "subcat":
            cn2, cd2 = category_build(inpath, pageset, phy_root, log_root,
                                      pathfunc)
            if ename is None:
                ename = cn2
            catdict[ename] = cd2
            exclude.add(ent.path)
        elif ent.kind == "page" and path.exists(inpath):
            p = page.Page(inpath, linkpath)
            p.read_metadata()
            pageset[outpath] = p
            if ename is None:
                if "name" in p.context:
                    ename = p.context["name"]
                else:
                    ename = path.splitext(path.basename(ent.path))[0].title()
            catdict[ename] = linkpath
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
        "order": "header main nav footer"
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
