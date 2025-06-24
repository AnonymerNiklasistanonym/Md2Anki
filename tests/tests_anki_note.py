#!/usr/bin/env python3

# Internal packages
import sys
import unittest
from pathlib import Path
from typing import List, Tuple, Set

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.anki_note import AnkiNote, MdSection
from md2anki.cli import (
    DEFAULT_CUSTOM_PROGRAMS,
    convert_list_to_dict_merged,
    str_to_str,
    json_str_to_str_list,
    DEFAULT_CUSTOM_PROGRAM_ARGS,
)
from md2anki.note_models import AnkiCardModelId


class TestAnkiNoteGeneric(unittest.TestCase):
    def setUp(self):
        self.anki_note_list: List[AnkiNote] = list()
        self.expected_tags: List[Set[str]] = list()
        self.expected_local_files: List[Set[Path]] = list()
        self.expected_md_sections: List[Tuple[MdSection, MdSection]] = list()
        self.expected_anki_output: List[Tuple[str, str]] = list()
        self.results_tags: List[Set[str]] = list()
        self.results_local_files: List[Set[Path]] = list()
        self.results_md_sections: List[Tuple[MdSection, MdSection]] = list()
        self.results_anki_output: List[Tuple[str, str]] = list()

        dir_dynamic_files = Path(__file__).parent.joinpath("dynamic_files")
        local_asset_dir = Path("assets")

        test_data: List[
            Tuple[
                AnkiNote,
                Set[str],
                Set[Path],
                Tuple[MdSection, MdSection],
                Tuple[str, str],
            ]
        ] = [
            (
                AnkiNote(
                    question="question", answer="answer", tags={"tag"}, guid="1234"
                ),
                {"tag"},
                set(),
                (
                    MdSection(heading="question", heading_id="1234", content="answer"),
                    MdSection(heading="question", heading_id="1234", content="answer"),
                ),
                ("<p>question</p>", "<p>answer</p>"),
            ),
            (
                AnkiNote(
                    question="question\n`{=:note_tag:=}`",
                    answer="answer $66 * 42 = 10$ ![](res/wikipedia_svg_demo.svg)",
                    guid="1234",
                ),
                {"note_tag"},
                {Path("res/wikipedia_svg_demo.svg")},
                (
                    MdSection(
                        heading="question",
                        heading_id="1234",
                        content="`{=:note_tag:=}`\n\n---\n\nanswer $66 * 42 = 10$ ![](res/wikipedia_svg_demo.svg)",
                    ),
                    MdSection(
                        heading="question",
                        heading_id="1234",
                        content="`{=:note_tag:=}`"
                        + f"\n\n---\n\nanswer $66 * 42 = 10$ ![]({local_asset_dir.joinpath('wikipedia_svg_demo.svg')})",
                    ),
                ),
                (
                    "<p>question</p>",
                    '<p>answer \\(66 * 42 = 10\\) <img alt="" src="wikipedia_svg_demo.svg" style=""/></p>',
                ),
            ),
        ]

        for (
            test_input,
            test_expected_tags,
            test_expected_local_files,
            test_expected_md_section,
            test_expected_anki_output,
        ) in test_data:
            self.anki_note_list.append(test_input)
            self.expected_tags.append(test_expected_tags)
            self.expected_local_files.append(test_expected_local_files)
            self.expected_md_sections.append(test_expected_md_section)
            self.expected_anki_output.append(test_expected_anki_output)
            self.results_tags.append(test_input.get_used_md2anki_tags())
            self.results_local_files.append(test_input.get_used_local_files())
            self.results_md_sections.append(
                (
                    test_input.create_md_section(),
                    test_input.create_md_section(local_asset_dir_path=local_asset_dir),
                )
            )
            self.results_anki_output.append(
                tuple(
                    test_input.genanki_create_note(
                        default_anki_card_model=f"{AnkiCardModelId.DEFAULT}",
                        dir_dynamic_files=dir_dynamic_files,
                        custom_program=convert_list_to_dict_merged(
                            DEFAULT_CUSTOM_PROGRAMS, str_to_str
                        ),
                        custom_program_args=convert_list_to_dict_merged(
                            DEFAULT_CUSTOM_PROGRAM_ARGS, json_str_to_str_list
                        ),
                        external_file_dirs=[],
                    ).fields
                )
            )

    def test_anki_note_tags_same(self):
        for anki_note, expected_tags, result_tags in zip(
            self.anki_note_list,
            self.expected_tags,
            self.results_tags,
        ):
            with self.subTest(anki_note=anki_note):
                self.assertEqual(
                    expected_tags,
                    result_tags,
                    f"Check if anki note {expected_tags=}=={result_tags=}",
                )

    def test_anki_note_local_files_same(self):
        for anki_note, expected_local_files, result_local_files in zip(
            self.anki_note_list,
            self.expected_local_files,
            self.results_local_files,
        ):
            with self.subTest(anki_note=anki_note):
                self.assertEqual(
                    expected_local_files,
                    result_local_files,
                    f"Check if anki note {expected_local_files=}=={result_local_files=}",
                )

    def test_anki_note_md_section_same(self):
        for anki_note, expected_md_section, result_md_section in zip(
            self.anki_note_list,
            self.expected_md_sections,
            self.results_md_sections,
        ):
            with self.subTest(anki_note=anki_note):
                self.assertEqual(
                    expected_md_section,
                    result_md_section,
                    f"Check if anki note {expected_md_section=}=={result_md_section=}",
                )

    def test_anki_note_anki_output_same(self):
        for anki_note, expected_anki_output, result_anki_output in zip(
            self.anki_note_list,
            self.expected_anki_output,
            self.results_anki_output,
        ):
            with self.subTest(anki_note=anki_note):
                self.assertEqual(
                    expected_anki_output,
                    result_anki_output,
                    f"Check if anki note {expected_anki_output=}=={result_anki_output=}",
                )
