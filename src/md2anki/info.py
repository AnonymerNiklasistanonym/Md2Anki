import os
from dataclasses import dataclass

RELATIVE_RES_DIR = "res"
RELATIVE_CSS_FILE_PATH = os.path.join(RELATIVE_RES_DIR, "stylesheet.css")
RELATIVE_CSS_FILE_PATH_TYPE_ANSWER = os.path.join(
    RELATIVE_RES_DIR, "stylesheet_type_answer.css"
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


md2anki_name = "md2anki"
md2anki_author = "AnonymerNiklasistanonym"
md2anki_description = "Convert Markdown formatted documents to anki decks"
md2anki_url = "https://github.com/AnonymerNiklasistanonym/Md2Anki"
md2anki_url_git = f"{md2anki_url}.git"
md2anki_url_bug_tracker = f"{md2anki_url}/issues"
md2anki_version = ProgramVersion(major=3, minor=0, patch=4, beta=True)

MD_ANKI_DECK_HEADING_SUBDECK_PREFIX = "Subdeck: "
MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR = "---"
ANKI_SUBDECK_SEPARATOR = "::"
