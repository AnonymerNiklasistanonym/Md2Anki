#!/usr/bin/env python3

# Internal packages
from enum import Enum
from pathlib import Path
from typing import Final

# Local modules
from md2anki.anki_model import AnkiModel
from md2anki.info.files import (
    RELATIVE_RES_CSS_FILE_PATH,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_CLOZE,
)
from md2anki.info.general import MD2ANKI_NAME

CURRENT_DIR: Final = Path(__file__).parent
CSS_FILE_PATH: Final = CURRENT_DIR.joinpath(RELATIVE_RES_CSS_FILE_PATH)
CSS_FILE_PATH_TYPE_ANSWER: Final = CURRENT_DIR.joinpath(
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER
)
CSS_FILE_PATH_TYPE_CLOZE: Final = CURRENT_DIR.joinpath(
    RELATIVE_RES_CSS_FILE_PATH_TYPE_CLOZE
)


class AnkiCardModelId(Enum):
    DEFAULT = f"{MD2ANKI_NAME}_type_default"
    TYPE_ANSWER = f"{MD2ANKI_NAME}_type_answer"
    TYPE_CLOZE = f"{MD2ANKI_NAME}_type_cloze"
    TYPE_CLOZE_EXTRA = f"{MD2ANKI_NAME}_type_cloze_extra"

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


def create_type_cloze_anki_deck_model(extra=False) -> AnkiModel:
    with open(CSS_FILE_PATH, "r") as file:
        css_data = file.read()
    with open(CSS_FILE_PATH_TYPE_CLOZE, "r") as file:
        css_data += file.read()
    return AnkiModel(
        guid=396500402 if extra else 396500302,
        name=f"{MD2ANKI_NAME} {AnkiCardModelId.TYPE_CLOZE_EXTRA.value if extra else AnkiCardModelId.TYPE_CLOZE.value} (v2)",
        description=f"{MD2ANKI_NAME} (type cloze{' extra' if extra else ''})",
        fields=["Text", "Extra"] if extra else ["Text"],
        css=css_data,
        cloze=True,
        template_card_question="{{cloze:Text}}",
        template_card_answer='{{cloze:Text}}<hr id="answer">{{Extra}}'
        if extra
        else "{{cloze:Text}}",
        template_card_answer_front_side="",
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
