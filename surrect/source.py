from collections import OrderedDict
from collections.abc import MutableMapping
from os import listdir, path

from enum import Enum
from typing import Tuple, Callable

from . import scroll


def parse_scroll_metadata(lexer, metadata):
    """
    Metadata exists as series of special comments, each starting with
    three hashes, optionally interleaved with regular comments.
    Metadata comments are key-value pairs.
    Reading stops after the first non-comment token.
    Returns the first (token, value) pair of non-comment tokens,
    or None if no tokens are left.
    """
    for token, value in lexer:
        if token is not scroll.lexer.TOKEN_COMMENT:
            break
        # One of the hashes is removed by the lexer.
        elif value.startswith("##"):
            key, _, value = value[2:].partition(":")
            metadata[key.strip()] = value.strip()
    else:
        return None
    return token, value


def scrape_scroll_metadata(lexer, metadata):
    """
    Siphons off metadata from a lexer, putting it in the provided dict,
    then yeilds tokes as the lexer would.
    Uses parse_scroll_metadata to do so.
    """
    tokval = parse_scroll_metadata(lexer, metadata)
    if tokval is None:
        return
    yield tokval
    yield from lexer


def read_scroll_metadata(scrpath: str) -> dict:
    """
    Read metadata from a scroll file.
    Uses parse_scroll_metadata to do so.
    """
    metadata = {}
    with open(scrpath, "r") as source:
        lexer = scroll.lexer.lex(source)
        parse_scroll_metadata(lexer, metadata)
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
    default_name = path.basename(catpath).strip().strip(path.sep).title()
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


class Entity:
    __slots__ = ("name", "toc")


SourceType = Enum("SourceType", ("SCROLL", "RESOURCE"))


class Source(Entity):
    __slots__ = ("kind", "source", "destination", "metadata")

    def __init__(self, kind, name, toc, source, destination, metadata, relsrc=None):
        self.kind = kind
        self.toc = toc
        self.source = source
        # Note that distination will likely be rewritten by a renderer.
        self.destination = destination
        self.metadata = metadata if metadata is not None else {}
        if name is None:
            if name in self.metadata:
                self.name = self.metadata["name"]
            else:
                if toc or relsrc is None:
                    n = path.splitext(path.basename(source))[0].title()
                else:
                    n = relsrc
                self.name = self.metadata["name"] = n
        else:
            self.name = self.metadata["name"] = name
        if "title" not in self.metadata:
            self.metadata["title"] = self.name

    def __str__(self):
        return self.name + " : " + self.destination

    def __repr__(self):
        return "Source({0}, {1}, {2}, {3}, {4}, {5})".format(
            repr(self.kind), repr(self.name), repr(self.toc),
            repr(self.source), repr(self.destination),
            repr(self.metadata)
        )


class Link(Entity):
    __slots__ = ("ref",)

    def __init__(self, name, toc, ref):
        self.toc = toc
        self.ref = ref
        if name is None:
            self.name = ref
        else:
            self.name = name

    def __str__(self):
        return self.name + " : " + self.ref

    def __repr__(self):
        return "Link({0}, {1}, {2})".format(
            repr(self.name), repr(self.toc), repr(self.ref)
        )


class Category(Entity, MutableMapping):
    __slots__ = ("index", "parent", "entities")

    def __init__(self, name):
        self.name = name
        self.toc = True
        self.index = None
        self.parent = self
        self.entities = OrderedDict()

    def __str__(self):
        if self.name is not None:
            fn = self.name
        else:
            fn = "[root]"
        if self.index is not None:
            return fn + " : " + str(self.index)
        else:
            return fn

    def __setitem__(self, key, val):
        if key == "..":
            if isinstance(val, Category):
                self.parent = val
            else:
                raise TypeError("Cannot assign non-category as parent.")
        else:
            if isinstance(val, Entity):
                self.entities[key] = val
            else:
                raise TypeError("Cannot assign non-entity to a category key.")
        return val

    def __getitem__(self, key):
        if key == "..":
            return self.parent
        else:
            return self.entities[key]

    def __delitem__(self, key):
        if key == "..":
            self.parent = self
        else:
            del self.entities[key]

    def __len__(self):
        return len(self.entities)

    def __iter__(self):
        return iter(self.entities.values())

    def add(self, ent: Entity):
        if ent.name is not None:
            self.entities[ent.name] = ent
        else:
            raise ValueError("category entities cannot be anonymous")

    def sources(self):
        if isinstance(self.index, Source):
            yield self.index
        for entity in self.entities.values():
            if isinstance(entity, Category):
                yield from entity.sources()
            elif isinstance(entity, Source):
                yield entity


def category_build(catroot: str, catpath: str=None, name: str=None) -> Category:
    root = False
    if catpath is None:
        root = True
        catpath = catroot

    # Get the category configuration.
    catcfg = category_load(catpath)
    if catcfg["scan"]:
        category_scan(catcfg)
    catpath = catcfg["catpath"]
    exclude = catcfg["exclude"]

    # The category object.
    cat = Category(None if root else name or catcfg["name"])

    if catcfg["index"] is not None:
        srcpath = path.abspath(path.join(catpath, catcfg["index"]))
        relpath = path.relpath(srcpath, start=catroot)

        if path.exists(srcpath):
            metadata = read_scroll_metadata(srcpath)
            srcent = Source(SourceType.SCROLL, None, False,
                            srcpath, relpath, metadata)
            cat.index = srcent
            exclude.add(catcfg["index"])

    for ent in catcfg["entries"]:
        # Category and scroll paths are all relative to their directory.
        srcpath = path.abspath(path.join(catpath, ent.path))
        relpath = path.relpath(srcpath, start=catroot)

        if ent.path in exclude:
            # Nothing to do.
            continue
        if ent.kind == "subcat":
            sco = category_build(catroot, srcpath, ent.name)
            # Set parent category reference.
            sco.parent = cat
            cat.add(sco)
        elif (ent.kind == "page" or ent.kind == "secret") \
                and path.exists(srcpath):
            metadata = read_scroll_metadata(srcpath)
            cat.add(Source(SourceType.SCROLL, ent.name, True if ent.kind != "secret" else False,
                           srcpath, relpath, metadata, ent.path))
        elif (ent.kind == "asis" or ent.kind == "resource") \
                and path.exists(srcpath):
            cat.add(Source(SourceType.RESOURCE, ent.name, True if ent.kind != "resource" else False,
                           srcpath, relpath, None, ent.path))
        elif ent.kind == "link":
            cat.add(Link(ent.name, True, ent.path))
        else:
            # Print a warning?
            continue
    return cat

