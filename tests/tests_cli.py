import sys
from os.path import dirname, join

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "..", "src"))

import md2anki


def test_cli_args():
    # Debug flag
    valid_args = ["input_file.md"]
    assert md2anki.parse_cli_args(["-d", *valid_args]).debug is True
    assert md2anki.parse_cli_args(["--debug", *valid_args]).debug is True
    # Detect not existing files
    assert md2anki.parse_cli_args(["input_file.md"]).error is not None
    # Don't throw errors if file exists
    assert md2anki.parse_cli_args([__file__]).error is None
