#!/usr/bin/env python3

# Internal packages
from typing import Final

# anki information
ANKI_SUBDECK_SEPARATOR: Final = "::"
"""This seperator in the name of a deck marks it as a subdeck: `GrandparentDeck::ParentDeck::ChildDeck`"""
ANKI_SUPPORTED_FILE_FORMATS: Final = [".jpg", ".png", ".svg"]
"""A list of files that are natively supported as assets"""
