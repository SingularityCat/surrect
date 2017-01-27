import json

from collections import OrderedDict

from logging import getLogger, ERROR, WARNING, INFO, DEBUG
from os import listdir, makedirs, mkdir, path, unlink, walk
from argparse import ArgumentParser
from shutil import copyfile, rmtree

from . import meta

from .rune import describe as rune_describe, load as rune_load
from .source import category_build
from .summon import get_outfunc_msg, load_renderers, load_globmap, globmap_sources_to_renderers, DEFAULT_CONFIG

mode_choices = {"build", "gen", "runes"}

arg_parser = ArgumentParser()
arg_parser.add_argument("-f", "--summonfile",
    dest="summonfile", action="store", default="Summonfile",
    help="read a file other then Summonfile for build configuration"
)

arg_parser.add_argument("-t", "--format",
    dest="format", action="store", default="html",
    help="output format."
)

arg_parser.add_argument("-n", "--noop",
    dest="noop", action="store_true", default=False,
    help="do a dry run - no files will be written"
)

arg_parser.add_argument("-m", "--mode",
    dest="mode", action="store", default=None, choices=mode_choices,
    help="set a summon mode"
)

arg_parser.add_argument("-b", "--build",
    dest="mode", action="store_const", const="gen",
    help="switch to build mode, this is the default"
)

arg_parser.add_argument("-r", "--runes",
    dest="mode", action="store_const", const="runes",
    help="list all runes, with descriptions"
)

arg_parser.add_argument("-g", "--gen",
    dest="mode", action="store_const", const="gen",
    help="switch to generate mode, creates a default Summonfile"
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


VERBOSITY_TO_LOGLEVEL = {
    0: ERROR,
    1: WARNING,
    2: INFO,
    3: DEBUG
}


out = get_outfunc_msg()


def gen_mode(args):
    # TODO: Support generating catfiles.
    if args.force or not path.exists(args.summonfile):
        if args.noop:
            out("Would have written default Summonfile to \"%s\""
                % args.summonfile)
            return 0
        with open(args.summonfile, "w") as cfgdst:
            out("Generating Summonfile at \"%s\"" % args.summonfile)
            json.dump(DEFAULT_CONFIG, cfgdst)
            return 0
    else:
        out("Not overwriting Summonfile at \"%s\"" % args.summonfile)
        return 1


def main():
    log = getLogger(__name__)
    args = arg_parser.parse_args()
    log.setLevel(VERBOSITY_TO_LOGLEVEL[min(args.verbosity, 3)])

    if args.ver:
        print("surrect %s" % meta.version)
        return 0

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
        return gen_mode(args)

    with open(args.summonfile) as cfgsrc:
        cfg = json.load(cfgsrc)

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
            print("{0}: {1}".format(rname, rdesc))
        return 0

    if args.mode == "build":
        root_ctx = cfg["summon"].get("context", {}).copy()

        out("Initialising renderers...")
        renderers = load_renderers(cfg["renderers"], phy_root, root_ctx)
        globmap = load_globmap(cfg["summon"]["map"])
        for renderer in renderers.values():
            renderer.set_opt(noop=args.noop, force=args.force)

        out("Gathering source information...")
        sources = OrderedDict()
        _, category_tree = category_build(cat_root, cat_root, sources)
        src_rend_list = globmap_sources_to_renderers(sources, globmap, renderers)

        if path.exists(phy_root):
            if len(listdir(phy_root)) > 0:
                if args.force:
                    rmtree(phy_root)
                    mkdir(phy_root)
                else:
                    log.error("Build directory \"%s\" exists and is not empty!"
                              % phy_root)
                    return 1
        else:
            mkdir(phy_root)

        out("Conducting riturals...")
        for source, renderer in src_rend_list:
            renderer.ritual(source)

        out("Summoning...")
        for source, renderer in src_rend_list:
            renderer.summon(source, category_tree)

    return 0

if __name__ == "__main__":
    exit(main())
