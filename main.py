#!/usr/bin/env python3

# This file makes md2anki runnable without installing the package

import sys
from os.path import dirname, join

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "src"))

from md2anki.cli import parse_cli_args
from md2anki.main import main


# Main method
if __name__ == "__main__":
    cli_args = parse_cli_args(sys.argv[1:])
    exit_code = main(cli_args)
    exit(exit_code)
