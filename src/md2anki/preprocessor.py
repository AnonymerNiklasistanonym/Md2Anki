#!/usr/bin/env python3

# Internal packages
import logging
import re
import textwrap
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
from md2anki.info.general import (
    MD2ANKI_MD_PP_EVALUATE_CODE_LANGUAGE_PREFIX,
    MD2ANKI_EVALUATE_CODE_ENV_NAME_ANKI_HTML_BOOL,
    MD2ANKI_EVALUATE_CODE_ENV_NAME_PANDOC_PDF_BOOL,
    MD2ANKI_MD_PP_COMMENT_INSERT_FILE_PREFIX,
    MD2ANKI_NAME,
    MD2ANKI_MD_PP_MD2ANKI_TAG_PREFIX,
    MD2ANKI_MD_PP_MD2ANKI_TAG_SUFFIX,
)
from md2anki.md_util import (
    md_update_local_filepaths,
    md_update_code_parts,
    md_update_images,
    md_update_math_sections,
    md_update_generic_id_sections,
)
from md2anki.evaluate_code import (
    evaluate_code_in_subprocess,
    UnableToEvaluateCodeException,
)

# Logger
log = logging.getLogger(__name__)

# Constants
REGEX_MATH_BLOCK: Final = re.compile(r"\$\$([\S\s\n]+?)\$\$", flags=re.MULTILINE)
REGEX_MD_COMMENT_INSERT_FILE: Final = re.compile(
    r"(?:^[ \t]*[\n\r]|\A)(?P<indent>[ \t]*)\[//]:\s+#\s+\("
    rf"{MD2ANKI_MD_PP_COMMENT_INSERT_FILE_PREFIX}"
    r"(?P<file>.*?)\)(?=(?:[ \t]*[\n\r]){2,}|[ \t]*\Z)",
    flags=re.MULTILINE,
)


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
    external_file_dirs: List[Path],
    evaluate_code: bool = False,
    evaluate_code_cache_dir: Optional[Path] = None,
    keep_temp_files: bool = False,
    anki_latex_math: bool = False,
    render_to_html: bool = False,
) -> str:
    """
    Preprocess Markdown content with md2anki macros.

    Args:
        @param md_content: Markdown content with md2anki/pandoc/... macros
        @param dir_dynamic_files: Directory for dynamically created files
        @param custom_program: Custom program commands
        @param custom_program_args: Custom program command arguments
        @param external_file_dirs: Other directories that contain file references.
        @param evaluate_code: Evaluate code
        @param evaluate_code_cache_dir: Cache code evaluations in directory
        @param keep_temp_files: Keep temporary files (debugging)
        @param anki_latex_math: Additionally render certain macros with HTML in mind
        @param render_to_html: Additionally render certain macros with HTML in mind
    Returns:
        The update markdown content.
    """

    log.debug(f">> Update md2anki macro Markdown to native Markdown")
    log.debug(f"   > {md_content=}")

    # 1. Replace Markdown comments with external file content

    def insert_external_file(regex_group_match: Match):
        indent = regex_group_match.group(1)
        filepath = Path(regex_group_match.group(2))
        found_file = False
        if filepath.is_file():
            found_file = True
        else:
            for external_file_dir in external_file_dirs:
                if external_file_dir.joinpath(filepath).is_file():
                    found_file = True
                    filepath = external_file_dir.joinpath(filepath)
                    break
        if not found_file:
            raise RuntimeError(
                f"File to be inserted was not found ({filepath=}, {external_file_dirs=})"
            )
        with open(filepath, "r") as f:
            return f"\n\n{textwrap.indent(f.read(), indent)}\n"

    md_content = re.sub(REGEX_MD_COMMENT_INSERT_FILE, insert_external_file, md_content)

    log.debug(f">> Updated insert file comments")
    log.debug(f"   > {md_content=}")

    # 2. Find, evaluate and store all code sections so that they won't be changed by other changes
    code_sections: Dict[int, str] = dict()
    placeholder_code_section: Final = (
        f"{MD2ANKI_NAME}_placeholder_start_code_{create_unique_id()}",
        f"{MD2ANKI_NAME}_placeholder_end_code_{create_unique_id()}",
    )

    def update_code_section_with_images_or_placeholder(
        code: str,
        code_block: bool,
        language: Optional[str],
        code_block_indent: Optional[str],
    ) -> str:
        # Remove md2anki tags
        if (
            code_block is False
            and language is None
            and code.startswith(MD2ANKI_MD_PP_MD2ANKI_TAG_PREFIX)
            and code.endswith(MD2ANKI_MD_PP_MD2ANKI_TAG_SUFFIX)
        ):
            return ""
        # Fix pandoc inline notation for language formatting
        if language is not None and language.startswith("."):
            language = language[1:]
        indent = code_block_indent if code_block_indent is not None else ""
        # Fix code block condent if indented
        indent_free_code = code
        if code_block and code_block_indent is not None and len(code_block_indent) > 0:
            indent_free_code = textwrap.dedent(code)
        prefix = "\n" if code_block else ""
        # Detect executable code
        try:
            if (
                evaluate_code
                and language is not None
                and language.startswith(MD2ANKI_MD_PP_EVALUATE_CODE_LANGUAGE_PREFIX)
            ):
                code_output, image_list = evaluate_code_in_subprocess(
                    language[1:],
                    indent_free_code,
                    dir_dynamic_files=dir_dynamic_files,
                    custom_program=custom_program,
                    custom_program_args=custom_program_args,
                    keep_temp_files=keep_temp_files,
                    additional_env={
                        MD2ANKI_EVALUATE_CODE_ENV_NAME_ANKI_HTML_BOOL: str(
                            render_to_html
                        ),
                        MD2ANKI_EVALUATE_CODE_ENV_NAME_PANDOC_PDF_BOOL: str(
                            not render_to_html
                        ),
                    },
                    cache_dir=evaluate_code_cache_dir,
                )
                log.debug(
                    f"> Evaluate {indent_free_code=}: {code_output=}, {image_list=}",
                )
                if len(image_list) > 0:
                    return prefix + "\n".join(
                        map(lambda x: f"{indent}![]({x})\n", image_list)
                    )
                else:
                    return prefix + textwrap.indent("".join(code_output), indent)
            elif language is not None and language.startswith("="):
                # If there is no code update values
                language = language[1:]
                log.warning(
                    f"Code ({language!r}) for evaluation was found but evaluation is disabled!",
                )
        except UnableToEvaluateCodeException as err:
            log.error(err)

        if language is None:
            language = "text"
        if render_to_html is False:
            if code_block:
                return prefix + f"{indent}```{language}\n{code}```\n"
            else:
                return f"`{code}`" + (
                    ("{." + language + "}") if language is not None else ""
                )
        try:
            language_lexer = get_lexer_by_name(language)
        except ClassNotFound as err:
            log.warning(
                f"Default to text lexer ({language=}, {err=}, check supported lexers by running with --lexers)",
            )
            language_lexer = get_lexer_by_name("text")
        html_formatter = get_formatter_by_name("html", noclasses=True)
        pygments_html_output = highlight(code, language_lexer, html_formatter).replace(
            "background: #f8f8f8", ""
        )
        if code_block:
            code_section = textwrap.indent(
                pygments_html_output.replace(
                    'class="highlight"', 'class="highlight highlight_block"'
                ),
                indent,
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
        return f"{prefix}{placeholder_code_section[0]}{code_section_index}{placeholder_code_section[1]}"

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
        f"{MD2ANKI_NAME}_placeholder_start_math_{create_unique_id()}",
        f"{MD2ANKI_NAME}_placeholder_end_math_{create_unique_id()}",
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
