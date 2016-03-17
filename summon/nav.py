from collections import OrderedDict
from collections.abc import Mapping
from os import listdir, path

from . import scroll
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
    """
    # Early exit if scanning is disabled in this configuration.
    if not catcfg["scan"]:
        return
    # Construct set of accounted for paths.
    accounted = {ent.path for ent in catcfg["entries"]} | catcfg["exclude"]
    catpath = catcfg["catpath"]
    for p in listdir(catpath):
        # Skip accounted for paths.
        if p in accounted:
            continue
        rp = path.join(catpath, p)
        if path.isdir(rp):
            sce = scroll.CatEntry("subcat", None, p)
            catcfg["entries"].append(sce)
        elif path.exists(rp) and rp.endswith(".scroll"):
            sce = scroll.CatEntry("page", None, p)
            catcfg["entries"].append(sce)


def category_build(catpath, pageset, resourceset,
                   cat_root, phy_root, log_root, pathfunc=scroll_html_pfunc):
    # Get the category configuration.
    catcfg = category_get_catcfg(catpath)
    category_scan(catcfg)
    catpath = catcfg["catpath"]
    exclude = catcfg["exclude"]
    # The category dict.
    catdict = OrderedDict()

    if catcfg["index"] is not None:
        inpath = path.normpath(path.join(catpath, catcfg["index"]))
        outpath = path.join(phy_root, path.relpath(inpath, cat_root))
        linkpath = path.join(log_root, path.relpath(outpath, phy_root))
        if path.exists(inpath):
            idxpage = page.Page(inpath, linkpath)
            pageset[pathfunc(outpath)] = idxpage
            catdict[None] = pathfunc(linkpath)

    for ent in catcfg["entries"]:
        ename = ent.name
        # Category and scroll paths are all relative to thier directory.
        inpath = path.normpath(path.join(catpath, ent.path))
        outpath = path.join(phy_root, path.relpath(inpath, cat_root))
        linkpath = path.join(log_root, path.relpath(outpath, phy_root))
        if ent.path in exclude:
            continue

        if ent.kind == "subcat":
            cn2, cd2 = category_build(inpath, pageset, resourceset,
                                      cat_root, phy_root, log_root, pathfunc)
            if ename is None:
                ename = cn2
            catdict[ename] = cd2
        elif ent.kind == "resource":
            resourceset[outpath] = inpath
        elif (ent.kind == "page" or ent.kind == "secret") \
                and path.exists(inpath):
            p = page.Page(inpath, linkpath)
            p.read_metadata()
            pageset[pathfunc(outpath)] = p
            if ename is None:
                if "name" in p.context:
                    ename = p.context["name"]
                else:
                    ename = path.splitext(path.basename(ent.path))[0].title()
            if ent.kind != "secret":
                catdict[ename] = pathfunc(linkpath)
        elif ent.kind == "link":
            if ename is None:
                ename = ent.path
            catdict[ename] = ent.path
    return catcfg["name"], catdict


ENTLSTINITFMT, ENTLSTFINIFMT = "<ul>", "</ul>"
ENTINITFMT, ENTFINIFMT = "<li>", "</li>"
CATFMT = "<h1>{name}</h1>"
IDXCATFMT = "<a href=\"{link}\"><h1>{name}</h1></a>"
LNKFMT = "<a href=\"{link}\">{name}</a>"
CURLNKFMT = "<a class=\"curlnk\" href=\"{link}\">{name}</a>"


def gen_navigation_renderer(entlstinitfunc=ENTLSTINITFMT.format,
                            entlstfinifunc=ENTLSTFINIFMT.format,
                            entinitfunc=ENTINITFMT.format,
                            entfinifunc=ENTFINIFMT.format,
                            catfunc=CATFMT.format,
                            idxcatfunc=IDXCATFMT.format,
                            lnkfunc=LNKFMT.format,
                            curlnkfunc=CURLNKFMT.format):
    def navigation_render(catdat, catname=None, curlink=None):
        entrywrap = bool(catname)
        if entrywrap:
            if None in catdat:
                yield idxcatfunc(name=catname, link=catdat[None])
            else:
                yield catfunc(name=catname)
        if entrywrap:
            yield entlstinitfunc()
        for name, link in catdat.items():
            if entrywrap:
                yield entinitfunc()
            # If we encounter a category here, recurse into it.
            if isinstance(link, Mapping):
                yield from navigation_render(link, name, curlink)
            elif link == curlink:
                yield curlnkfunc(name=name, link=link)
            else:
                yield lnkfunc(name=name, link=link)
            if entrywrap:
                yield entfinifunc()
        if entrywrap:
            yield entlstfinifunc()
    return navigation_render
