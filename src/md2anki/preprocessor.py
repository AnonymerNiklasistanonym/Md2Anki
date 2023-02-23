#!/usr/bin/env python3

# Internal packages
import logging
import re
import sys
from pathlib import Path
from re import Match
from typing import Optional, Dict, List, Final

# Installed packages
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound

# Local modules
from md2anki.create_id import create_unique_id
from md2anki.html_util import fix_inline_code_p_tags
from md2anki.md_util import (
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


def md_preprocessor_md2anki(
    md_content: str,
    dir_dynamic_files: Path,
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    evaluate_code: bool = False,
    keep_temp_files: bool = False,
    anki_latex_math: bool = False,
    render_to_html: bool = False,
) -> str:
    """
    Args:
        @param md_content: Markdown content with md2anki/pandoc/... macros
        @param dir_dynamic_files: Directory for dynamically created files
        @param custom_program: Custom program commands
        @param custom_program_args: Custom program command arguments
        @param evaluate_code: Evaluate code
        @param keep_temp_files: Keep temporary files (debugging)
        @param anki_latex_math: Additionally render certain macros with HTML in mind
        @param render_to_html: Additionally render certain macros with HTML in mind
    Returns:
        The update markdown content.
    """

    log.debug(f">> Update md2anki macro Markdown to native Markdown")
    log.debug(f"   > {md_content=}")

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
        try:
            if evaluate_code and language is not None and language.startswith("="):
                code_output, image_list = subprocess_evaluate_code(
                    language[1:],
                    code,
                    dir_dynamic_files=dir_dynamic_files,
                    custom_program=custom_program,
                    custom_program_args=custom_program_args,
                    keep_temp_files=keep_temp_files,
                    customEnv={
                        "MD2ANKI_ANKI_HTML": str(render_to_html),
                        "MD2ANKI_PANDOC_PDF": str(not render_to_html),
                    },
                )
                log.debug(
                    f"> Evaluate {code=}: {code_output=}, {image_list=}",
                )
                if len(image_list) > 0:
                    return "".join(map(lambda x: f"![]({x})\n", image_list))
                else:
                    return "".join(code_output)
            elif language is not None and language.startswith("="):
                # If there is no code update values
                language = language[1:]
                log.warning(
                    f"Code ({language!r}) for evaluation was found but evaluation is disabled!",
                )
        except UnableToEvaluateCodeException as err:
            print(err, file=sys.stderr)
        if language is None:
            language = "text"
        if render_to_html is False:
            if code_block:
                return f"```{language}\n{code}```\n"
            else:
                return f"`{code}`" + (
                    ("{." + language + "}") if language is not None else ""
                )
        try:
            language_lexer = get_lexer_by_name(language)
        except ClassNotFound as err:
            log.warning(
                f"Default to text lexer ({language=}, {err=})",
            )
            language_lexer = get_lexer_by_name("text")
        html_formatter = get_formatter_by_name("html", noclasses=True)
        pygments_html_output = highlight(code, language_lexer, html_formatter).replace(
            "background: #f8f8f8", ""
        )
        if code_block:
            code_section = pygments_html_output.replace(
                'class="highlight"', 'class="highlight highlight_block"'
            )
        else:
            code_section = (
                pygments_html_output.replace("\n", " ")
                .replace("\r", "")
                .replace('class="highlight"', 'class="highlight highlight_inline"')
                .rstrip()
            )

        code_section_index = len(code_sections)
        code_sections[code_section_index] = code_section
        return f"{placeholder_code_section[0]}{code_section_index}{placeholder_code_section[1]}"

    md_content = md_update_code_parts(
        md_content, update_code_section_with_images_or_placeholder
    )

    log.debug(f">> Updated code sections with images or placeholders({code_sections=})")
    log.debug(f"   > {md_content=}")

    md_content = re.sub(
        REGEX_MATH_BLOCK, multi_line_math_block_to_single_line, md_content
    )

    # Collect all math sections to later overwrite them again
    math_sections: Dict[int, str] = dict()
    placeholder_math_section: Final = (
        f"md2anki_placeholder_start_math_{create_unique_id()}",
        f"md2anki_placeholder_end_math_{create_unique_id()}",
    )

    if anki_latex_math is True:

        def update_math_section_with_placeholder(math_section: str, block: bool) -> str:
            math_section_index = len(math_sections)
            math_fence = ("\\[", "\\]") if block else (f"\\(", "\\)")
            math_sections[
                math_section_index
            ] = f"{math_fence[0]}{math_section}{math_fence[1]}"
            return f"{placeholder_math_section[0]}{math_section_index}{placeholder_math_section[1]}"

        md_content = md_update_math_sections(
            md_content, update_math_section_with_placeholder
        )

        log.debug(f">> Updated math sections with placeholders ({math_sections=})")
        log.debug(f"   > {md_content=}")

    # Reset local file paths to resources
    md_content = md_update_local_filepaths(md_content)

    log.debug(f">> Reset local filepaths")
    log.debug(f"   > {md_content=}")

    if render_to_html is True:
        # Extract files that this card requests and update paths
        md_content = md_update_images(md_content, update_md_image_to_html)

        log.debug(f">> Updated images to HTML")
        log.debug(f"   > {md_content=}")

        # Render many elements like tables by converting MD to HTML
        md_content = markdown.markdown(
            md_content,
            extensions=["markdown.extensions.extra"],
            tab_length=2,
        )

        log.debug(">> Render markdown to HTML")
        log.debug(f"   > {md_content=}")

    if anki_latex_math is True:
        # Insert all math sections again
        def update_math_section_placeholder_with_value(placeholder_index: str) -> str:
            return math_sections.pop(int(placeholder_index))

        md_content = md_update_generic_id_sections(
            md_content,
            placeholder_math_section,
            update_math_section_placeholder_with_value,
        )

        log.debug(f">> Replaced math section placeholders")
        log.debug(f"   > {md_content=}")

        if len(math_sections) > 0:
            raise RuntimeError(
                f"Not all math sections were inserted back! ({math_sections=})"
            )

    # Insert all code sections again
    def update_code_section_placeholder_with_value(placeholder_index: str) -> str:
        return code_sections.pop(int(placeholder_index))

    md_content = md_update_generic_id_sections(
        md_content,
        placeholder_code_section,
        update_code_section_placeholder_with_value,
    )

    log.debug(f">> Replaced code section placeholders")
    log.debug(f"   > {md_content=}")

    if len(code_sections) > 0:
        raise RuntimeError(
            f"Not all code sections were inserted back! ({code_sections=})"
        )

    if render_to_html is True:
        # Postfix for HTML p tags in front of inline code
        md_content = fix_inline_code_p_tags(md_content)

    return md_content
