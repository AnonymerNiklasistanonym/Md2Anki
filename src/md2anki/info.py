from dataclasses import dataclass


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
md2anki_url_git = "https://github.com/AnonymerNiklasistanonym/Md2Anki.git"
md2anki_version = ProgramVersion(major=3, minor=0, patch=0, beta=True)

MD_ANKI_DECK_HEADING_SUBDECK_PREFIX = "Subdeck: "
MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR = "---"
ANKI_SUBDECK_SEPARATOR = "::"
