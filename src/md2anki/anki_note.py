#!/usr/bin/env python3

# Internal packages
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Optional, Dict, List
from urllib.parse import ParseResult

# Installed packages
import genanki

# Local modules
from md2anki.create_id import create_unique_id
from md2anki.preprocessor import md_preprocessor_md2anki
from md2anki.md_util import (
    md_get_used_files,
    md_get_used_md2anki_tags,
    md_update_local_filepaths,
)

log = logging.getLogger(__name__)


@dataclass
class MdSection:
    """
    Represents a markdown section of anki deck notes.
    """

    heading: str = ""
    heading_id: str = ""
    content: str = ""

    def create_string(
        self,
        depth: int = 1,
        heading_prefix: Optional[str] = None,
        with_heading_id=True,
    ) -> str:
        output = (
            f"{'#' * depth} {heading_prefix if heading_prefix is not None else ''}{self.heading}"
            f"{f' ({self.heading_id})' if with_heading_id and len(self.heading_id) > 0 else ''}\n"
        )
        if self.content != "":
            output += f"\n{self.content}\n"
        return output


@dataclass
class AnkiNote:
    """
    Contains all information of an anki deck note.
    """

    question: str = ""
    """Question multi line string"""
    answer: str = ""
    """Answer multi line string"""
    tags: Set[str] = field(default_factory=lambda: set())
    """Tags"""
    guid: str = create_unique_id()
    """Unique id"""

    def get_used_local_files(self) -> Set[Path]:
        return set(
            [
                file
                for file in md_get_used_files(self.question).union(
                    md_get_used_files(self.answer)
                )
                if not isinstance(file, ParseResult)
            ]
        )

    def get_used_md2anki_tags(self) -> Set[str]:
        return (
            md_get_used_md2anki_tags(self.question)
            .union(md_get_used_md2anki_tags(self.answer))
            .union(self.tags)
        )

    def genanki_create_note(
        self,
        anki_card_model: genanki.Model,
        dir_dynamic_files: Path,
        custom_program: Dict[str, List[str]],
        custom_program_args: Dict[str, List[List[str]]],
        external_file_dirs: List[Path],
        evaluate_code: bool = False,
        evaluate_code_cache_dir: Optional[Path] = None,
        keep_temp_files: bool = False,
        merge_fields: bool = False,
    ) -> genanki.Note:
        """
        Args:
            @param anki_card_model: The card model
            @param dir_dynamic_files: Directory for dynamically created files
            @param custom_program: Custom program commands
            @param custom_program_args: Custom program command arguments
            @param evaluate_code: Evaluate code
            @param evaluate_code_cache_dir: Cache code evaluations in directory
            @param external_file_dirs: External file directories to insert files from
            @param keep_temp_files: Keep temporary files (debugging)
        Returns:
            An anki note for genanki
        """
        question_field_str = md_preprocessor_md2anki(
            self.question,
            dir_dynamic_files=dir_dynamic_files,
            custom_program=custom_program,
            custom_program_args=custom_program_args,
            evaluate_code=evaluate_code,
            evaluate_code_cache_dir=evaluate_code_cache_dir,
            external_file_dirs=external_file_dirs,
            keep_temp_files=keep_temp_files,
            anki_latex_math=True,
            render_to_html=True,
        )
        answer_field_str = md_preprocessor_md2anki(
            self.answer,
            dir_dynamic_files=dir_dynamic_files,
            custom_program=custom_program,
            custom_program_args=custom_program_args,
            evaluate_code=evaluate_code,
            evaluate_code_cache_dir=evaluate_code_cache_dir,
            external_file_dirs=external_file_dirs,
            keep_temp_files=keep_temp_files,
            anki_latex_math=True,
            render_to_html=True,
        )
        return genanki.Note(
            guid=self.guid,
            model=anki_card_model,
            fields=[f"{question_field_str}\n\n{answer_field_str}"]
            if merge_fields
            else [question_field_str, answer_field_str],
            tags=list(self.get_used_md2anki_tags().union(self.tags)),
        )

    def create_md_section(
        self, local_asset_dir_path: Optional[Path] = None
    ) -> MdSection:
        newline_count_question = len(self.question.splitlines())
        question_header: str = self.question.splitlines()[0].rstrip()
        question_body: str
        if newline_count_question <= 1:
            question_body = ""
        else:
            question_body = (
                f"\n{''.join(self.question.splitlines(keepends=True)[1:])}\n\n---"
            )
        if local_asset_dir_path is not None:
            question_header = md_update_local_filepaths(
                question_header, local_asset_dir_path
            )
            question_body = md_update_local_filepaths(
                question_body, local_asset_dir_path
            )
            answer = md_update_local_filepaths(self.answer, local_asset_dir_path)
        else:
            answer = self.answer

        return MdSection(
            question_header, self.guid, f"{question_body}\n\n{answer}".strip()
        )
