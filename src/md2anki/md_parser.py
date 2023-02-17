#!/usr/bin/env python3

# Internal packages
import copy
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Optional, TextIO, List, Tuple, Final

# Local modules
from md2anki.anki_deck import AnkiDeck, AnkiNote
from md2anki.create_id import create_unique_id_int, create_unique_id
from md2anki.info import (
    ANKI_SUBDECK_SEPARATOR,
    MD_ANKI_DECK_HEADING_SUBDECK_PREFIX,
    MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR,
)

REGEX_MD_ANKI_DECK_HEADING: Final = re.compile(r"^(#+)\s+(.+?)(?:\s+\((\d+)\))?\s*$")
"""
Group 1: anki deck heading depth
Group 2: anki deck heading text
Group 3: anki deck id (optional)
"""
REGEX_MD_ANKI_NOTE_QUESTION_HEADING: Final = re.compile(
    r"^(##+)\s+(.+?)(?:\s+\(([^()\s]+?)\))?\s*$"
)
"""
Group 1: anki note question heading depth
Group 2: anki note question heading text
Group 3: anki note id (optional)
"""

log = logging.getLogger(__name__)


class NoAnkiDeckFoundException(Exception):
    """Raised when no anki deck is found"""

    pass


class RootAnkiDeckWasSubdeckException(Exception):
    """Raised when the root anki deck is a subdeck"""

    pass


class AnkiNoteUnexpectedDepth(Exception):
    """Raised when an anki note is found at an unexpected depth"""

    pass


class AnkiSubdeckUnexpectedDepth(Exception):
    """Raised when an anki subdeck is found at an unexpected depth"""

    pass


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


def parse_possible_anki_deck_heading(
    md_file_line: str, parent_deck_name: Optional[str] = None
) -> Optional[Tuple[AnkiDeck, int, bool]]:
    """
    Try to parse an anki (sub) deck heading from a Markdown file.

    @param md_file_line: The Markdown line.
    @param parent_deck_name: The current parent deck name in case this is a subdeck heading.
    @return: Anki (sub) deck with heading depth and subdeck indicator if match otherwise None.
    """
    regex_match: Final = REGEX_MD_ANKI_DECK_HEADING.match(md_file_line)

    if regex_match is not None:
        anki_deck_name = regex_match.group(2)
        anki_deck_guid = (
            int(regex_match.group(3))
            if regex_match.group(3) is not None
            else create_unique_id_int()
        )
        anki_deck_is_subdeck = anki_deck_name.startswith(
            MD_ANKI_DECK_HEADING_SUBDECK_PREFIX
        )
        if anki_deck_is_subdeck:
            if parent_deck_name is None:
                log.warning(
                    f"Found {anki_deck_name=} heading that is a subdeck but no parent deck name"
                )
            anki_deck_name = anki_deck_name[len(MD_ANKI_DECK_HEADING_SUBDECK_PREFIX) :]
        if parent_deck_name is not None:
            anki_deck_name = (
                f"{parent_deck_name}{ANKI_SUBDECK_SEPARATOR}{anki_deck_name}"
            )
        tmp_anki_deck = AnkiDeck(
            name=anki_deck_name,
            guid=anki_deck_guid,
        )
        return (
            tmp_anki_deck,
            len(regex_match.group(1)),
            anki_deck_is_subdeck,
        )
    return None


def parse_possible_anki_note_heading(
    md_file_line: str,
) -> Optional[Tuple[AnkiNote, int]]:
    regex_match: Final = REGEX_MD_ANKI_NOTE_QUESTION_HEADING.match(md_file_line)

    if regex_match is not None:
        return AnkiNote(
            question=regex_match.group(2),
            guid=regex_match.group(3)
            if regex_match.group(3) is not None
            else create_unique_id(),
        ), len(regex_match.group(1))
    return None


