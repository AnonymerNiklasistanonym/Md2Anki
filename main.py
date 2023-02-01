#!/usr/bin/env python3

# This file makes md2anki runnable without installing the package

import sys
from os.path import dirname, join

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "src"))

from md2anki.entry_point import entry_point


# Main method
if __name__ == "__main__":
    entry_point()
