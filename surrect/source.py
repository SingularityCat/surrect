from collections import namedtuple, OrderedDict
from collections.abc import MutableMapping
from os import listdir, path

from enum import Enum
from typing import Tuple, Callable

from . import scroll


def read_scroll_metadata(scrpath : str) -> dict:
    """
    Read metadata from a scroll file.
    Metadata exists as series of special comments, each starting with
    three hashes, optionally interleaved with regular comments.
    Metadata comments are key-value pairs.
    Reading stops after the first non-comment token.
    """
    metadata = {}
    with open(scrpath, "r") as source:
        lexer = scroll.lexer.lex(source)
        for token, value in lexer:
            if token is not scroll.lexer.TOKEN_COMMENT:
                break
            # One of the hashes is removed by the lexer.
            elif value.startswith("##"):
                key, _, value = value[2:].partition(":")
                metadata[key.strip()] = value.strip()
        lexer.close()
    return metadata


def category_load(catpath: str) -> dict:
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
        if catpath == "":
            catpath = "."

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


def category_scan(catcfg: dict) -> None:
    """
    Adds all files in a directory to the end of the
    entries list in a category configuration.
    """
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


SourceType = Enum("SourceType", ("SCROLL", "RESOURCE", "LINK"))
class Source:
    __slots__ = ("kind", "source", "relpath", "ref", "metadata")

    def __init__(self, kind, source, relpath, metadata):
        self.kind = kind
        self.source = source
        self.relpath = relpath
        self.ref = None
        self.metadata = metadata


def category_build(catroot: str, catpath: str, sources: MutableMapping) -> Tuple[str, OrderedDict]:
    # Get the category configuration.
    catcfg = category_load(catpath)
    if catcfg["scan"]:
        category_scan(catcfg)
    catpath = catcfg["catpath"]
    exclude = catcfg["exclude"]
    # The category dict.
    catdict = OrderedDict()

    if catcfg["index"] is not None:
        srcpath = path.abspath(path.join(catpath, catcfg["index"]))
        relpath = path.relpath(srcpath, start=catroot)

        if path.exists(srcpath):
            srcent = Source(SourceType.SCROLL, srcpath, relpath, read_scroll_metadata(srcpath))
            catdict[None] = srcent
            sources[srcpath] = srcent
            exclude.add(catcfg["index"])

    for ent in catcfg["entries"]:
        ename = ent.name
        # Category and scroll paths are all relative to their directory.
        srcpath = path.abspath(path.join(catpath, ent.path))
        relpath = path.relpath(srcpath, start=catroot)
        if ent.path in exclude:
            # Nothing to do.
            continue
        if srcpath in sources:
            # Print a warning?
            continue
        if ent.kind == "subcat":
            scn, scd = category_build(catroot, srcpath, sources)
            if ename is None:
                ename = scn
            catdict[ename] = scd
            if ".." not in scd:
                # Set parent category reference.
                scd[".."] = catdict
        elif ent.kind == "resource":
            sources[srcpath] = Source(SourceType.RESOURCE, srcpath, relpath, {})
        elif (ent.kind == "page" or ent.kind == "secret") \
                and path.exists(srcpath):
            metadata = read_scroll_metadata(srcpath)
            srcent = Source(SourceType.SCROLL, srcpath, relpath, metadata)
            if ename is None:
                if "name" in metadata:
                    ename = metadata["name"]
                else:
                    ename = path.splitext(path.basename(ent.path))[0].title()
            if ent.kind != "secret":
                catdict[ename] = srcent
            sources[srcpath] = srcent
        elif ent.kind == "link":
            if ename is None:
                ename = ent.path
            catdict[ename] = ent.path
        else:
            # Print a warning?
            continue
    return catcfg["name"], catdict


def source(rootcat):
    sources = OrderedDict()
    return *category_build(rootcat, rootcat, sources), sources