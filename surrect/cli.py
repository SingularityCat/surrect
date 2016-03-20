from logging import getLogger, ERROR, WARNING, INFO, DEBUG
from os import listdir, makedirs, mkdir, path, unlink, walk
from argparse import ArgumentParser
from shutil import copyfile, rmtree

from .rune import describe as rune_describe, load as rune_load
from .nav import category_build
from .summon import get_outfunc, generate_page_builder, make_default_config
from . import meta

mode_choices = {"build", "gen", "runes"}

arg_parser = ArgumentParser()
arg_parser.add_argument("-f", "--file", "--summonfile",
    dest="summonfile", action="store", default="Summonfile",
    help="Read a file other then Summonfile for configuration."
)
arg_parser.add_argument("-n", "--noop",
    dest="noop", action="store_true", default=False,
    help="Do a dry run - no files will be written."
)

arg_parser.add_argument("-m", "--mode",
    dest="mode", action="store", default=None, choices=mode_choices,
    help="Set a summon mode."
)

arg_parser.add_argument("-b", "--build",
    dest="mode", action="store_const", const="gen",
    help="Switch to build mode, this is the default."
)

arg_parser.add_argument("-r", "--runes",
    dest="mode", action="store_const", const="runes",
    help="List all runes, with descriptions."
)

arg_parser.add_argument("-g", "--gen",
    dest="mode", action="store_const", const="gen",
    help="Switch to generate mode, creates a default Summonfile."
)

arg_parser.add_argument("-o", "--force",
    dest="force", action="store_true", default=False,
    help="Overwrite files"
)

arg_parser.add_argument("-v", "--verbose",
    dest="verbosity", action="count", default=0,
    help="Verbosity, can be passed up to three times"
)


VERBOSITY_TO_LOGLEVEL = {
    0: ERROR,
    1: WARNING,
    2: INFO,
    3: DEBUG
}


out = get_outfunc()

def main():
    log = getLogger(__name__)
    args = arg_parser.parse_args()
    log.setLevel(VERBOSITY_TO_LOGLEVEL[min(args.verbosity, 3)])
    cfg = make_default_config()

    out("surrect version %s" % meta.version)

    # if mode is unspecified, we will use build,
    # but only if the Summonfile exists.
    if args.mode is None:
        if path.exists(args.summonfile):
            args.mode = "build"
        else:
            out("no mode specified and no Summonfile found.")
            arg_parser.print_help()
            return 1

    if args.mode == "gen":
        if args.force or not path.exists(args.summonfile):
            if args.noop:
                out("Would have written default Summonfile to \"%s\""
                         % args.summonfile)
                return 0
            with open(args.summonfile, "w") as sfile:
                out("Generating Summonfile at \"%s\"" % args.summonfile)
                cfg.write(sfile)
                return 0
        else:
            out("Not overwriting Summonfile at \"%s\"" % args.summonfile)
            return 1

    cfg.read(args.summonfile)

    cat_root = cfg["summon"]["root dir"]    # category root, aka root dir
    phy_root = cfg["summon"]["build dir"]   # physical root, aka build dir
    log_root = cfg["summon"]["prefix"]      # logical root, aka prefix
    rune_dir = cfg["summon"]["rune dir"]    # location of runes.

    # Load runes.
    out("Loading runes...")
    for rpfx, rdirs, runes in walk(rune_dir):
        for rune in runes:
            runepath = path.join(rpfx, rune)
            if runepath.endswith(".py"):
                log.info("Loading rune \"%s\"" % runepath)
                rune_load(runepath)

    if args.mode == "runes":
        for rname, rdesc in rune_describe():
            print(rname, ":", rdesc)
        return 0

    if args.mode == "build":
        out("Gathering category information...")
        pages = {}
        resources = {}
        _, category_tree = category_build(cat_root, pages, resources,
                                          cat_root, phy_root, log_root)

        if args.noop:
            log.info("Would have written:")
            for outpath in pages.keys():
                log.info(outpath)
            return 0

        if path.exists(phy_root):
            if not args.force and len(listdir(phy_root)) != 0:
                log.error("Build directory \"%s\" exists and is not empty!"
                          % phy_root)
                return 1
        else:
            mkdir(phy_root)

        page_builder = generate_page_builder(cfg, category_tree)

        def apply_pathdict(pdict, operation, msgfmt):
            for outpath, obj in pdict.items():
                makedirs(path.dirname(outpath), exist_ok=True)
                if path.exists(outpath):
                    if not path.isdir(outpath):
                        unlink(outpath)
                    else:
                        rmtree(outpath, ignore_errors=True)
                    if path.exists(outpath):
                        log.critical("Path \"%s\" is stubborn." % outpath)
                        return 1
                operation(obj, outpath)
                log.info(msgfmt % outpath)
        out("Parsing scrolls and producing output...")
        apply_pathdict(pages, page_builder, "Summoned %s")
        out("Copying resources...")
        apply_pathdict(resources, copyfile, "Copied resource %s")

    return 0
