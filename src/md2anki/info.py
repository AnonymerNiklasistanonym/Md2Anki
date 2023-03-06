#!/usr/bin/env python3

# Internal packages
from dataclasses import dataclass
from pathlib import Path
from typing import Final

RELATIVE_RES_DIR: Final = Path("res")
RELATIVE_CSS_FILE_PATH: Final = RELATIVE_RES_DIR.joinpath("stylesheet.css")
RELATIVE_CSS_FILE_PATH_TYPE_ANSWER: Final = RELATIVE_RES_DIR.joinpath(
    "stylesheet_type_answer.css"
)


@dataclass
class ProgramVersion:
    """
    Contains all information about the md2anki version.
    """

    major: int
    minor: int = 0
    patch: int = 0
    beta: bool = False

    def __repr__(self):
        return f"{self.major}.{self.minor}.{self.patch}{'b' if self.beta else ''}"


md2anki_name: Final = "md2anki"
md2anki_author: Final = "AnonymerNiklasistanonym"
md2anki_description: Final = "Convert Markdown formatted documents to anki decks"
md2anki_url: Final = "https://github.com/AnonymerNiklasistanonym/Md2Anki"
md2anki_url_git: Final = f"{md2anki_url}.git"
md2anki_url_bug_tracker: Final = f"{md2anki_url}/issues"
md2anki_version: Final = ProgramVersion(major=3, minor=0, patch=11, beta=True)

MD_ANKI_DECK_HEADING_SUBDECK_PREFIX: Final = "Subdeck: "
MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR: Final = "---"
ANKI_SUBDECK_SEPARATOR: Final = "::"
