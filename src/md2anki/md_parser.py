import re
from enum import Enum
from typing import Optional, TextIO, List, Tuple

from md2anki.anki_deck import AnkiDeck, AnkiNote
from md2anki.create_id import create_unique_id_int, create_unique_id
from md2anki.info import (
    ANKI_SUBDECK_SEPARATOR,
    MD_ANKI_DECK_HEADING_SUBDECK_PREFIX,
    MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR,
)

REGEX_MD_ANKI_DECK_HEADING = re.compile(r"^(#+)\s+(.+?)(?:\s+\((\d+)\))?\s*$")
"""
Group 1: anki deck heading depth
Group 2: anki deck heading text
Group 3: anki deck id (optional)
"""
REGEX_MD_ANKI_NOTE_QUESTION_HEADING = re.compile(
    r"^(##+)\s+(.+?)(?:\s+\(([^()\s]+?)\))?\s*$"
)
"""
Group 1: anki note question heading depth
Group 2: anki note question heading text
Group 3: anki note id (optional)
"""


class ParseStateMarkdownDocument(str, Enum):
    """
    Parse states of the Markdown document parser.
    """

    LOOKING_FOR_ANKI_DECK_HEADING = ("LOOKING_FOR_ANKI_DECK_HEADING",)
    """Nothing was yet detected, anki deck heading is expected."""
    INSIDE_ANKI_DECK = ("INSIDE_ANKI_DECK",)
    """Anki deck heading was read and an anki note question/sub deck heading or anki deck description is expected."""
    LOOKING_FOR_ANKI_SUBDECK_DESCRIPTION = ("LOOKING_FOR_ANKI_SUBDECK_DESCRIPTION",)
    """Anki sub deck heading was read and an anki note question/sub deck heading or anki subdeck description is 
    expected."""
    ANKI_NOTE_QUESTION = ("ANKI_NOTE_QUESTION",)
    """An anki note question heading was read and a question answer seperator or answer is expected."""
    ANKI_NOTE_ANSWER = ("ANKI_NOTE_ANSWER",)
    """An anki note question answer seperator was read and an answer is expected."""


class ParseStateMarkdownDocumentAction(str, Enum):
    """
    Parse states of the Markdown document parser actions.
    """

    NONE = ("NONE",)
    FOUND_ANKI_DECK_DESCRIPTION = ("FOUND_ANKI_DECK_DESCRIPTION",)
    FOUND_ANKI_SUBDECK_HEADING = ("FOUND_ANKI_SUBDECK_HEADING",)
    FOUND_ANKI_NOTE_QUESTION_HEADING = ("FOUND_ANKI_NOTE_QUESTION_HEADING",)
    FOUND_ANKI_NOTE_QUESTION_ANSWER = ("FOUND_ANKI_NOTE_QUESTION_ANSWER",)


def parse_possible_anki_deck_heading(
    md_file_line: str, parent_deck_name: Optional[str] = None
) -> Optional[Tuple[AnkiDeck, int, bool]]:
    """
    Try to parse an anki (sub) deck heading from a Markdown file.

    @param md_file_line: The Markdown line.
    @param parent_deck_name: The current parent deck name in case this is a subdeck heading.
    @return: Anki (sub) deck with heading depth and subdeck indicator if match otherwise None.
    """
    regex_match = REGEX_MD_ANKI_DECK_HEADING.match(md_file_line)

    if regex_match is not None:
        temp_anki_deck = AnkiDeck(
            name=f"{parent_deck_name + ANKI_SUBDECK_SEPARATOR if parent_deck_name is not None else ''}"
            f"{regex_match.group(2)}",
            guid=int(regex_match.group(3))
            if regex_match.group(3) is not None
            else create_unique_id_int(),
        )
        return (
            temp_anki_deck,
            len(regex_match.group(1)),
            regex_match.group(2).startswith(MD_ANKI_DECK_HEADING_SUBDECK_PREFIX),
        )


def parse_possible_anki_note_question_header(
    md_file_line: str,
) -> Optional[Tuple[AnkiNote, int]]:
    regex_match = REGEX_MD_ANKI_NOTE_QUESTION_HEADING.match(md_file_line)

    if regex_match is not None:
        temp_anki_note = AnkiNote(
            question=regex_match.group(2),
            guid=regex_match.group(3)
            if regex_match.group(3) is not None
            else create_unique_id(),
        )
        return temp_anki_note, len(regex_match.group(1))


