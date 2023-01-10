#!/usr/bin/env python3

# Internal packages
import os
from enum import Enum

# Local modules
from md2anki.anki_deck import AnkiModel
from md2anki.info import (
    md2anki_name,
    RELATIVE_CSS_FILE_PATH,
    RELATIVE_CSS_FILE_PATH_TYPE_ANSWER,
)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CSS_FILE_PATH = os.path.join(CURRENT_DIR, RELATIVE_CSS_FILE_PATH)
CSS_FILE_PATH_TYPE_ANSWER = os.path.join(
    CURRENT_DIR, RELATIVE_CSS_FILE_PATH_TYPE_ANSWER
)


class AnkiCardModelId(Enum):
    DEFAULT = "md2anki_default"
    TYPE_ANSWER = "md2anki_type_answer"

    def __str__(self):
        return self.value


def create_type_answer_anki_deck_model() -> AnkiModel:
    with open(CSS_FILE_PATH, "r") as file:
        css_data = file.read().replace("\n", "")
    with open(CSS_FILE_PATH_TYPE_ANSWER, "r") as file:
        css_data += file.read().replace("\n", "")
    return AnkiModel(
        guid=396500202,
        name=f"{md2anki_name} {AnkiCardModelId.TYPE_ANSWER.value} (v2)",
        description=f"{md2anki_name} (type answer)",
        css=css_data,
        template_card_question='<div class="card card_question">{{Question}}</div>\n\n{{type:Answer}}',
        template_card_question_surround=("", ""),
        template_card_answer_front_side='<div class="card card_question">{{Question}}</div>\n\n<hr id="answer">\n\n',
        template_card_answer="{{type:Answer}}",
    )


def create_default_anki_deck_model() -> AnkiModel:
    with open(CSS_FILE_PATH, "r") as file:
        css_data = file.read().replace("\n", "")
    return AnkiModel(
        guid=396500102,
        name=f"{md2anki_name} {AnkiCardModelId.DEFAULT.value} (v2)",
        description=f"{md2anki_name} (default)",
        css=css_data,
    )
