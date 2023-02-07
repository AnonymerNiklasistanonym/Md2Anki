import os
import re
from re import Match
from typing import Callable, Final, Optional, Set

from md2anki.print import warn_print

REGEX_MD_TAG: Final = re.compile(r"`{=:(.*?):=}`")
"""
Regex expression to parse a markdown tag notation: '`{=:tag list string:=}`'
The first group is the 'tag list string'.
"""

REGEX_MD_IMAGE_FILE: Final = re.compile(
    r"!\[(.*?)]\((.*?)\)(?:\{(?:\s*?width\s*?=(.+?)[\s,;]*?)?(?:\s*?height\s*?=(.+?)[\s,;]*?)?})?"
)
"""
Regex expression to parse a markdown image notation: '![alt text](source path){ width=100px, height=200px }'
The first group is the 'alt text' and the second one the 'source path' while optionally there is a third and fourth
group for the width and height if found.
"""

REGEX_CODE_BLOCK: Final = re.compile(
    r"```(?:\{(.+?)}|(.+?))\n([\S\s\n]+?)```", flags=re.MULTILINE
)
REGEX_INLINE_CODE: Final = re.compile(r"(?<!\S)`([^`]+?)`(?:\{(.+?)})?(?!\S)")

REGEX_MATH_SECTION: Final = re.compile(r"\${2}((?:[^$]|\n)+?)\${2}|\$(.+?)\$")

# TODO Add update local files method
# TODO Add update (inline) code blocks method


def md_get_used_files(md_content: str) -> Set[str]:
    """Get the used files of a Markdown text"""
    files: Final[Set[str]] = set()

    def add_used_files(regex_group_match: Match) -> str:
        """Detect and add all image paths to the created set"""
        filepath = regex_group_match.group(2)
        files.add(filepath)
        return ""

    re.sub(REGEX_MD_IMAGE_FILE, add_used_files, md_content)
    return files


def md_update_local_filepaths(
    md_content: str, new_directory: Optional[str] = None
) -> str:
    """Update all local filepaths to a custom directory"""

    if new_directory is None:
        return md_content

    local_filepath_dir: Final[str] = new_directory

    def update_local_filepath(regex_group_match: Match):
        filepath = regex_group_match.group(2)
        # Ignore non local filepaths
        if filepath.startswith("https://") or filepath.startswith("http://"):
            return regex_group_match[0]
        new_filepath = os.path.join(local_filepath_dir, os.path.basename(filepath))
        return regex_group_match[0].replace(filepath, new_filepath)

    return re.sub(REGEX_MD_IMAGE_FILE, update_local_filepath, md_content)


def md_update_images(
    md_content: str,
    image_replacer: Callable[[str, str, Optional[str], Optional[str]], str],
) -> str:
    def update_image(regex_group_match: Match) -> str:
        file_path = regex_group_match.group(2)
        file_description = regex_group_match.group(1)
        opt_image_width = regex_group_match.group(3)
        opt_image_height = regex_group_match.group(4)
        return image_replacer(
            file_path, file_description, opt_image_width, opt_image_height
        )

    return re.sub(REGEX_MD_IMAGE_FILE, update_image, md_content)


def md_update_code_parts(
    md_content: str,
    code_replacer: Callable[[Optional[str], str, bool], str],
) -> str:
    """Update code parts `replacer(language, code, code_block): updated code str`"""

    def code_block_replace(regex_group_match: Match):
        language_normal = regex_group_match.group(1)
        language_pandoc = regex_group_match.group(2)
        return code_replacer(
            language_normal if language_normal is not None else language_pandoc,
            regex_group_match.group(3),
            True,
        )

    def inline_code_replace(regex_group_match: Match):
        return code_replacer(
            regex_group_match.group(2), regex_group_match.group(1), False
        )

    md_content = re.sub(REGEX_CODE_BLOCK, code_block_replace, md_content)
    md_content = re.sub(REGEX_INLINE_CODE, inline_code_replace, md_content)

    return md_content


def md_get_used_md2anki_tags(md_content: str) -> Set[str]:
    """Get the used (custom) md2anki tags of a Markdown text"""
    tags: Final[Set[str]] = set()

    def add_used_tags(regex_group_match: Match) -> str:
        """Detect and add all local found tags to the created set"""
        tag_strings = regex_group_match.group(1).split(",")
        for tag_string in tag_strings:
            tag = tag_string.strip()
            if " " in tag:
                old_tag = tag
                tag = tag.replace(" ", "_")
                warn_print(f"A tag with spaces {old_tag!r} was rewritten to {tag!r}")
            if len(tag) > 0:
                tags.add(tag)
        return ""

    re.sub(REGEX_MD_TAG, add_used_tags, md_content)
    return tags


def md_update_math_sections(md_content: str, replacer: Callable[[str, bool], str]):
    """Update math sections `replacer(math_section, block): updated str`"""

    def math_section_replace(regex_group_match: Match):
        if regex_group_match.group(1) is not None:
            return replacer(regex_group_match.group(1), True)
        else:
            return replacer(regex_group_match.group(2), False)

    md_content = re.sub(REGEX_MATH_SECTION, math_section_replace, md_content)
    return md_content