def parse_md_file_to_anki_deck_list(
    text_file: TextIO, initial_heading_depth: int = 1, debug=False
) -> List[AnkiDeck]:
    """
    Parse a Markdown file to an anki deck.

    @param initial_heading_depth: The initial Markdown heading depth.
    @param text_file: The text file content.
    @param debug: Enable debug output.
    @return: Anki deck object list (in case sub decks are found).
    """
    # Parse variables
    empty_lines: int = 0
    parse_state: ParseStateMarkdownDocument = (
        ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING
    )
    parse_state_action: ParseStateMarkdownDocumentAction = (
        ParseStateMarkdownDocumentAction.NONE
    )
    current_anki_note: Optional[AnkiNote] = None
    found_depth: int = 0
    new_anki_subdeck: Optional[AnkiDeck] = None
    new_anki_note: Optional[AnkiNote] = None

    # Output list
    anki_decks: List[AnkiDeck] = []
    anki_decks_stack: List[AnkiDeck] = []

    for line in text_file:
        if debug:
            print(f"{line=!r} ({parse_state=} {empty_lines=})")

        # Skip empty lines but track them
        line_stripped = line.strip()
        if len(line_stripped) == 0:
            empty_lines += 1
            if debug:
                print(f">> Found empty line ({empty_lines=})")
            continue

        # Parse states
        if parse_state == ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING:
            # Searching for an anki deck
            possible_anki_deck = parse_possible_anki_deck_heading(line)
            if possible_anki_deck is not None:
                new_anki_deck, found_depth, found_subdeck = possible_anki_deck
                if found_depth == initial_heading_depth:
                    anki_decks_stack.append(new_anki_deck)
                    parse_state = ParseStateMarkdownDocument.INSIDE_ANKI_DECK
                    empty_lines = 0
                    if debug:
                        print(
                            f">> Found anki deck heading line ({new_anki_deck.name=}, {new_anki_deck.guid=})"
                        )
                elif debug:
                    print(
                        ">> Found anki deck heading line but ignore it because of the heading depth "
                        f"({new_anki_deck.name=}, {found_depth=}, {initial_heading_depth=})"
                    )
        elif (
            parse_state == ParseStateMarkdownDocument.INSIDE_ANKI_DECK
            or parse_state == ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
            or parse_state == ParseStateMarkdownDocument.ANKI_NOTE_ANSWER
        ):
            # Searching for an anki subdeck heading or anki note question heading
            # - INSIDE_ANKI_DECK: or an existing anki deck description
            # - ANKI_NOTE_QUESTION: or an existing anki note answer / question (if separator is found)
            # - ANKI_NOTE_ANSWER: or an existing anki note answer
            possible_anki_sub_deck = parse_possible_anki_deck_heading(
                line, parent_deck_name=anki_decks_stack[-1].name
            )
            possible_anki_note = parse_possible_anki_note_question_header(line)
            if possible_anki_sub_deck is not None and possible_anki_sub_deck[2]:
                new_anki_subdeck, found_depth, found_subdeck = possible_anki_sub_deck
                parse_state_action = (
                    ParseStateMarkdownDocumentAction.FOUND_ANKI_SUBDECK_HEADING
                )
            elif possible_anki_note is not None:
                new_anki_note, found_depth = possible_anki_note
                parse_state_action = (
                    ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_HEADING
                )
            elif parse_state == ParseStateMarkdownDocument.INSIDE_ANKI_DECK:
                parse_state_action = (
                    ParseStateMarkdownDocumentAction.FOUND_ANKI_DECK_DESCRIPTION
                )
            elif parse_state == ParseStateMarkdownDocument.ANKI_NOTE_QUESTION:
                if line_stripped == MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR:
                    # Append current anki note answer to question
                    current_anki_note.question += (
                        f"\n\n{current_anki_note.answer.strip()}"
                    )
                    current_anki_note.answer = ""
                    # Switch parse state to make sure future separators are being kept in the answer
                    parse_state = ParseStateMarkdownDocument.ANKI_NOTE_ANSWER
                    empty_lines = 0
                    if debug:
                        print(
                            f">> Found anki note question answer seperator line ({current_anki_note.question=!r})"
                        )
                else:
                    parse_state_action = (
                        ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_ANSWER
                    )
            elif parse_state == ParseStateMarkdownDocument.ANKI_NOTE_ANSWER:
                parse_state_action = (
                    ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_ANSWER
                )

        # Append anki subdecks if there is a change in heading depth
        if len(anki_decks_stack) > 1:
            if (
                parse_state_action
                == ParseStateMarkdownDocumentAction.FOUND_ANKI_SUBDECK_HEADING
            ):
                deck_was_moved = False
                old_parent_name = anki_decks_stack[-1].name
                while len(anki_decks_stack) > (found_depth - initial_heading_depth):
                    anki_decks_stack[-1].description = anki_decks_stack[
                        -1
                    ].description.strip()
                    anki_decks.append(anki_decks_stack.pop())
                    deck_was_moved = True
                    if debug:
                        print(
                            f"=> Append anki deck from stack to anki deck list [depth-diff] ({anki_decks[-1].name=}, "
                            f"{anki_decks[-1].notes=})"
                        )
                # Refresh sub deck name in case any subdecks were appended
                if deck_was_moved:
                    new_anki_subdeck.name = new_anki_subdeck.name.replace(
                        old_parent_name, anki_decks_stack[-1].name
                    )
                    if debug:
                        print(
                            f">> Refresh anki subdeck name [deck-moved] ({old_parent_name=}, {new_anki_subdeck.name=})"
                        )

        # Append notes that are not yet appended
        if current_anki_note is not None:
            if (
                parse_state_action
                == ParseStateMarkdownDocumentAction.FOUND_ANKI_SUBDECK_HEADING
                or parse_state_action
                == ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_HEADING
            ):
                current_anki_note.tags = current_anki_note.tags.union(
                    anki_decks_stack[-1].get_used_global_tags()
                )
                current_anki_note.question = current_anki_note.question.strip()
                current_anki_note.answer = current_anki_note.answer.strip()
                anki_decks_stack[-1].notes.append(current_anki_note)
                current_anki_note = None
                if debug:
                    print(
                        f"=> Append current anki note to anki deck of current depth ({anki_decks_stack[-1].notes[-1]=}, "
                        f"{anki_decks_stack[-1].name=}"
                    )

        # Actions to perform based on information from parse states
        if (
            parse_state_action
            == ParseStateMarkdownDocumentAction.FOUND_ANKI_DECK_DESCRIPTION
        ):
            # no parse state change necessary
            anki_decks_stack[-1].description += empty_lines * "\n" + line
            empty_lines = 0
            if debug:
                print(
                    f">> Found anki deck description line ({anki_decks_stack[-1].description=!r})"
                )
        elif (
            parse_state_action
            == ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_HEADING
        ):
            if found_depth > (len(anki_decks_stack) + 1) or found_depth < (
                initial_heading_depth + 1
            ):
                raise RuntimeError(
                    f"The found anki note has an unexpected depth ({found_depth=}, "
                    f"expected_depth={initial_heading_depth + 1}-{len(anki_decks_stack) + 1}, "
                    f"{new_anki_note=})"
                )
            current_anki_note = new_anki_note
            new_anki_note = None
            parse_state = ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
            empty_lines = 0
            if debug:
                print(f"> Found new anki note question heading line ({new_anki_note=})")
        elif (
            parse_state_action
            == ParseStateMarkdownDocumentAction.FOUND_ANKI_NOTE_QUESTION_ANSWER
        ):
            current_anki_note.answer += empty_lines * "\n" + line
            empty_lines = 0
            if debug:
                print(f">> Found answer line ({current_anki_note.answer=!r})")
        elif (
            parse_state_action
            == ParseStateMarkdownDocumentAction.FOUND_ANKI_SUBDECK_HEADING
        ):
            if (found_depth - initial_heading_depth + 1) != len(anki_decks_stack) + 1:
                raise RuntimeError(
                    f"The found anki subdeck heading has an unexpected depth ({found_depth=}, "
                    f"expected_depth={len(anki_decks_stack) + 1}, {new_anki_subdeck.name=})"
                )
            anki_decks_stack.append(new_anki_subdeck)
            new_anki_subdeck = None
            parse_state = ParseStateMarkdownDocument.INSIDE_ANKI_DECK
            empty_lines = 0
            if debug:
                print(f">> Found anki subdeck heading line ({anki_decks_stack[-1]=})")

        parse_state_action = ParseStateMarkdownDocumentAction.NONE

    # Append not yet appended anki note
    if current_anki_note is not None:
        current_anki_note.tags = current_anki_note.tags.union(
            anki_decks_stack[-1].get_used_global_tags()
        )
        current_anki_note.question = current_anki_note.question.strip()
        current_anki_note.answer = current_anki_note.answer.strip()
        anki_decks_stack[-1].notes.append(current_anki_note)
        if debug:
            print(f"=> Append last anki note to anki deck ({current_anki_note=})")

    # Append yet not appended anki decks
    for anki_deck in anki_decks_stack:
        anki_deck.description = anki_deck.description.strip()
        anki_decks.append(anki_deck)
        if debug:
            print(
                f"=> Append anki deck from stack to anki deck list [finished-file] ({anki_decks[-1].name=}, "
                f"{anki_decks[-1].notes=})"
            )

    if parse_state == ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING:
        raise RuntimeError("Never found a anki deck heading in the Markdown content")

    if debug:
        print(
            f"=> Return anki decks: ({', '.join([f'{a.name} ({len(a.notes)})' for a in anki_decks])})"
        )

    return anki_decks
