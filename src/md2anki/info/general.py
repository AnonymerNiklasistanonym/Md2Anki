#!/usr/bin/env python3

# Internal packages
from dataclasses import dataclass
from typing import Final


@dataclass
class ProgramVersion:
    """
    Contains the program version information.
    """

    major: Final[int] = 1
    minor: Final[int] = 0
    patch: Final[int] = 0
    beta: Final[bool] = False

    def __repr__(self):
        return f"{self.major}.{self.minor}.{self.patch}{'b' if self.beta else ''}"


# md2anki general information
MD2ANKI_NAME: Final = "md2anki"
MD2ANKI_NAME_GIT: Final = "Md2Anki"
MD2ANKI_AUTHOR: Final = "AnonymerNiklasistanonym"
MD2ANKI_DESCRIPTION: Final = "Convert Markdown formatted documents to anki decks"
MD2ANKI_URL: Final = f"https://github.com/AnonymerNiklasistanonym/{MD2ANKI_NAME_GIT}"
MD2ANKI_URL_SOURCE_CODE: Final = MD2ANKI_URL
MD2ANKI_URL_GIT: Final = f"{MD2ANKI_URL}.git"
MD2ANKI_URL_BUG_TRACKER: Final = f"{MD2ANKI_URL}/issues"
MD2ANKI_VERSION: Final = ProgramVersion(major=3, minor=0, patch=20, beta=True)

# md2anki Markdown preprocessor information
MD2ANKI_MD_PP_ANKI_DECK_HEADING_SUBDECK_PREFIX: Final = "Subdeck: "
MD2ANKI_MD_PP_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR: Final = "---"
MD2ANKI_MD_PP_EVALUATE_CODE_LANGUAGE_PREFIX: Final = "="
MD2ANKI_MD_PP_COMMENT_INSERT_FILE_PREFIX = f"{MD2ANKI_NAME.upper()}_INSERT_FILE="
MD2ANKI_MD_PP_MD2ANKI_TAG_PREFIX = "{=:"
MD2ANKI_MD_PP_MD2ANKI_TAG_SUFFIX = ":=}"
MD2ANKI_MD_PP_MD2ANKI_MODEL_PREFIX = "{=<"
MD2ANKI_MD_PP_MD2ANKI_MODEL_SUFFIX = ">=}"

# md2anki evaluate code information
MD2ANKI_EVALUATE_CODE_ENV_NAME_ANKI_HTML_BOOL = f"{MD2ANKI_NAME.upper()}_ANKI_HTML"
MD2ANKI_EVALUATE_CODE_ENV_NAME_PANDOC_PDF_BOOL = f"{MD2ANKI_NAME.upper()}_PANDOC_PDF"
