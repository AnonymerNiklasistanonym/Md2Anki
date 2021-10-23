#!/usr/bin/env python3

import sys as _sys
from md2anki.md2anki import (
    parse_cli_args,
    main,
    parse_md_file_to_anki_deck,
    Md2AnkiArgs,
    AnkiDeckNote,
    AnkiDeck,
    AnkiModel,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
)


def _main():
    cliArgs = parse_cli_args(_sys.argv[1:])
    exitCode = main(cliArgs, is_package=True)
    exit(exitCode)
