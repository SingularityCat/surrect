"""summon: Ancillary stuff related to surrect."""

import sys
import codecs

from os import path
from functools import partial
from shutil import copyfile

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

    def ritual(self, sources):
        """Prep step"""
        for srcpath, source in sources.items():
            source.ref = source.relpath

    def summon(self, sources, catroot):
        """Output step"""
        raise NotImplementedError("summon not implemented.")


@renderer("site")
class SiteRenderer(Renderer):
    def __init__(self, build_dir, root_context, fmt, cfg):
        super().__init__(build_dir, root_context, fmt)
        self.load_cfg(cfg)

    def load_cfg(self, cfg):
        """Load configuration, filling in defaults."""
        self.base_context.update(cfg.get("context", {}))
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
        self.nav_renderer = gen_navigation_renderer(
            cfg["nav"].get("start", ""),
            cfg["nav"].get("end", ""),
            cfg["nav"].get("category", "{name}\n"),
            cfg["nav"].get("indexed category", "{name} ({ref})\n"),
            cfg["nav"].get("entry list start", ""),
            cfg["nav"].get("entry list end", ""),
            cfg["nav"].get("entry start", ""),
            cfg["nav"].get("entry end", ""),
            cfg["nav"].get("link", "{name} ({ref})\n"),
            cfg["nav"].get("current link", "{name} ({ref})\n"),
            rune.escape_lookup(self.fmt)
        )

    def ritual(self, sources):
        for srcpath, source in sources.items():
            ctx = self.context.copy()
            ctx["path"] = sources.relpath
            ctx["dir"] = path.dirname(ctx["path"])
            ctx["filename"] = path.basename(ctx["path"])
            ctx["filebase"], ctx["fileext"] = path.splitext(ctx["filename"])
            ctx.update(source.metadata)
            source.metadata = ctx
            source.relpath = self.path_fmt.vformat(source.metadata)
            source.ref = self.ref_fmt.vformat(source.metadata)

    def summon(self, sources, catroot):
        for srcpath, source in sources.items():
            dstpath = path.join(self.build_dir, source.relpath)
            if source.kind is SourceType.SCROLL:
                with open(srcpath) as srcfile:
                    scroll_tree = scroll.parser.parse(scroll.lexer.lex(srcfile))

                rune_tree = rune.assemble(scroll_tree)
                inscribed_tree = rune.inscribe(rune_tree, self.fmt, source.metadata)

                with open(dstpath) as dstfile:
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
                            dstfile.write(block.vformat(source.metadata))
                        else:
                            # Print warning?
                            pass
            elif source.kind is SourceType.RESOURCE:
                copyfile(srcpath, dstpath)


def load_renderers(cfg, build_dir, root_context):
    rendmap = {}
    for rendname, rendcfg in cfg.items():
        rid, _, fmt = rendcfg["renderer"].partition(":")
        rendinst = renderer_lookup(rid)(build_dir, root_context, fmt, rendcfg)
        rendmap[rendname] = rendinst
    return rendmap


DEFAULT_CONFIG = {
    "summon": {
        "root dir": "root",
        "rune dir": "runes",
        "build dir": "build",
        "map": [
            ["*.man.scroll", "manual"],
            ["*.scroll", "site"]
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
