"""summon: Ancillary stuff related to surrect."""

import sys
import codecs

from os import path, makedirs
from functools import partial
from shutil import copyfile
from fnmatch import fnmatch

from . import scroll
from . import rune
from .source import source, SourceType
from .util import brace_expand


def get_outfunc_msg(colour=sys.stdout.isatty()):
    u8f = codecs.getwriter("utf8")(sys.stderr.buffer, "replace")
    return partial(print, "\033[35m⛧ \033[0m" if colour else "⛧ ", flush=True, file=u8f)


def gen_navigation_renderer(wrap_init_func,
                            wrap_fini_func,
                            nav_init_func,
                            nav_fini_func,
                            ent_init_func,
                            ent_fini_func,
                            cat_func,
                            idxcat_func,
                            lnk_func,
                            curlnk_func,
                            escape_func):
    def navigation_render(catdat, ctx, catname=None, cursource=None, function_entry=True):
        ctx = ctx.copy()
        if function_entry:
            wrap_init_func(ctx)
        entrywrap = bool(catname)
        if entrywrap:
            ctx["name"] = catname
            if None in catdat:
                ctx["ref"] = catdat[None].ref
                yield idxcat_func(ctx)
            else:
                yield cat_func(ctx)
            yield nav_init_func(ctx)
        for name, source in catdat.items():
            if name is None:
                continue
            name = escape_func(name, context=ctx)
            if entrywrap:
                yield ent_init_func(ctx)
            # If we encounter a category here, recurse into it.
            if isinstance(source, dict):
                yield from navigation_render(source, ctx, name, cursource, function_entry=False)
            else:
                ctx["name"] = name
                ctx["ref"] = source.ref
                if source is cursource:
                    yield curlnk_func(ctx)
                else:
                    yield lnk_func(ctx)
            if entrywrap:
                yield ent_fini_func(ctx)
        if entrywrap:
            yield nav_fini_func(ctx)
        if function_entry:
            wrap_fini_func(ctx)

    return navigation_render


renderers = {}


def renderer_register(rendid, rendcls):
    renderers[rendid] = rendcls


def renderer(rendid):
    return lambda rendcls: renderer_register(rendid, rendcls)


def renderer_lookup(rendid):
    return renderers[rendid]


class Renderer:
    def __init__(self, build_dir, root_context, fmt):
        self.build_dir = build_dir
        self.context = root_context.copy()
        self.fmt = fmt
        self.context["type"] = self.fmt
        # Default options:
        self.noop = False
        self.force = False

    def set_opt(self, noop=None, force=None):
        if noop is not None:
            self.noop = noop
        if force is not None:
            self.force = force

    def ritual(self, source):
        """Prep step"""
        source.ref = source.relpath

    def summon(self, source, catroot):
        """Output step"""
        raise NotImplementedError("summon not implemented.")


