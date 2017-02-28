"""summon: Core surrect logic."""

import sys
import codecs

from os import path, makedirs
from functools import partial
from shutil import copyfile
from fnmatch import fnmatch

from . import scroll
from . import registries
from . import rune
from .source import Category, Source, SourceType, Link
from .util import path_attributes, brace_expand


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
                            escape_func,
                            ref_func):
    def navigation_render(cat: Category, current: Source, ctx, function_entry=True):
        ctx = ctx.copy()
        if function_entry:
            yield wrap_init_func(ctx)
        entrywrap = bool(cat.name)
        if entrywrap:
            ctx["name"] = cat.name
            if cat.index is not None:
                ctx["ref"] = ref_func(cat.index, current)
                yield idxcat_func(ctx)
            else:
                yield cat_func(ctx)
            yield nav_init_func(ctx)
        for ent in cat:
            if not ent.toc:
                continue
            if entrywrap:
                yield ent_init_func(ctx)
            # If we encounter a category here, recurse into it.
            if isinstance(ent, Category):
                yield from navigation_render(ent, current, ctx, function_entry=False)
            else:
                name = escape_func(ent.name, context=ctx)
                ctx["name"] = name
                if isinstance(ent, Source):
                    ctx["ref"] = ref_func(ent, current)
                elif isinstance(ent, Link):
                    ctx["ref"] = ent.ref
                if ent is current:
                    yield curlnk_func(ctx)
                else:
                    yield lnk_func(ctx)
            if entrywrap:
                yield ent_fini_func(ctx)
        if entrywrap:
            yield nav_fini_func(ctx)
        if function_entry:
            yield wrap_fini_func(ctx)

    return navigation_render


renderers = {}


def renderer_register(rendid, rendcls):
    renderers[rendid] = rendcls


def renderer(rendid):
    return lambda rendcls: renderer_register(rendid, rendcls)


def renderer_lookup(rendid):
    return renderers[rendid]


class Referencer:
    def __init__(self, cat, current, ref_func):
        self.cat = cat
        self.current = current
        self.ref_func = ref_func

    def __getitem__(self, key):
        return RecursiveReferencer(self.cat, self.current, self.ref_func)[key]


class RecursiveReferencer(Referencer):
    def __getitem__(self, key):
        ent = self.cat[key]
        if isinstance(ent, Category):
            self.cat = ent
            return self
        elif isinstance(ent, Source):
            return self.ref_func(ent, self.current)
        elif isinstance(ent, Link):
            return ent.ref

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
        pass

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
        self.path_fmt = cfg.get("path format", "{dir}{filebase}.{type}")
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
            nav.get("entry list start", "").format_map,
            nav.get("entry list end", "").format_map,
            nav.get("entry start", "").format_map,
            nav.get("entry end", "").format_map,
            nav.get("category", "{name}\n").format_map,
            nav.get("indexed category", "{name} ({ref})\n").format_map,
            nav.get("link", "{name} ({ref})\n").format_map,
            nav.get("current link", "{name} ({ref})\n").format_map,
            registries.escape_lookup(self.fmt),
            registries.referencer_lookup(self.fmt)
        )

    def ritual(self, source):
        ctx = self.context.copy()
        ctx.update(source.metadata)
        path_attributes(source.destination, ctx)
        source.metadata = ctx
        source.destination = self.path_fmt.format_map(source.metadata)

    def summon(self, source, catroot):
        srcpath = source.source
        dstpath = path.join(self.build_dir, source.destination)

        if self.noop:
            # TODO: more granular handling.
            return

        makedirs(path.dirname(dstpath), exist_ok=True)

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
                        for fragment in self.nav_renderer(catroot, source, source.metadata):
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
    for source in sources:
        for glob, rendref in mapping:
            if fnmatch(source.source, glob):
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
            "path format": "{dir}{filebase}.html",
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
