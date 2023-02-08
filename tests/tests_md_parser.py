import sys
import io
import unittest
from os.path import dirname, join
from typing import List, Tuple, Optional

from md2anki.anki_deck import AnkiDeck
from md2anki.anki_note import AnkiNote
from md2anki.md_parser import (
    parse_possible_anki_deck_heading,
    parse_possible_anki_note_heading,
    parse_md_content_to_anki_deck_list,
    NoAnkiDeckFoundException,
    RootAnkiDeckWasSubdeckException,
    AnkiNoteUnexpectedDepth,
    AnkiSubdeckUnexpectedDepth,
)


class TestParsePossibleAnkiDeckHeading(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.parent_deck_list: List[Optional[str]] = list()
        self.deck_id_list: List[bool] = list()
        self.results: List[Optional[Tuple[AnkiDeck, int, bool]]] = list()
        self.expected: List[Optional[Tuple[AnkiDeck, int, bool]]] = list()

        test_data: List[
            Tuple[str, Optional[str], bool, Optional[Tuple[AnkiDeck, int, bool]]]
        ] = [
            ("", None, False, None),
            ("just text", None, False, None),
            ("# Heading", None, False, (AnkiDeck(name="Heading"), 1, False)),
            (
                "# Heading (12345)",
                None,
                True,
                (AnkiDeck(name="Heading", guid=12345), 1, False),
            ),
            ("## Heading", None, False, (AnkiDeck(name="Heading"), 2, False)),
            (
                "## Subdeck: Heading",
                "parent deck",
                False,
                (AnkiDeck(name="parent deck::Heading"), 2, True),
            ),
            (
                "## Subdeck: Heading (12367)",
                "parent deck",
                True,
                (AnkiDeck(name="parent deck::Heading", guid=12367), 2, True),
            ),
            ("## Subdeck: Heading", None, False, (AnkiDeck(name=f"Heading"), 2, True)),
        ]

        for test_input, test_parent_deck, test_deck_id, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.parent_deck_list.append(test_parent_deck)
            self.deck_id_list.append(test_deck_id)
            self.results.append(
                parse_possible_anki_deck_heading(
                    test_input, parent_deck_name=test_parent_deck
                )
            )
            self.expected.append(test_expected)

    def test_parsed_possible_anki_deck_same(self):
        for md_content, parent_deck, deck_id, result, expected in zip(
            self.md_content_list,
            self.parent_deck_list,
            self.deck_id_list,
            self.results,
            self.expected,
            strict=True,
        ):
            with self.subTest(
                md_content=md_content, parent_deck_name=parent_deck, deck_id=deck_id
            ):
                if expected is None:
                    self.assertIsNone(
                        result,
                        f"Check if parsed anki deck None {result=}",
                    )
                elif result is None:
                    self.fail(f"{result=} was None but something else was {expected=}")
                else:
                    self.assertEqual(
                        result[0].name,
                        expected[0].name,
                        f"Check if parsed anki deck name {result[0].name=}=={expected[0].name=}",
                    )
                    if deck_id:
                        self.assertEqual(
                            result[0].guid,
                            expected[0].guid,
                            f"Check if parsed anki deck guid {result[0].guid=}=={expected[0].guid=}",
                        )
                    self.assertEqual(
                        result[1],
                        expected[1],
                        f"Check if parsed anki deck level {result[1]=}=={expected[1]=}",
                    )
                    self.assertEqual(
                        result[2],
                        expected[2],
                        f"Check if parsed anki deck subdeck {result[2]=}=={expected[2]=}",
                    )


class TestParsePossibleAnkiNoteQuestionHeader(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.note_id_list: List[bool] = list()
        self.results: List[Optional[Tuple[AnkiNote, int]]] = list()
        self.expected: List[Optional[Tuple[AnkiNote, int]]] = list()

        test_data: List[Tuple[str, bool, Optional[Tuple[AnkiNote, int]]]] = [
            ("", False, None),
            ("just text", False, None),
            ("# Heading", False, None),
            ("## Heading", False, (AnkiNote(question="Heading"), 2)),
            (
                "## Heading (abcsdeef)",
                True,
                (AnkiNote(question="Heading", guid="abcsdeef"), 2),
            ),
        ]

        for test_input, test_note_id, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.note_id_list.append(test_note_id)
            self.results.append(parse_possible_anki_note_heading(test_input))
            self.expected.append(test_expected)

    def test_parsed_possible_anki_note_question_same(self):
        for md_content, note_id, result, expected in zip(
            self.md_content_list,
            self.note_id_list,
            self.results,
            self.expected,
            strict=True,
        ):
            with self.subTest(md_content=md_content, note_id=note_id):
                if expected is None:
                    self.assertIsNone(
                        result,
                        f"Check if parsed anki note None ({result=})",
                    )
                elif result is None:
                    self.assertTrue(
                        False,
                        f"Result should never be None ({result=}) if expected is not None ({expected=})",
                    )
                else:
                    result_anki_note, result_anki_note_heading_depth = result
                    expected_anki_note, expected_anki_note_heading_depth = expected
                    self.assertEqual(
                        result_anki_note.question,
                        expected_anki_note.question,
                        f"Check if {result_anki_note.question=}=={expected_anki_note.question=}",
                    )
                    if note_id:
                        self.assertEqual(
                            result_anki_note.guid,
                            expected_anki_note.guid,
                            f"Check if {result_anki_note.guid=}=={expected_anki_note.guid=}",
                        )
                    self.assertEqual(
                        result_anki_note_heading_depth,
                        expected_anki_note_heading_depth,
                        f"Check if {result_anki_note_heading_depth=}=={expected_anki_note_heading_depth=}",
                    )


class TestParseMdContentToAnkiDeckList(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.md_content_exception_list: List[str] = list()
        self.results: List[List[AnkiDeck]] = list()
        self.expected: List[List[AnkiDeck]] = list()
        self.expected_exception: List[Exception] = list()

        test_data: List[Tuple[str, List[AnkiDeck], Optional[Exception]]] = [
            (
                "",
                [],
                # type: ignore
                NoAnkiDeckFoundException,
            ),
            (
                "## Question",
                [],
                # type: ignore
                NoAnkiDeckFoundException,
            ),
            (
                "# Subdeck: Heading",
                [],
                # type: ignore
                RootAnkiDeckWasSubdeckException,
            ),
            (
                "# Heading\n\n### Question",
                [],
                # type: ignore
                AnkiNoteUnexpectedDepth,
            ),
            (
                "# Heading\n\n### Subdeck: Heading 2",
                [],
                # type: ignore
                AnkiSubdeckUnexpectedDepth,
            ),
            ("# Heading (1234)", [AnkiDeck(name="Heading", guid=1234)], None),
            (
                "# Heading (1234)\n\n" "## Question (abcdef)\n\nAnswer",
                [
                    AnkiDeck(
                        name="Heading",
                        guid=1234,
                        notes=[
                            AnkiNote(
                                question="Question", answer="Answer", guid="abcdef"
                            )
                        ],
                    )
                ],
                None,
            ),
            (
                "# Heading (12349)\n\n"
                "## Question 1 (abcdef)\n\nAnswer 1\n\n"
                "## Question 2 (abcdefg)\n\nMore question\n\n---\n\nAnswer 2",
                [
                    AnkiDeck(
                        name="Heading",
                        guid=12349,
                        notes=[
                            AnkiNote(
                                question="Question 1", answer="Answer 1", guid="abcdef"
                            ),
                            AnkiNote(
                                question="Question 2\n\nMore question",
                                answer="Answer 2",
                                guid="abcdefg",
                            ),
                        ],
                    )
                ],
                None,
            ),
            (
                "# Heading (1234)\n\n"
                "## Question 1 (abcdef)\n\nAnswer 1\n\n"
                "## Subdeck: Heading 2 (12345)\n\n"
                "### Question 2 (abcdefg)\n\nAnswer 2\n\n"
                "## Question 3 (abcdefgh)\n\nAnswer 3",
                [
                    AnkiDeck(
                        name="Heading",
                        guid=1234,
                        notes=[
                            AnkiNote(
                                question="Question 1", answer="Answer 1", guid="abcdef"
                            ),
                        ],
                    ),
                    AnkiDeck(
                        name="Heading::Heading 2",
                        guid=12345,
                        notes=[
                            AnkiNote(
                                question="Question 2", answer="Answer 2", guid="abcdefg"
                            ),
                        ],
                    ),
                    AnkiDeck(
                        name="Heading",
                        guid=1234,
                        notes=[
                            AnkiNote(
                                question="Question 3",
                                answer="Answer 3",
                                guid="abcdefgh",
                            ),
                        ],
                    ),
                ],
                None,
            ),
            (
                "# Heading (1234)\n\n`{=:global_tag:=}`\n\n"
                "## Question 1 (abcdef)\n\nAnswer 1\n\n"
                "## Subdeck: Heading 2 (12345)\n\n`{=:subdeck_tag:=}`\n\n"
                "### Question 2 (abcdefg)\n\nAnswer 2\n\n"
                "## Question 3 (abcdefgh)\n\nAnswer 3",
                [
                    AnkiDeck(
                        name="Heading",
                        guid=1234,
                        notes=[
                            AnkiNote(
                                question="Question 1",
                                answer="Answer 1",
                                guid="abcdef",
                                tags={"global_tag"},
                            ),
                        ],
                        tags={"global_tag"},
                    ),
                    AnkiDeck(
                        name="Heading::Heading 2",
                        guid=12345,
                        notes=[
                            AnkiNote(
                                question="Question 2",
                                answer="Answer 2",
                                guid="abcdefg",
                                tags={"global_tag", "subdeck_tag"},
                            ),
                        ],
                        tags={"global_tag", "subdeck_tag"},
                    ),
                    AnkiDeck(
                        name="Heading",
                        guid=1234,
                        notes=[
                            AnkiNote(
                                question="Question 3",
                                answer="Answer 3",
                                guid="abcdefgh",
                                tags={"global_tag"},
                            ),
                        ],
                        tags={"global_tag"},
                    ),
                ],
                None,
            ),
        ]

        for test_input, test_expected, test_expected_exception in test_data:
            if test_expected_exception is not None:
                self.md_content_exception_list.append(test_input)
                self.expected_exception.append(test_expected_exception)
            else:
                self.md_content_list.append(test_input)
                self.results.append(
                    parse_md_content_to_anki_deck_list(io.StringIO(test_input))
                )
                self.expected.append(test_expected)

    def test_parsed_anki_deck_list_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected, strict=True
        ):
            with self.subTest(md_content=md_content):
                for expected_anki_deck, result_anki_deck in zip(
                    expected, result, strict=True
                ):
                    self.assertEqual(
                        expected_anki_deck.name,
                        result_anki_deck.name,
                        f"Check if {expected_anki_deck.name=}=={result_anki_deck.name=}",
                    )
                    self.assertEqual(
                        expected_anki_deck.guid,
                        result_anki_deck.guid,
                        f"Check if {expected_anki_deck.guid=}=={result_anki_deck.guid=}",
                    )
                    result_anki_deck_all_tags = (
                        result_anki_deck.get_used_global_tags().union(
                            result_anki_deck.tags
                        )
                    )
                    self.assertSetEqual(
                        expected_anki_deck.tags,
                        result_anki_deck_all_tags,
                        f"Check if {expected_anki_deck.tags=}=={result_anki_deck_all_tags=}",
                    )
                    for expected_anki_note, result_anki_note in zip(
                        expected_anki_deck.notes,
                        result_anki_deck.notes,
                        strict=True,
                    ):
                        self.assertEqual(
                            expected_anki_note.guid,
                            result_anki_note.guid,
                            f"Check if {expected_anki_note.guid=}=={result_anki_note.guid=}",
                        )
                        self.assertEqual(
                            expected_anki_note.question,
                            result_anki_note.question,
                            f"Check if {expected_anki_note.question=}=={result_anki_note.question=}",
                        )
                        self.assertEqual(
                            expected_anki_note.answer,
                            result_anki_note.answer,
                            f"Check if {expected_anki_note.answer=}=={result_anki_note.answer=}",
                        )
                        self.assertSetEqual(
                            expected_anki_note.tags,
                            result_anki_note.tags,
                            f"Check if {expected_anki_note.tags=}=={result_anki_note.tags=}",
                        )

    def test_parsed_anki_deck_list_exception_same(self):
        for md_content, expected_exception in zip(
            self.md_content_exception_list, self.expected_exception, strict=True
        ):
            with self.subTest(md_content=md_content):
                # Ignore type error, is the correct type
                self.assertRaises(
                    # type: ignore
                    expected_exception,
                    parse_md_content_to_anki_deck_list,
                    io.StringIO(md_content),
                )
