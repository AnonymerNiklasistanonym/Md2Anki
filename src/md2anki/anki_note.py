import html
import re
import sys
from dataclasses import dataclass, field
from typing import Set, Optional, Dict

import genanki
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound

from md2anki.html_util import fix_inline_code_p_tags
from md2anki.print import debug_print, warn_print
from md2anki.subprocess import (
    evaluate_code,
    UnableToEvaluateCodeException,
    SubprocessPrograms,
)
from md2anki.create_id import create_unique_id
from md2anki.md_util import (
    md_get_used_files,
    md_get_used_md2anki_tags,
    md_update_local_filepaths,
    md_update_code_parts,
    md_update_images,
    md_update_math_sections,
)


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

    def get_used_local_files(self) -> Set[str]:
        return set(
            [
                file
                for file in md_get_used_files(self.question).union(
                    md_get_used_files(self.answer)
                )
                if not file.startswith("https://") and not file.startswith("http://")
            ]
        )

    def get_used_md2anki_tags(self) -> Set[str]:
        return md_get_used_md2anki_tags(self.question).union(
            md_get_used_md2anki_tags(self.answer)
        )

    def genanki_create_note(
        self,
        anki_card_model: genanki.Model,
        dir_dynamic_files: str,
        debug=False,
    ) -> genanki.Note:
        """
        Args:
            anki_card_model: The card model
            dir_dynamic_files: Directory for dynamically created files
            debug: Output debug information
        Returns:
            An anki note for genanki
        """
        tmp_question = self.question
        tmp_answer = self.answer

        if debug:
            print(f"{tmp_question=}")
            print(f"{tmp_answer=}")

        # Fix source code blocks
        def md_code_replacer(language: Optional[str], code: str, code_block: bool):
            if language is not None and language.startswith("."):
                language = language[1:]
            # Detect executable code
            try:
                if language is not None and language.startswith("="):
                    code_output = evaluate_code(
                        language[1:],
                        code,
                        dir_dynamic_files=dir_dynamic_files,
                        debug=debug,
                    )
                    debug_print(f"> Evaluate {code=}: {code_output=}", debug=debug)
                    return html.escape(code_output)
            except UnableToEvaluateCodeException as err:
                print(err, file=sys.stderr)
            if language == SubprocessPrograms.JUPYTER_NOTEBOOK_MATPLOTLIB.name:
                language = SubprocessPrograms.PYTHON.name
            if language is None:
                language = "text"
            try:
                language_lexer = get_lexer_by_name(language)
            except ClassNotFound as err:
                warn_print(f"Default to text lexer ({language=}, {err=})")
                language_lexer = get_lexer_by_name("text")
            html_formatter = get_formatter_by_name("html", noclasses=True)
            pygments_html_output = highlight(
                code, language_lexer, html_formatter
            ).replace("background: #f8f8f8", "")
            if code_block:
                return pygments_html_output.replace(
                    'class="highlight"', 'class="highlight highlight_block"'
                )
            else:
                return (
                    pygments_html_output.replace("\n", " ")
                    .replace("\r", "")
                    .replace('class="highlight"', 'class="highlight highlight_inline"')
                    .rstrip()
                )

        tmp_question = md_update_code_parts(tmp_question, md_code_replacer)
        tmp_answer = md_update_code_parts(tmp_answer, md_code_replacer)

        if debug:
            print(f">> tmp_question_code_fix: {tmp_question!r}")
            print(f">> tmp_answer_code_fix:   {tmp_answer!r}")

        # Update local file paths to root directory
        tmp_question = md_update_local_filepaths(tmp_question)
        tmp_answer = md_update_local_filepaths(tmp_answer)

        # Fix multi line TeX commands (otherwise broken on Website)
        regex_math_block = re.compile(r"\$\$([\S\s\n]+?)\$\$", flags=re.MULTILINE)

        def lambda_math_block_to_single_line(regex_group_match):
            return "".join(regex_group_match.group().splitlines())

        tmp_question = re.sub(
            regex_math_block, lambda_math_block_to_single_line, tmp_question
        )
        tmp_answer = re.sub(
            regex_math_block, lambda_math_block_to_single_line, tmp_answer
        )

        # Extract files that this card requests and update paths
        def update_image(
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

        tmp_question = md_update_images(tmp_question, update_image)
        tmp_answer = md_update_images(tmp_answer, update_image)

        if debug:
            print(f">> tmp_question_image_fix: {tmp_question!r}")
            print(f">> tmp_answer_image_fix:   {tmp_answer!r}")

        # Collect all math sections to later overwrite them again
        math_sections: Dict[int, str] = dict()
        placeholder_content = "placeholder"

        def update_math_section_placeholder(math_section: str, block: bool) -> str:
            math_section_index = len(math_sections)
            math_sections[math_section_index] = math_section
            if block:
                return f"$${placeholder_content}{math_section_index}$$"
            else:
                return f"${placeholder_content}{math_section_index}$"

        tmp_question = md_update_math_sections(
            tmp_question, update_math_section_placeholder
        )
        tmp_answer = md_update_math_sections(
            tmp_answer, update_math_section_placeholder
        )

        # Render tables
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

        if debug:
            print(f">> tmp_question_html_conversion: {tmp_question!r}")
            print(f">> tmp_answer_html_conversion:   {tmp_answer!r}")

        # Insert all math sections again
        def update_math_section_stored(math_section: str, block: bool) -> str:
            math_section_str = math_sections[
                int(math_section[len(placeholder_content) :])
            ]
            if block:
                return f"\\[{math_section_str}\\]"
            else:
                return f"\\({math_section_str}\\)"

        tmp_question = md_update_math_sections(tmp_question, update_math_section_stored)
        tmp_answer = md_update_math_sections(tmp_answer, update_math_section_stored)

        if debug:
            print(f">> tmp_question_math_fix: {tmp_question!r}")
            print(f">> tmp_answer_math_fix:   {tmp_answer!r}")

        # Explicitly render line breaks
        tmp_question = fix_inline_code_p_tags(tmp_question)
        tmp_answer = fix_inline_code_p_tags(tmp_answer)

        if debug:
            print(f">> tmp_question_newline_fix: {tmp_question!r}")
            print(f">> tmp_answer_newline_fix:   {tmp_answer!r}")

        return genanki.Note(
            guid=self.guid,
            model=anki_card_model,
            fields=[tmp_question, tmp_answer],
            tags=list(self.get_used_md2anki_tags().union(self.tags)),
        )

    def create_md_section(
        self, local_asset_dir_path: Optional[str] = None
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
        question_header = md_update_local_filepaths(
            question_header, local_asset_dir_path
        )
        question_body = md_update_local_filepaths(question_body, local_asset_dir_path)
        answer = md_update_local_filepaths(self.answer, local_asset_dir_path)
        return MdSection(
            question_header, self.guid, f"{question_body}\n\n{answer}".strip()
        )