def parse_md_content_to_anki_deck_list(
    md_file: TextIO, md_file_dirs: List[Path], initial_heading_depth: int = 1
) -> List[AnkiDeck]:
    """
    Parse a Markdown file to an anki deck.

    @param md_file: The Markdown file content.
    @param md_file_dirs: The Markdown file directories of that file.
    @param initial_heading_depth: The initial Markdown heading depth.
    @return: Anki deck object list (in case sub decks are found).
    """
    anki_deck_order_index: int = 0
    """A counter to preserve the order of read anki deck headings"""
    empty_lines: int = 0
    """The amount of empty lines read"""
    parse_state: ParseStateMarkdownDocument = (
        ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING
    )
    """Parse state to know what information is currently being searched for"""
    anki_decks: Final[List[AnkiDeck]] = []
    """Final list of anki decks"""
    anki_decks_stack: Final[List[AnkiDeck]] = []
    """The current anki decks stack"""

    for line in md_file:
        log.debug(f"{line=!r} ({parse_state=},{empty_lines=},{anki_decks_stack=})")
        line_stripped = line.strip()

        if len(line_stripped) == 0:
            # 1. Skip empty lines but keep track of them
            empty_lines += 1
            log.debug(f"=> Found {empty_lines=}")
        elif parse_state == ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING:
            # 2. Look for a root anki deck heading
            possible_anki_deck = parse_possible_anki_deck_heading(line)
            if possible_anki_deck is not None:
                root_anki_deck, heading_depth, is_subdeck = possible_anki_deck
                log.debug(f"=> Found {root_anki_deck=}")
                if heading_depth != initial_heading_depth:
                    # Ignore root headings that are not in the specified initial depth
                    log.warning(
                        f"   -> Ignore {root_anki_deck=} because ({heading_depth=}!={initial_heading_depth=})"
                    )
                elif is_subdeck:
                    # Raise error if root heading is a subdeck
                    raise RootAnkiDeckWasSubdeckException(
                        f"The root anki deck heading can't be a subdeck ({line!r})"
                    )
                else:
                    # Add root anki deck to the stack
                    root_anki_deck.md_document_order = anki_deck_order_index
                    anki_deck_order_index += 1
                    anki_decks_stack.append(root_anki_deck)
                    # Change parse state to indicate that a root anki deck was found
                    parse_state = ParseStateMarkdownDocument.INSIDE_ANKI_DECK
        elif (
            parse_state == ParseStateMarkdownDocument.INSIDE_ANKI_DECK
            or parse_state == ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
            or parse_state == ParseStateMarkdownDocument.ANKI_NOTE_ANSWER
        ):
            # 3. Searching for an anki subdeck heading or anki note question heading
            # - INSIDE_ANKI_DECK: or an existing anki deck description
            # - ANKI_NOTE_QUESTION: or an existing anki note answer / question (if separator is found)
            # - ANKI_NOTE_ANSWER: or an existing anki note answer
            possible_anki_sub_deck = parse_possible_anki_deck_heading(
                line, parent_deck_name=anki_decks_stack[-1].name
            )
            possible_anki_note = parse_possible_anki_note_heading(line)
            if possible_anki_sub_deck is not None and possible_anki_sub_deck[2]:
                # A subdeck was detected
                (
                    anki_subdeck,
                    heading_depth,
                    is_subdeck,
                ) = possible_anki_sub_deck
                log.debug(f">> Detected {anki_subdeck=}")
                # If there is a change in heading depth pop subdecks from the stack that won't be referenced again
                if len(anki_decks_stack) > (heading_depth - initial_heading_depth):
                    deck_was_moved = False
                    # Store the old anki deck name before updating it
                    old_anki_parentdeck_name = anki_decks_stack[-1].name
                    # While the anki deck stack has more decks than the heading depth of the found subdeck indicated
                    while len(anki_decks_stack) > (
                        heading_depth - initial_heading_depth
                    ):
                        anki_decks.append(anki_decks_stack.pop())
                        log.debug(
                            f"<= [anki decks] Append {anki_decks[-1]!r} "
                            f"[{len(anki_decks_stack)=}>{heading_depth - initial_heading_depth=}]",
                        )
                        deck_was_moved = True
                    # Refresh sub deck name in case that the previous parent deck was removed from the stack
                    if deck_was_moved:
                        anki_subdeck.name = anki_subdeck.name.replace(
                            old_anki_parentdeck_name, anki_decks_stack[-1].name, 1
                        )
                        log.debug(
                            f">> Update {anki_subdeck.name=} ({old_anki_parentdeck_name=} was removed from the stack)"
                        )
                # Check if the subdeck heading depth is at the expected depth
                if len(anki_decks_stack) != (heading_depth - initial_heading_depth):
                    expected_heading_depth = (
                        len(anki_decks_stack) + initial_heading_depth
                    )
                    raise AnkiSubdeckUnexpectedDepth(
                        f"The found {anki_subdeck.name=} heading has an unexpected {heading_depth=} "
                        f"({expected_heading_depth=})"
                    )
                # Add all tags from the parent deck to the current subdeck
                anki_subdeck.tags = anki_subdeck.tags.union(
                    anki_decks_stack[-1].get_used_global_tags()
                )
                anki_subdeck.md_document_order = anki_deck_order_index
                anki_deck_order_index += 1
                anki_decks_stack.append(anki_subdeck)
                log.debug(
                    f"<= [anki deck stack] Append {anki_subdeck=}",
                )
                parse_state = ParseStateMarkdownDocument.INSIDE_ANKI_DECK
            elif possible_anki_note is not None:
                # A note was detected
                anki_note, heading_depth = possible_anki_note
                log.debug(f">> Detected {anki_note=}")
                # Check if the note heading depth is at a supported depth
                if heading_depth > (len(anki_decks_stack) + 1) or heading_depth < (
                    initial_heading_depth + 1
                ):
                    raise AnkiNoteUnexpectedDepth(
                        f"The found {anki_note=} has an unexpected {heading_depth=} "
                        f"({initial_heading_depth + 1=}<=expected_depth<={len(anki_decks_stack) + 1=})"
                    )
                # In case the note belongs to another deck append finished subdecks to the final list
                parent_deck_removed = False
                while len(anki_decks_stack) > (heading_depth - initial_heading_depth):
                    anki_subdeck = anki_decks_stack.pop()
                    anki_decks.append(anki_subdeck)
                    log.debug(
                        f"<= [anki decks | new anki note at smaller heading depth] Append {anki_subdeck=}",
                    )
                    parent_deck_removed = True
                # If a parent deck was removed create a copy of the deck to preserve order
                if parent_deck_removed:
                    anki_subdeck = anki_decks_stack.pop()
                    anki_decks.append(anki_subdeck)
                    log.debug(
                        f"<= [anki decks | parent deck was removed] Append {anki_subdeck=}",
                    )
                    anki_deck = copy.deepcopy(anki_subdeck)
                    anki_deck.notes = []
                    anki_deck.md_document_order = anki_deck_order_index
                    anki_deck_order_index += 1
                    anki_decks_stack.append(anki_deck)
                    log.debug(f"<= [anki deck stack] Append {anki_deck=}")
                # Append the note to the current anki deck
                anki_deck = anki_decks_stack[-1]
                anki_deck.notes.append(anki_note)
                log.debug(
                    f"<= [anki deck | new anki note] Append {anki_note=} ({anki_deck.name=}, {anki_deck.guid=})",
                )
                parse_state = ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
            elif parse_state == ParseStateMarkdownDocument.INSIDE_ANKI_DECK:
                # Update the current anki deck description
                anki_deck = anki_decks_stack[-1]
                anki_deck.description += empty_lines * "\n" + line
                empty_lines = 0
                log.debug(
                    f"=> Found/Update {anki_deck.description=} ({anki_deck.name=}, {anki_deck.guid=})",
                )
            elif (
                parse_state == ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
                and line_stripped == MD_ANKI_NOTE_QUESTION_ANSWER_SEPARATOR
            ):
                # Append read anki note answer to question and reset answer
                anki_note = anki_decks_stack[-1].notes[-1]
                anki_note.question = (
                    f"{anki_note.question.rstrip()}\n\n{anki_note.answer.lstrip()}"
                )
                anki_note.answer = ""
                log.debug(
                    f"=> Found question answer seperator/Update {anki_note.question=} ({anki_note.guid=})",
                )
                # Switch parse state to make sure future separators are being kept in the answer
                parse_state = ParseStateMarkdownDocument.ANKI_NOTE_ANSWER
            elif (
                parse_state == ParseStateMarkdownDocument.ANKI_NOTE_QUESTION
                or parse_state == ParseStateMarkdownDocument.ANKI_NOTE_ANSWER
            ):
                anki_note = anki_decks_stack[-1].notes[-1]
                anki_note.answer += empty_lines * "\n" + line
                empty_lines = 0
                log.debug(f"=> Found/Update {anki_note.answer=}")

    # Append yet not appended anki decks (in the correct order!)
    for anki_deck in anki_decks_stack:
        anki_decks.append(anki_deck)
        log.debug(f"<= [anki decks | reached eof] Append {anki_deck=}")

    if parse_state == ParseStateMarkdownDocument.LOOKING_FOR_ANKI_DECK_HEADING:
        raise NoAnkiDeckFoundException

    # Clean up descriptions of all anki decks as well as their notes
    for parent_anki_deck in anki_decks:
        parent_anki_deck.additional_file_dirs.extend(md_file_dirs)
        parent_anki_deck.description = parent_anki_deck.description.strip()
        for anki_note in parent_anki_deck.notes:
            anki_note.tags = anki_note.tags.union(
                parent_anki_deck.get_used_global_tags()
            )
            anki_note.question = anki_note.question.strip()
            anki_note.answer = anki_note.answer.strip()

    # Sort anki decks in order of their document order
    anki_decks.sort(key=lambda x: x.md_document_order)

    log.debug(
        f"=> Return anki decks: ({', '.join([f'{a.name} ({len(a.notes)})' for a in anki_decks])})",
    )

    return anki_decks
