import sys
import json

from logging import getLogger, ERROR, WARNING, INFO, DEBUG
from os import listdir, mkdir, path, walk
from argparse import ArgumentParser, FileType
from shutil import rmtree

from . import meta

from . import rune, scroll
from .source import Category, category_build, scrape_scroll_metadata
from .summon import get_outfunc_msg, load_renderers, load_globmap, globmap_sources_to_renderers, DEFAULT_CONFIG


VERBOSITY_TO_LOGLEVEL = {
    0: ERROR,
    1: WARNING,
    2: INFO,
    3: DEBUG
}


log = getLogger(__name__)
out = get_outfunc_msg()

# Helper functions.

def load_runedir(runedir):
    # Load runes.
    out("Loading runes...")
    for rpfx, rdirs, runes in walk(runedir):
        for rid in runes:
            runepath = path.join(rpfx, rid)
            if runepath.endswith(".py"):
                log.info("Loading rune file \"%s\"" % runepath)
                rune.load(runepath)


# Mode functions - invoked like surrect [global opts] mode [mode opts]
# Argument is always the arg namespace.

def gen_mode(args):
    # TODO: Support generating catfiles.
    if args.force or not path.exists(args.summonfile):
        if args.noop:
            out("Would have written default Summonfile to \"%s\""
                % args.summonfile)
            return 0
        with open(args.summonfile, "w") as cfgdst:
            out("Generating Summonfile at \"%s\"" % args.summonfile)
            json.dump(DEFAULT_CONFIG, cfgdst, indent=4, sort_keys=True, ensure_ascii=False)
            cfgdst.write("\n")
            return 0
    else:
        out("Not overwriting Summonfile at \"%s\"" % args.summonfile)
        return 1


def build_mode(args):
    with open(args.summonfile) as cfgsrc:
        cfg = json.load(cfgsrc)

    cat_root = cfg["summon"]["root dir"]    # category root, aka root dir
    phy_root = cfg["summon"]["build dir"]   # physical root, aka build dir
    root_ctx = cfg["summon"].get("context", {}).copy()  # root context.

    load_runedir(cfg["summon"]["rune dir"])

    out("Initialising renderers...")
    renderers = load_renderers(cfg["renderers"], phy_root, root_ctx)
    globmap = load_globmap(cfg["summon"]["map"])
    for renderer in renderers.values():
        renderer.set_opt(noop=args.noop, force=args.force)

    out("Gathering source information...")
    category_tree = category_build(cat_root)
    log.info("source tree:")
    def log_cat_tree(cat, indent=""):
        for ent in cat:
            if isinstance(ent, Category):
                log.info("{0} - {1}".format(indent, ent))
                log_cat_tree(ent, indent + "    ")
            else:
                log.info("{0} - {1}".format(indent, ent))
    log_cat_tree(category_tree)
    src_rend_list = globmap_sources_to_renderers(category_tree.sources(), globmap, renderers)

    if path.exists(phy_root):
        if len(listdir(phy_root)) > 0:
            if args.force:
                if args.noop:
                    out("Would have removed '%s'" % phy_root)
                else:
                    out("Removing '%s'..." % phy_root)
                    rmtree(phy_root)
                    mkdir(phy_root)
            else:
                log.error("Build directory \"%s\" exists and is not empty!"
                          % phy_root)
                return 1
    else:
        if not args.noop:
            mkdir(phy_root)

        out("Conducting riturals...")
        for source, renderer in src_rend_list:
            renderer.ritual(source)

        out("Summoning...")
        for source, renderer in src_rend_list:
            renderer.summon(source, category_tree)
    return 0


def runes_mode(args):
    with open(args.summonfile) as cfgsrc:
        cfg = json.load(cfgsrc)

    load_runedir(cfg["summon"]["rune dir"])
    for rname, rdesc in rune.describe():
        print("{0}: {1}".format(rname, rdesc))
    return 0


def asm_mode(args):
    if args.runedir is not None:
        load_runedir(args.runedir)

    metadata = {}
    scroll_tree = scroll.parse(
        scrape_scroll_metadata(
            scroll.lex(args.input),
            metadata
        )
    )

    rune_tree = rune.assemble(scroll_tree)
    inscribed_tree = rune.inscribe(rune_tree, args.format, metadata)

    for node in inscribed_tree:
        if type(node.data) is str:
            args.output.write(node.data)
    
    return 0

arg_parser = ArgumentParser()

arg_parser.add_argument("-f", "--summonfile",
    dest="summonfile", action="store", default="Summonfile",
    help="read a file other then Summonfile for project configuration"
)

arg_parser.add_argument("-n", "--noop",
    dest="noop", action="store_true", default=False,
    help="do a dry run - no files will be written"
)

arg_parser.add_argument("--no-core-runes",
    dest="import_defaults", default=True,
    help="don't load core runes or format related functions."
)

arg_parser.add_argument("-F", "--force",
    dest="force", action="store_true", default=False,
    help="overwrite files, and otherwise generally care less about things"
)

arg_parser.add_argument("-v", "--verbose",
    dest="verbosity", action="count", default=0,
    help="verbosity, can be passed up to three times"
)

arg_parser.add_argument("-V", "--version",
    dest="ver", action="store_true", default=False,
    help="print version and exit"
)

arg_parser.set_defaults(mode=None)

spo = arg_parser.add_subparsers(help="mode")

build_parser = spo.add_parser("build", help="build a project")
build_parser.set_defaults(mode=build_mode)
gen_parser = spo.add_parser("gen", help="generate a default Summonfile")
gen_parser.set_defaults(mode=gen_mode)
runes_parser = spo.add_parser("runes", help="list all runes, with descriptions")
runes_parser.set_defaults(mode=runes_mode)
asm_parser = spo.add_parser("asm", help="assemble a single scroll - ignores Summonfile and noop options")
asm_parser.set_defaults(mode=asm_mode)


asm_parser.add_argument("-t", "--format",
    dest="format", action="store", default="html",
    help="use this as the output format."
)

asm_parser.add_argument("-r", "--runedir",
    dest="runedir", action="store", default="",
    help="load runes from this directory."
)

asm_parser.add_argument("--head",
    dest="head", action="store", default="",
    help="write this text before assembly"
)

asm_parser.add_argument("--tail",
    dest="tail", action="store", default="",
    help="write this text after assembly"
)

asm_parser.add_argument(nargs='?',
    dest="input", action="store", type=FileType("r"), default=sys.stdin,
    help="input file, defaults to stdin"
)

asm_parser.add_argument(nargs='?',
    dest="output", action="store", type=FileType("w"), default=sys.stdout,
    help="output file, defaults to stdout"
)


def main():
    args = arg_parser.parse_args()
    log.setLevel(VERBOSITY_TO_LOGLEVEL[min(args.verbosity, 3)])

    if args.ver:
        print("surrect %s" % meta.version)
        return 0

    if args.import_defaults:
        from . import core_runes, core_format

    out("surrect version %s" % meta.version)

    # if mode is unspecified, we will use build,
    # but only if the Summonfile exists.
    if args.mode is None:
        if path.exists(args.summonfile):
            args.mode = build_mode
        else:
            out("no mode specified and no Summonfile found.")
            arg_parser.print_help()
            return 1

    return args.mode(args)

if __name__ == "__main__":
    exit(main())