@renderer("site")
class SiteRenderer(Renderer):
    def __init__(self, build_dir, root_context, fmt, cfg):
        super().__init__(build_dir, root_context, fmt)
        self.load_cfg(cfg)

    def load_cfg(self, cfg):
        """Load configuration, filling in defaults."""
        self.context.update(cfg.get("context", {}))
        self.path_fmt = cfg.get("path format", "{dir}/{filebase}.{type}")
        self.reference_fmt = cfg.get("ref format", self.path_fmt)
        self.page_comp = cfg.get("page composition", ["main", "nav"])
        self.running_blocks = {}
        for name, block in cfg.get("running blocks", {}).items():
            if isinstance(block, str):
                self.running_blocks[name] = block
            else:
                # If the running block is not a string, join on a newline.
                self.running_blocks[name] = "\n".join(block)
        nav = cfg.get("nav", {})
        self.nav_renderer = gen_navigation_renderer(
            nav.get("start", "").format_map,
            nav.get("end", "").format_map,
            nav.get("category", "{name}\n").format_map,
            nav.get("indexed category", "{name} ({ref})\n").format_map,
            nav.get("entry list start", "").format_map,
            nav.get("entry list end", "").format_map,
            nav.get("entry start", "").format_map,
            nav.get("entry end", "").format_map,
            nav.get("link", "{name} ({ref})\n").format_map,
            nav.get("current link", "{name} ({ref})\n").format_map,
            rune.escape_lookup(self.fmt)
        )

    def ritual(self, source):
        ctx = self.context.copy()
        ctx["path"] = source.relpath
        ctx["dir"] = path.dirname(ctx["path"])
        if ctx["dir"] == "":
            ctx["dir"] = "."
        ctx["filename"] = path.basename(ctx["path"])
        ctx["filebase"], ctx["fileext"] = path.splitext(ctx["filename"])
        ctx.update(source.metadata)
        source.metadata = ctx
        source.relpath = self.path_fmt.format_map(source.metadata)
        source.ref = self.reference_fmt.format_map(source.metadata)

    def summon(self, source, catroot):
        srcpath = source.source
        dstpath = path.join(self.build_dir, source.relpath)

        if self.noop:
            # TODO: more granular handling.
            return

        makedirs(path.dirname(srcpath), exist_ok=True)

        if source.kind is SourceType.SCROLL:
            with open(srcpath, "r") as srcfile:
                scroll_tree = scroll.parser.parse(scroll.lexer.lex(srcfile))

            rune_tree = rune.assemble(scroll_tree)
            inscribed_tree = rune.inscribe(rune_tree, self.fmt, source.metadata)

            with open(dstpath, "w") as dstfile:
                for name in self.page_comp:
                    if name == "main":
                        for node in inscribed_tree:
                            if type(node.data) is str:
                                dstfile.write(node.data)
                    elif name == "nav":
                        for fragment in self.nav_renderer(catroot, source.metadata, cursource=source):
                            dstfile.write(fragment)
                    elif name in self.running_blocks:
                        block = self.running_blocks[name]
                        dstfile.write(block.format_map(source.metadata))
                    else:
                        # Print warning?
                        pass
        elif source.kind is SourceType.RESOURCE:
            copyfile(srcpath, dstpath)


def load_renderers(renderer_cfg, build_dir, root_context):
    rendmap = {}
    for rendname, rendcfg in renderer_cfg.items():
        rid, _, fmt = rendcfg["renderer"].partition(":")
        rendinst = renderer_lookup(rid)(build_dir, root_context, fmt, rendcfg)
        rendmap[rendname] = rendinst
    return rendmap


def load_globmap(map_cfg):
    glob_map = []
    for metaglob, rendref in map_cfg:
        glob_map += [(glob, rendref) for glob in brace_expand(metaglob)]
    return glob_map


def globmap_sources_to_renderers(sources, mapping, renderers):
    maplst = []
    for srcpath, source in sources.items():
        for glob, rendref in mapping:
            if fnmatch(srcpath, glob):
                maplst.append((source, renderers[rendref]))
                break
    return maplst


DEFAULT_CONFIG = {
    "summon": {
        "root dir": "root",
        "rune dir": "runes",
        "build dir": "build",
        "map": [
            ("*.man.scroll", "manual"),
            ("*.scroll", "site")
        ],
        "context": {
        }
    },
    "renderers": {
        "manual": {
            "renderer": "site:man",
            "path format": "man/{section}/{filebase}.{section}",
            "ref format": "{filebase}({section})",
            "page": {
                "order": "main"
            }
        },
        "site": {
            "renderer": "site:html",
            "path format": "{dir}/{filebase}.html",
            "ref format": "{dir}/{filebase}.html",
            "page composition": ["head", "main", "nav", "tail"],
            "nav": {
                "start": "<nav id=\"navigation\">",
                "end": "</nav>",
                "category": "<h1>{name}</h1>",
                "indexed category": "<a href=\"{ref}\"><h1>{name}</h1></a>",
                "entry list start": "<ul>",
                "entry list end": "</ul>",
                "entry start": "<li>",
                "entry end": "</li>",
                "link": "<a href=\"{ref}\">{name}</a>",
                "current link": "<a class=\"curlnk\" href=\"{ref}\">{name}</a>"
            },
            "running blocks": {
                "head": [
                    "<!DOCTYPE html>",
                    "<head>",
                    "    <meta charset=\"UTF-8\"/>",
                    "    <title>{title}</title>",
                    "    <meta name=\"generator\" content=\"⛧ surrect\"/>",
                    "</head>",
                    "<body>"
                ],
                "tail": [
                    "</body>"
                ]
            }
        }
    }
}
