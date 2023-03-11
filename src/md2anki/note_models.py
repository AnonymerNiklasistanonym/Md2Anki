#!/usr/bin/env python3

# Internal packages
from enum import Enum
from pathlib import Path
from typing import Final

# Local modules
from md2anki.anki_deck import AnkiModel
from md2anki.info.files import (
    RELATIVE_RES_CSS_FILE_PATH,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER,
)
from md2anki.info.general import MD2ANKI_NAME

CURRENT_DIR: Final = Path(__file__).parent
CSS_FILE_PATH: Final = CURRENT_DIR.joinpath(RELATIVE_RES_CSS_FILE_PATH)
CSS_FILE_PATH_TYPE_ANSWER: Final = CURRENT_DIR.joinpath(
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER
)


class AnkiCardModelId(Enum):
    DEFAULT = f"{MD2ANKI_NAME}_default"
    TYPE_ANSWER = f"{MD2ANKI_NAME}_type_answer"

    def __str__(self):
        return self.value


def create_type_answer_anki_deck_model() -> AnkiModel:
    with open(CSS_FILE_PATH, "r") as file:
        css_data = file.read()
    with open(CSS_FILE_PATH_TYPE_ANSWER, "r") as file:
        css_data += file.read()
    return AnkiModel(
        guid=396500203,
        name=f"{MD2ANKI_NAME} {AnkiCardModelId.TYPE_ANSWER.value} (v3)",
        description=f"{MD2ANKI_NAME} (type answer)",
        css=css_data,
        template_card_question='<div class="card card_question">{{Question}}</div>\n\n{{type:Answer}}',
        template_card_question_surround=("", ""),
        template_card_answer_front_side='<div class="card card_question">{{Question}}</div>\n\n<hr id="answer">\n\n',
        template_card_answer="{{type:Answer}}",
    )


def create_default_anki_deck_model() -> AnkiModel:
    with open(CSS_FILE_PATH, "r") as file:
        css_data = file.read()
    return AnkiModel(
        guid=396500103,
        name=f"{MD2ANKI_NAME} {AnkiCardModelId.DEFAULT.value} (v3)",
        description=f"{MD2ANKI_NAME} (default)",
        css=css_data,
    )
