#!/usr/bin/env python3

import sys
from md2anki.md2anki import parse_cli_args, main_method


def main():
    cliArgs = parse_cli_args(sys.argv[1:])
    exitCode = main_method(cliArgs, is_package=True)
    exit(exitCode)
