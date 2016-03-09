from logging import getLogger
from os import path
from argparse import ArgumentParser, ArgumentError

from .summon import make_default_config

mode_choices = {"build", "gen"}

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
    dest="mod", action="store", default="build", choices=mode_choices,
    help="Set a build mode."
)

arg_parser.add_argument("-b", "--build",
    dest="mode", action="store_const", const="gen",
    help="Switch to build mode, this is the default."
)

arg_parser.add_argument("-g", "--gen",
    dest="mode", action="store_const", const="gen",
    help="Switch to generate mode, creates a default Summonfile."
)

arg_parser.add_argument("-o", "--force",
    dest="force", action="store_true", default=False,
    help="Overwrite files"
)


def main():
    args = arg_parser.parse_args()
    cfg = make_default_config()

    if args.mode == "gen":
        if args.noop:
            return 0

        if args.force or not path.exists(args.summonfile):
            with open(args.summonfile, "w") as sfile:
                cfg.write(sfile)
                return 0
        else:
            return 1

    cfg.read(args.summonfile)
    

if __name__ == "__main__":
    status = main()
    exit(status)
