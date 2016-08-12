"""summon: Ancillary stuff related to surrect."""

import sys
import codecs

from os import path
from configparser import ConfigParser
from functools import partial

from . import nav


def get_outfunc_msg(colour=sys.stdout.isatty()):
    u8w = codecs.getwriter("utf8")

    if colour:
        return partial(print, "\033[35m⛧ \033[0m", flush=True, file=codecs.getwriter("utf8")(sys.stderr.buffer, "replace"))
    else:
        return partial(print, "⛧ ")


def generate_page_builder(cfg, catdict):
    section_order = [sec.strip() for sec in cfg["page"]["order"].split(" ")]

    # Convert config things to formatter functions
    fmtfuncs = {}
    for fmtname, fmtval in cfg["nav"].items():
        if fmtname == "category":
            fmtfuncs["catfunc"] = fmtval.format
        elif fmtname == "indexed category":
            fmtfuncs["idxcatfunc"] = fmtval.format
        elif fmtname == "entry list start":
            fmtfuncs["entlstinitfunc"] = fmtval.format
        elif fmtname == "entry list end":
            fmtfuncs["entlstfinifunc"] = fmtval.format
        elif fmtname == "entry start":
            fmtfuncs["entinitfunc"] = fmtval.format
        elif fmtname == "entry end":
            fmtfuncs["entfinifunc"] = fmtval.format
        elif fmtname == "link":
            fmtfuncs["lnkfunc"] = fmtval.format
        elif fmtname == "current link":
            fmtfuncs["curlnkfunc"] = fmtval.format

    nav_render = nav.gen_navigation_renderer(**fmtfuncs)

    def do_header(page, outfile):
        outfile.write(cfg["header"]["start"])
        outfile.write(cfg["header"]["format"].format(*page.context))
        outfile.write(cfg["header"]["end"])

    def do_main(page, outfile):
        outfile.write("<main>")
        page.read_scroll()
        for tag in page.build_main():
            outfile.write(tag)
        outfile.write("</main>")

    def do_nav(page, outfile):
        outfile.write(cfg["nav"]["start"])
        for tag in nav_render(catdict, None, page.linkpath):
            outfile.write(tag)
        outfile.write(cfg["nav"]["end"])

    def do_footer(page, outfile):
        outfile.write(cfg["footer"]["start"])
        outfile.write(cfg["footer"]["format"].format(*page.context))
        outfile.write(cfg["footer"]["end"])

    def page_builder(page, outpath):
        title = path.splitext(path.basename(page.filepath))[0].title()
        if "title" in page.context:
            title = page.context["title"]

        outfile = open(outpath, "w")
        outfile.write("<!DOCTYPE html>\n")
        outfile.write("<head>")
        outfile.write("<meta charset=\"UTF-8\"/>")
        outfile.write("<title>" + title + "</title>")
        outfile.write(cfg["page"]["head"])
        outfile.write("</head>")
        outfile.write("<body>")
        for sec in section_order:
            if sec == "header":
                do_header(page, outfile)
            elif sec == "main":
                do_main(page, outfile)
            elif sec == "nav":
                do_nav(page, outfile)
            elif sec == "footer":
                do_footer(page, outfile)
        outfile.write("</body>")

    return page_builder


DEFAULT_CONFIG = {
    "summon": {
        "root dir": "root",
        "rune dir": "runes",
        "prefix": "/",
        "build dir": "build"
    },
    "page": {
        "order": "header main nav footer",
        "head": "<meta name=\"generator\" content=\"⛧ surrect\"/>"
    },
    "nav": {
        "start": "<nav id=\"navigation\">",
        "end": "</nav>",
        "category": nav.CATFMT,
        "indexed category": nav.IDXCATFMT,
        "entry list start": nav.ENTLSTINITFMT,
        "entry list end": nav.ENTLSTFINIFMT,
        "entry start": nav.ENTINITFMT,
        "entry end": nav.ENTFINIFMT,
        "link": nav.LNKFMT,
        "current link": nav.CURLNKFMT
    },
    "header": {
        "start": "<header>",
        "end": "</header>",
        "format": ""
    },
    "footer": {
        "start": "<footer>",
        "end": "</footer>",
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
