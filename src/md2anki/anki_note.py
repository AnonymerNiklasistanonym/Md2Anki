#!/usr/bin/env python3

# Internal packages
import html
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from re import Match
from typing import Set, Optional, Dict, List, Final
from urllib.parse import ParseResult

# Installed packages
import genanki
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound

# Local modules
from md2anki.create_id import create_unique_id
from md2anki.html_util import fix_inline_code_p_tags
from md2anki.md_util import (
    md_get_used_files,
    md_get_used_md2anki_tags,
    md_update_local_filepaths,
    md_update_code_parts,
    md_update_images,
    md_update_math_sections,
    md_update_generic_id_sections,
)
from md2anki.subprocess import (
    subprocess_evaluate_code,
    UnableToEvaluateCodeException,
)

log = logging.getLogger(__name__)

REGEX_MATH_BLOCK: Final = re.compile(r"\$\$([\S\s\n]+?)\$\$", flags=re.MULTILINE)


def multi_line_math_block_to_single_line(regex_group_match: Match):
    return "".join(regex_group_match.group().splitlines())


def update_md_image_to_html(
    file_path: str,
    file_description: str,
    width: Optional[str],
    height: Optional[str],
) -> str:
    style = ""
    if width is not None:
        style += f"width: {width};"
    if height is not None:
        style += f"height: {height};"
    return f'<img src="{file_path}" alt="{file_description}" style="{style}">'


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
        evaluate_code: bool = False,
        keep_temp_files: bool = False,
    ) -> genanki.Note:
        """
        Args:
            @param anki_card_model: The card model
            @param dir_dynamic_files: Directory for dynamically created files
            @param custom_program: Custom program commands
            @param custom_program_args: Custom program command arguments
            @param evaluate_code: Evaluate code
            @param keep_temp_files: Keep temporary files (debugging)
        Returns:
            An anki note for genanki
        """
        tmp_question = self.question
        tmp_answer = self.answer

        log.debug(f">> Convert note content (MD) to anki output (HTML)")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        # Find and store all code sections so that they won't be changed by other changes
        code_sections: Dict[int, str] = dict()
        placeholder_code_section: Final = (
            f"<div>md2anki_placeholder_start_code_{create_unique_id()}",
            f"md2anki_placeholder_end_code_{create_unique_id()}</div>",
        )

        def update_code_section_with_images_or_placeholder(
            code: str, code_block: bool, language: Optional[str]
        ):
            if language is not None and language.startswith("."):
                language = language[1:]
            # Detect executable code
            code_section = None
            image_section = None
            try:
                if evaluate_code and language is not None and language.startswith("="):
                    code_output, image_list = subprocess_evaluate_code(
                        language[1:],
                        code,
                        dir_dynamic_files=dir_dynamic_files,
                        custom_program=custom_program,
                        custom_program_args=custom_program_args,
                        keep_temp_files=keep_temp_files,
                    )
                    log.debug(
                        f"> Evaluate {code=}: {code_output=}, {image_list=}",
                    )
                    if len(image_list) > 0:
                        image_section = "".join(
                            map(lambda x: f"![]({x})\n", image_list)
                        )
                    else:
                        code_section = html.escape("".join(code_output))
                elif language is not None and language.startswith("="):
                    # If there is no code update values
                    language = language[1:]
                    log.warning(
                        f"[CARD={self.guid}] Code ({language!r}) for evaluation was found but evaluation is disabled!",
                    )
            except UnableToEvaluateCodeException as err:
                print(err, file=sys.stderr)
            if image_section is not None:
                return image_section
            elif code_section is None:
                if language is None:
                    language = "text"
                try:
                    language_lexer = get_lexer_by_name(language)
                except ClassNotFound as err:
                    log.warning(
                        f"[CARD={self.guid}] Default to text lexer ({language=}, {err=})",
                    )
                    language_lexer = get_lexer_by_name("text")
                html_formatter = get_formatter_by_name("html", noclasses=True)
                pygments_html_output = highlight(
                    code, language_lexer, html_formatter
                ).replace("background: #f8f8f8", "")
                if code_block:
                    code_section = pygments_html_output.replace(
                        'class="highlight"', 'class="highlight highlight_block"'
                    )
                else:
                    code_section = (
                        pygments_html_output.replace("\n", " ")
                        .replace("\r", "")
                        .replace(
                            'class="highlight"', 'class="highlight highlight_inline"'
                        )
                        .rstrip()
                    )

            code_section_index = len(code_sections)
            code_sections[code_section_index] = code_section
            return f"{placeholder_code_section[0]}{code_section_index}{placeholder_code_section[1]}"

        tmp_question = md_update_code_parts(
            tmp_question, update_code_section_with_images_or_placeholder
        )
        tmp_answer = md_update_code_parts(
            tmp_answer, update_code_section_with_images_or_placeholder
        )

        log.debug(
            f">> Updated code sections with images or placeholders({code_sections=})"
        )
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        tmp_question = re.sub(
            REGEX_MATH_BLOCK, multi_line_math_block_to_single_line, tmp_question
        )
        tmp_answer = re.sub(
            REGEX_MATH_BLOCK, multi_line_math_block_to_single_line, tmp_answer
        )

        # Collect all math sections to later overwrite them again
        math_sections: Dict[int, str] = dict()
        placeholder_math_section: Final = (
            f"md2anki_placeholder_start_math_{create_unique_id()}",
            f"md2anki_placeholder_end_math_{create_unique_id()}",
        )

        def update_math_section_with_placeholder(math_section: str, block: bool) -> str:
            math_section_index = len(math_sections)
            math_fence = ("\\[", "\\]") if block else (f"\\(", "\\)")
            math_sections[
                math_section_index
            ] = f"{math_fence[0]}{math_section}{math_fence[1]}"
            return f"{placeholder_math_section[0]}{math_section_index}{placeholder_math_section[1]}"

        tmp_question = md_update_math_sections(
            tmp_question, update_math_section_with_placeholder
        )
        tmp_answer = md_update_math_sections(
            tmp_answer, update_math_section_with_placeholder
        )

        log.debug(f">> Updated math sections with placeholders ({math_sections=})")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        # Reset local file paths to resources
        tmp_question = md_update_local_filepaths(tmp_question)
        tmp_answer = md_update_local_filepaths(tmp_answer)

        log.debug(f">> Reset local filepaths")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        # Extract files that this card requests and update paths
        tmp_question = md_update_images(tmp_question, update_md_image_to_html)
        tmp_answer = md_update_images(tmp_answer, update_md_image_to_html)

        log.debug(f">> Updated images to HTML")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        # Render many elements like tables by converting MD to HTML
        tmp_question = markdown.markdown(
            tmp_question,
            extensions=["markdown.extensions.extra"],
            tab_length=2,
        )
        tmp_answer = markdown.markdown(
            tmp_answer,
            extensions=["markdown.extensions.extra"],
            tab_length=2,
        )

        log.debug(">> Render markdown to HTML")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        # Insert all math sections again
        def update_math_section_placeholder_with_value(placeholder_index: str) -> str:
            return math_sections.pop(int(placeholder_index))

        tmp_question = md_update_generic_id_sections(
            tmp_question,
            placeholder_math_section,
            update_math_section_placeholder_with_value,
        )
        tmp_answer = md_update_generic_id_sections(
            tmp_answer,
            placeholder_math_section,
            update_math_section_placeholder_with_value,
        )

        log.debug(f">> Replaced math section placeholders")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        if len(math_sections) > 0:
            raise RuntimeError(
                f"Not all math sections were inserted back! ({math_sections=})"
            )

        # Insert all code sections again
        def update_code_section_placeholder_with_value(placeholder_index: str) -> str:
            return code_sections.pop(int(placeholder_index))

        tmp_question = md_update_generic_id_sections(
            tmp_question,
            placeholder_code_section,
            update_code_section_placeholder_with_value,
        )
        tmp_answer = md_update_generic_id_sections(
            tmp_answer,
            placeholder_code_section,
            update_code_section_placeholder_with_value,
        )

        log.debug(f">> Replaced code section placeholders")
        log.debug(f"   > {tmp_question=}")
        log.debug(f"   > {tmp_answer=}")

        if len(code_sections) > 0:
            raise RuntimeError(
                f"Not all code sections were inserted back! ({code_sections=})"
            )

        # Postfix for HTML p tags in front of inline code
        tmp_question = fix_inline_code_p_tags(tmp_question)
        tmp_answer = fix_inline_code_p_tags(tmp_answer)

        return genanki.Note(
            guid=self.guid,
            model=anki_card_model,
            fields=[tmp_question, tmp_answer],
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
