#!/usr/bin/env python3

# Internal packages
import sys as _sys

# Local modules
from md2anki.cli import parse_cli_args
from md2anki.main import main


def entry_point():
    cli_args = parse_cli_args(_sys.argv[1:])
    exit_code = main(cli_args)
    exit(exit_code)
