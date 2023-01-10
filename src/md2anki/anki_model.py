from dataclasses import dataclass
from typing import Tuple

import genanki

from md2anki.create_id import create_unique_id_int


@dataclass
class AnkiModel:
    """
    Contains all information of an anki model (for anki notes of an anki deck)
    """

    name: str = ""
    """Model name"""
    description: str = ""
    """Model description"""
    css: str = ""
    """Style information (CSS code) for each anki note"""
    js: str = ""
    """Script information (JS code) for each anki note"""
    guid: int = create_unique_id_int()
    """Unique id of anki model"""
    template_card_question: str = "{{Question}}"
    """Card question template"""
    template_card_question_surround: Tuple[str, str] = (
        '<div class="card card_question">',
        "</div>",
    )
    """Card question template content before and after"""
    template_card_answer_front_side: str = '{{FrontSide}}<hr id="answer">'
    """Card answer front side"""
    template_card_answer: str = "{{Answer}}"
    """Card answer text"""
    template_card_answer_surround: Tuple[str, str] = (
        '<div class="card card_answer">',
        "</div>",
    )
    """Card answer template content before and after"""

    def genanki_create_model(self) -> genanki.Model:
        return genanki.Model(
            self.guid,
            self.description,
            fields=[{"name": "Question"}, {"name": "Answer"}],
            css=self.css,
            templates=[
                {
                    "name": self.name,
                    "qfmt": f"{self.js}\n{self.template_card_question_surround[0]}\n{self.template_card_question}\n"
                    f"{self.template_card_question_surround[1]}",
                    "afmt": f"{self.template_card_answer_front_side}{self.template_card_answer_surround[0]}\n"
                    f"{self.template_card_answer}\n{self.template_card_answer_surround[1]}",
                }
            ],
        )
