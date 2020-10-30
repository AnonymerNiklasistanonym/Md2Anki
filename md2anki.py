#!/usr/bin/env python3

# Internal packages
import os.path
import random
import re
import sys
import urllib.request
import html
import markdown
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, TextIO, Set
from uuid import uuid4

# Installed packages
import genanki
import pymdownx.arithmatex as arithmatex

VERSION_MAJOR: int = 2
VERSION_MINOR: int = 0
VERSION_PATCH: int = 0

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CSS_GENERAL_FILE_PATH = os.path.join(CURRENT_DIR, "stylesheet.css")
HIGHLIGHTJS_SCRIPT_FILE_PATH = os.path.join(CURRENT_DIR, "highlightJs_renderer.js")
KATEXT_FILE_SCRIPT_PATH = os.path.join(CURRENT_DIR, "kaTex_renderer.js")

HLJS_VERSION = "10.3.1"
HLJS_CSS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/styles/default.min.css"
HLJS_CSS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.css"
HLJS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/highlight.min.js"
HLJS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.js"

KATEX_VERSION = "0.12.0"
KATEX_CSS_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css"
KATEX_CSS_FILE_NAME = f"katex_{KATEX_VERSION}.min.css"
KATEX_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js"
KATEX_FILE_NAME = f"katex_{KATEX_VERSION}.min.js"
KATEX_AUTO_RENDERER_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js"
KATEX_AUTO_RENDERER_FILE_NAME = f"katex_auto_render_{KATEX_VERSION}.min.js"


def cli_help():
    print(
        "$ python3 md2anki.py MD_FILE [OPTIONS]\n\n"
        + "Create an anki deck file (.apkg) from a markdown document.\n"
        + "If no custom output path is given the file name of the document\n"
        + "(+ .apkg) is used.\n\n"
        + "Options:\n"
        + "\t-d\t\t\tActivate debugging output\n"
        + "\t-o-anki FILE_PATH\tCustom anki deck output file path\n"
        + "\t-o-md FILE_PATH\t\tCustom markdown output file path\n"
        + "\t-o-backup-dir DIR_PATH\tBackup the input and its local assets\n"
        + "\t-file-dir DIR_PATH\tAdditional file directory\n\n"
        + "Also supported are:\n"
        + "\t--help\n"
        + "\t--version"
    )


def cli_version():
    print(f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}")


def create_unique_id() -> str:
    return str(uuid4())


def create_unique_id_int(length: int = 32) -> int:
    return random.getrandbits(length)


@dataclass
class AnkiDeckNote:
    """
    Contains all information of an anki deck note
    """

    question: str = ""
    """Question multi line string"""
    answer: str = ""
    """Answer multi line string"""
    category: Optional[str] = None
    """Optional category for note"""
    guid: str = create_unique_id()
    """Unique id of anki deck note"""

    regex_image_file = re.compile(
        r"!\[(.*?)\]\((.*?)\)(?:\{(?:\s*?width\s*?=(.+?)\s*?)?(?:\s*?height\s*?=(.+?)\s*?)?\})?"
    )
    """
    Regex expression to parse a markdown image notation: '[alt text](source path){ width=100px, height=200px)'
    The first group is the 'alt text' and the second one the 'source path' while optionally there is a third and fourth
    group for the width and height if found.
    """

    def get_used_files(self) -> Set[str]:
        """Get the used local files of the note"""
        regex_image_file = re.compile(r"!\[.*?\]\((.*?)\)")
        files: Set[str] = set()

        def add_image_path(regex_group_match):
            """Detect and add all local image path to the created set"""
            filepath = regex_group_match.group(1)
            # Only add file path if it is not an URL
            if not filepath.startswith("https://") and not filepath.startswith(
                "http://"
            ):
                files.add(filepath)
            # Only return string for correct type checking
            return ""

        re.sub(regex_image_file, add_image_path, self.question)
        re.sub(regex_image_file, add_image_path, self.answer)
        return files

    def genanki_create_note(
        self,
        anki_card_model: genanki.Model,
        additional_file_dirs_to_escape: Optional[List[str]] = None,
        escape_unicode=True,
        markdown_to_anki_html=True,
        debug=False,
    ) -> genanki.Note:
        """
        Args:
            anki_card_model: The card model
            additional_file_dirs_to_escape: File directories that contain (image) resources and should be escaped
            escape_unicode: Escape unicode symbols
            markdown_to_anki_html: Create html <br> tags for newlines
            debug: Output debug information
        Returns:
            An anki note for genanki
        """
        if additional_file_dirs_to_escape is None:
            additional_file_dirs_to_escape = []
        temp_question = self.question
        temp_answer = self.answer

        if debug:
            print(f">> Input question text: '{temp_question}'")
            print(f">> Input answer text: '{temp_answer}'")

        for file_dir_to_escape in additional_file_dirs_to_escape:
            temp_question = temp_question.replace(
                f'"{file_dir_to_escape}{os.path.sep}', '"'
            )
            temp_answer = temp_answer.replace(
                f'"{file_dir_to_escape}{os.path.sep}', '"'
            )

        def code_block_replace(regex_group_match):
            language = regex_group_match.group(1)
            code = html.escape(regex_group_match.group(2))
            return f'<pre><code class="{language}">{code}</code></pre>'

        def inline_code_replace(regex_group_match):
            code = html.escape(regex_group_match.group(1))
            return f' <pre style="display: inline"><code class="nohighlight">{code}</code></pre> '

        # Fix source code blocks
        regex_code_block = re.compile(r"```(.*?)\n([\S\s\n]+?)```", flags=re.MULTILINE)
        regex_inline_code = re.compile(r"(?:^|\s)`(.*?)`(?:$|\s)")

        temp_question = re.sub(regex_code_block, code_block_replace, temp_question)
        temp_answer = re.sub(regex_code_block, code_block_replace, temp_answer)
        temp_question = re.sub(regex_inline_code, inline_code_replace, temp_question)
        temp_answer = re.sub(regex_inline_code, inline_code_replace, temp_answer)

        # Fix multi line TeX commands (otherwise broken on Website)
        regex_math_block = re.compile(r"\$\$([\S\s\n]+?)\$\$", flags=re.MULTILINE)

        def lambda_math_block_to_single_line(regex_group_match):
            return "".join(regex_group_match.group().splitlines())

        temp_question = re.sub(
            regex_math_block, lambda_math_block_to_single_line, temp_question
        )
        temp_answer = re.sub(
            regex_math_block, lambda_math_block_to_single_line, temp_answer
        )

        # Extract files that this card requests and update paths
        def extract_image_info_and_update_image_path(regex_group_match) -> str:
            filepath = regex_group_match.group(2)
            # Check if file path is a URL
            if not filepath.startswith("https://") and not filepath.startswith(
                "http://"
            ):
                filename = os.path.basename(filepath)
            else:
                filename = filepath
            file_description = regex_group_match.group(1)
            style = ""
            if regex_group_match.group(3) is not None:
                style += f"width: {regex_group_match.group(3)};"
            if regex_group_match.group(4) is not None:
                style += f"height: {regex_group_match.group(4)};"
            return f'<img src="{filename}" alt="{file_description}" style="{style}">'

        temp_question = re.sub(
            self.regex_image_file,
            extract_image_info_and_update_image_path,
            temp_question,
        )
        temp_answer = re.sub(
            self.regex_image_file, extract_image_info_and_update_image_path, temp_answer
        )

        if debug:
            print(
                f">> Card text for question before markdown module parsing: '{temp_question}'"
            )
            print(
                f">> Card text for question before markdown module parsing: '{temp_answer}'"
            )

        # # Dumb fix because arithmatex and markdown are shit
        regex_dumb = r"(\${2}(?:[^\$]|\n)+?\${2}|\${1}.+?\${1})"

        def dumb_backslash_fix(regex_group_match):
            return regex_group_match.group(0).replace("\\", "\\\\")

        temp_question = re.sub(regex_dumb, dumb_backslash_fix, temp_question)
        temp_answer = re.sub(regex_dumb, dumb_backslash_fix, temp_answer)

        # Render tables
        temp_question = markdown.markdown(
            temp_question,
            extensions=[
                "markdown.extensions.tables",
                arithmatex.ArithmatexExtension(
                    generic=True,
                    inline_syntax="dollar",
                    block_syntax="dollar",
                    preview=False,
                ),
            ],
        )
        temp_answer = markdown.markdown(
            temp_answer,
            extensions=[
                "markdown.extensions.tables",
                arithmatex.ArithmatexExtension(
                    generic=True,
                    inline_syntax="dollar",
                    block_syntax="dollar",
                    preview=False,
                ),
            ],
        )

        if debug:
            print(
                f">> Card text for question after markdown module parsing: '{temp_question}'"
            )
            print(
                f">> Card text for question after markdown module parsing: '{temp_answer}'"
            )

        # Explicitly render line breaks
        if markdown_to_anki_html:
            temp_question = temp_question.replace(r"(?!>)\n", "<br>").replace("\r", "")
            temp_answer = temp_answer.replace(r"(?!>)\n", "<br>").replace("\r", "")

        # Fix inline math sections
        regex_math_part = re.compile(r"(\${1,2})((?:.|\r?\n)+?)\1", flags=re.MULTILINE)

        def update_math_section(regex_group_match) -> str:
            math_section_tag = regex_group_match.group(1)
            math_section_content = regex_group_match.group(2)
            if math_section_tag == "$":
                return f'<span class="math math-inline">${math_section_content}$</span>'
            else:
                return (
                    f'<span class="math math-display">$${math_section_content}$$</span>'
                )

        temp_question = re.sub(regex_math_part, update_math_section, temp_question)
        temp_answer = re.sub(regex_math_part, update_math_section, temp_answer)

        if debug:
            print(f">> Final card text for question: '{temp_question}'")
            print(f">> Final card text for answer: '{temp_answer}'")

        return genanki.Note(
            guid=self.guid, model=anki_card_model, fields=[temp_question, temp_answer]
        )

    def update_local_file_paths(
        self, text_input: str, local_asset_dir_path: Optional[str] = None
    ) -> str:

        if local_asset_dir_path is None:
            return text_input

        # Extract files that this card requests and update paths
        def extract_image_info_and_update_image_path(regex_group_match) -> str:
            filepath = regex_group_match.group(2)
            # Check if file path is a URL
            if not filepath.startswith("https://") and not filepath.startswith(
                "http://"
            ):
                new_file_path = os.path.join(
                    local_asset_dir_path, os.path.basename(filepath)
                )
                return regex_group_match.group(0).replace(
                    f"]({filepath})", f"]({new_file_path})"
                )
            else:
                return regex_group_match.group(0)

        return re.sub(
            self.regex_image_file, extract_image_info_and_update_image_path, text_input
        )

    def md_create_string(
        self, heading_level=2, local_asset_dir_path: Optional[str] = None
    ) -> str:
        newline_count_question = len(self.question.splitlines())
        question_header: str = self.question.splitlines()[0].rstrip()
        question_body: str
        if newline_count_question <= 1:
            question_body = ""
        else:
            question_body = (
                f"\n{''.join(self.question.splitlines(keepends=True)[1:])}\n\n---"
            )
        question_header = self.update_local_file_paths(
            question_header, local_asset_dir_path=local_asset_dir_path
        )
        question_body = self.update_local_file_paths(
            question_body, local_asset_dir_path=local_asset_dir_path
        )
        answer = self.update_local_file_paths(
            self.answer, local_asset_dir_path=local_asset_dir_path
        )
        return f"{'#' * heading_level} {question_header} ({self.guid}){question_body}\n\n{answer}"


@dataclass
class AnkiModel:
    """
    Contains all information of an anki model (for anki notes of an anki deck)
    """

    name: str = ""
    """Model name"""
    description: str = ""
    """Model description"""
    css: str = ""
    """Style information (CSS code) for each anki note"""
    js: str = ""
    """Script information (JS code) for each anki note"""
    guid: int = create_unique_id_int()
    """Unique id of anki model"""
    template_card_question: str = "{{Question}}"
    """Card question text"""
    template_card_separator: str = '{{FrontSide}}<hr id="answer">'
    """Card separator text"""
    template_card_answer: str = "{{Answer}}"
    """Card answer text"""

    def genanki_create_model(self) -> genanki.Model:
        return genanki.Model(
            self.guid,
            self.description,
            fields=[{"name": "Question"}, {"name": "Answer"}],
            css=self.css,
            templates=[
                {
                    "name": self.name,
                    "qfmt": self.js + "\n" + self.template_card_question,
                    "afmt": self.template_card_separator + self.template_card_answer,
                }
            ],
        )


@dataclass
class AnkiDeck:
    """
    Contains all information of an anki deck
    """

    name: str = "No name"
    """Name of the deck"""
    model: AnkiModel = AnkiModel()
    """Model of cards of anki deck"""
    guid: int = create_unique_id_int()
    """Unique id of anki deck"""
    notes: List[AnkiDeckNote] = field(default_factory=lambda: list())
    """List of anki notes"""
    additional_file_dirs: List[str] = field(default_factory=lambda: list())
    """List of additional file dirs that should be searched for missing files used in notes"""

    def genanki_create_deck(
        self,
        anki_card_model: genanki.Model,
        additional_file_dirs_to_escape: Optional[List[str]] = None,
        debug=False,
    ) -> genanki.Deck:
        temp_anki_deck = genanki.Deck(self.guid, self.name)
        for note in self.notes:
            temp_anki_deck.add_note(
                note.genanki_create_note(
                    anki_card_model, additional_file_dirs_to_escape, debug=debug
                )
            )
        return temp_anki_deck

    def get_local_files_from_notes(self, debug=False) -> List[str]:
        files: Set[str] = set()
        for note in self.notes:
            files.update(note.get_used_files())
        file_list: List[str] = list()
        for file in files:
            # Check if every file can be found
            if os.path.isfile(file):
                file_list.append(file)
            else:
                file_found = False
                # Check if file is located in one of the additional file dirs
                for additional_file_dir in self.additional_file_dirs:
                    new_file_path = os.path.join(additional_file_dir, file)
                    if debug:
                        print(
                            f"file not found check in additional file dirs: '{new_file_path}'"
                        )
                    if os.path.isfile(new_file_path):
                        file_list.append(new_file_path)
                        file_found = True
                        break
                if not file_found:
                    raise Exception(f"File was not found: {file}")
        return file_list

    def genanki_write_deck_to_file(self, output_file_path: str, debug=False):
        temp_genanki_anki_deck = self.genanki_create_deck(
            self.model.genanki_create_model(), self.additional_file_dirs, debug=debug
        )
        temp_genanki_anki_deck_package = genanki.Package(temp_genanki_anki_deck)
        temp_genanki_anki_deck_package.media_files = self.get_local_files_from_notes(
            debug=debug
        )
        temp_genanki_anki_deck_package.write_to_file(output_file_path)

    def md_write_deck_to_file(
        self,
        output_file_path: str,
        local_asset_dir_path: Optional[str] = None,
        debug=False,
    ):
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(f"# {self.name} ({self.guid})")
            for note in self.notes:
                file.write("\n\n")
                file.write(
                    note.md_create_string(local_asset_dir_path=local_asset_dir_path)
                )
            file.write("\n")

    def md_backup_deck_to_directory(self, output_dir_path: str, debug=False):
        if not os.path.isdir(output_dir_path):
            os.mkdir(output_dir_path)
        asset_dir_path = os.path.join(output_dir_path, "assets")
        if not os.path.isdir(asset_dir_path):
            os.mkdir(asset_dir_path)
        local_asset_dir_path = os.path.relpath(asset_dir_path, output_dir_path)
        self.md_write_deck_to_file(
            os.path.join(output_dir_path, "document.md"),
            local_asset_dir_path=local_asset_dir_path,
        )
        for file in self.get_local_files_from_notes(debug=debug):
            shutil.copyfile(file, os.path.join(asset_dir_path, os.path.basename(file)))


def download_script_files(
    dir_path: str = os.path.join(CURRENT_DIR, "temp"),
    skip_download_if_existing: bool = True,
):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    if (
        not os.path.isfile(os.path.join(dir_path, HLJS_CSS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            HLJS_CSS_URL, os.path.join(dir_path, HLJS_CSS_FILE_NAME)
        )
    if (
        not os.path.isfile(os.path.join(dir_path, HLJS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(HLJS_URL, os.path.join(dir_path, HLJS_FILE_NAME))
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_CSS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            KATEX_CSS_URL, os.path.join(dir_path, KATEX_CSS_FILE_NAME)
        )
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(KATEX_URL, os.path.join(dir_path, KATEX_FILE_NAME))
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            KATEX_AUTO_RENDERER_URL,
            os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME),
        )


def create_katex_highlightjs_anki_deck_model(
    dir_path: str = os.path.join(CURRENT_DIR, "temp"),
    skip_download_if_existing: bool = True,
    online: bool = True,
    debug=False,
) -> AnkiModel:
    highlightjs_css_template_code = ""
    highlightjs_js_template_code = ""
    katex_css_template_code = ""
    katex_js_template_code = ""

    if online:
        katex_js_template_code += (
            f'<link rel="stylesheet" href="{KATEX_CSS_URL}" crossorigin="anonymous">\n'
            f'<script src="{KATEX_URL}" crossorigin="anonymous"></script>\n'
            f'<script src="{KATEX_AUTO_RENDERER_URL}" crossorigin="anonymous"></script>\n'
        )
        highlightjs_js_template_code += (
            f'<link rel="stylesheet" href="{HLJS_CSS_URL}" crossorigin="anonymous">\n'
            f'<script src="{HLJS_URL}" crossorigin="anonymous"></script>\n'
        )

        if debug:
            print(f"katex_js_template_code[online]: {katex_js_template_code}")
            print(
                f"highlightjs_js_template_code[online]: {highlightjs_js_template_code}"
            )
    else:
        download_script_files(
            dir_path=dir_path, skip_download_if_existing=skip_download_if_existing
        )
        # Get source code to highlighting source code
        with open(
            os.path.join(dir_path, HLJS_CSS_FILE_NAME), "r"
        ) as highlightjs_css_file:
            highlightjs_css_template_code += highlightjs_css_file.read()
        with open(os.path.join(dir_path, HLJS_FILE_NAME), "r") as hljs_script_file:
            highlightjs_js_template_code += (
                f"\n<script>\n{hljs_script_file.read()}\n</script>"
            )

        if debug:
            print(f"highlightjs_css_template_code: {highlightjs_css_template_code}")
            print(f"highlightjs_js_template_code: {highlightjs_css_template_code}")

        # Get source code to render LaTeX math code
        with open(os.path.join(dir_path, KATEX_CSS_FILE_NAME), "r") as katex_css_file:
            katex_css_template_code += katex_css_file.read()
        with open(os.path.join(dir_path, KATEX_FILE_NAME), "r") as katex_file:
            katex_js_template_code += f"\n<script>\n{katex_file.read()}\n</script>"
        with open(
            os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME), "r"
        ) as katex_auto_renderer_file:
            katex_js_template_code += (
                f"\n<script>\n{katex_auto_renderer_file.read()}\n</script>"
            )

        if debug:
            print(f"katex_css_template_code: {katex_css_template_code}")
            print(f"katex_js_template_code: {katex_js_template_code}")

    with open(CSS_GENERAL_FILE_PATH, "r") as cssFile:
        css_code = cssFile.read()
    with open(HIGHLIGHTJS_SCRIPT_FILE_PATH, "r") as highlightjs_script_file:
        highlightjs_js_template_code += (
            f"\n<script>\n{highlightjs_script_file.read()}\n</script>"
        )
    with open(KATEXT_FILE_SCRIPT_PATH, "r") as katex_file:
        katex_js_template_code += f"\n<script>\n{katex_file.read()}\n</script>"

    online_state = "online" if online else "offline"
    return AnkiModel(
        guid=999990001,
        name=f"Md2Anki card (KaTeX {KATEX_VERSION}, HighlightJs {HLJS_VERSION}, {online_state})",
        description="Card with integrated KaTeX and HighlightJs support",
        css=katex_css_template_code + highlightjs_css_template_code + css_code,
        js=katex_js_template_code + highlightjs_js_template_code,
    )


class ParseSectionState(Enum):
    NONE = ("NONE",)
    HEADER = ("HEADER",)
    QUESTION_HEADER = ("QUESTION_HEADER",)
    QUESTION_ANSWER_SEPERATOR = ("QUESTION_ANSWER_SEPERATOR",)
    ANSWER = ("ANSWER",)


def parse_header(md_file_line: str, debug_this=False) -> Optional[AnkiDeck]:
    regex_header = re.compile(r"^# (.+?)\s+\((\d+)\)\s+$")
    regex_header_without_id = re.compile(r"^# (.+?)\s+$")

    regex_header_match = regex_header.match(md_file_line)
    regex_header_without_id_match = regex_header_without_id.match(md_file_line)

    if regex_header_match is not None:
        temp_anki_deck = AnkiDeck(
            name=regex_header_match.group(1), guid=int(regex_header_match.group(2))
        )
        if debug_this:
            print(
                f"> Found header (name={temp_anki_deck.name},guid={temp_anki_deck.guid})"
            )
        return temp_anki_deck
    elif regex_header_without_id_match is not None:
        temp_anki_deck = AnkiDeck(
            name=regex_header_without_id_match.group(1), guid=create_unique_id_int()
        )
        if debug_this:
            print(f"> Found header without id (name={temp_anki_deck.name})")
        return temp_anki_deck


def parse_question_header(
    md_file_line: str, debug_this=False
) -> Optional[AnkiDeckNote]:
    regex_question_header = re.compile(r"^## (.+?)\s+\((.+?)\)\s+$")
    regex_question_header_without_id = re.compile(r"^## (.+?)\s+$")

    regex_question_header_match = regex_question_header.match(md_file_line)
    regex_question_header_without_id_match = regex_question_header_without_id.match(
        md_file_line
    )

    if regex_question_header_match is not None:
        temp_anki_note = AnkiDeckNote(
            question=regex_question_header_match.group(1),
            guid=regex_question_header_match.group(2),
        )
        if debug_this:
            print(
                f"> Found question header (question={temp_anki_note.question},id={temp_anki_note.guid})"
            )
        return temp_anki_note
    elif regex_question_header_without_id_match is not None:
        temp_anki_note = AnkiDeckNote(
            question=regex_question_header_without_id_match.group(1),
            guid=create_unique_id(),
        )
        if debug_this:
            print(
                f"> Found question header without id (question={temp_anki_note.question})"
            )
        return temp_anki_note


def parse_md_file_to_anki_deck(text_file: TextIO, debug=False) -> AnkiDeck:
    empty_lines: int = 0
    parse_state: ParseSectionState = ParseSectionState.NONE

    temp_anki_deck: AnkiDeck = AnkiDeck()
    temp_anki_note: AnkiDeckNote = AnkiDeckNote()

    for line in text_file:

        # Strip line from newlines
        line_stripped = line.strip()

        if debug:
            print(
                f"line='{line_stripped}' state={parse_state.name} empty_lines={empty_lines}"
            )

        # Skip empty lines
        if len(line_stripped) == 0:
            empty_lines += 1
            if debug:
                print(f"> Found empty line")
            continue

        # Parse states
        if parse_state == ParseSectionState.NONE:
            temp_optional_anki_deck = parse_header(line, debug_this=debug)
            if temp_optional_anki_deck is not None:
                temp_anki_deck = temp_optional_anki_deck
                parse_state = ParseSectionState.HEADER
                empty_lines = 0
            else:
                print(f"WARNING: Header was not found: '{line_stripped}'")
        elif parse_state == ParseSectionState.HEADER:
            # Header was read -> expect question header
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_note = temp_optional_anki_note
                parse_state = ParseSectionState.QUESTION_HEADER
                empty_lines = 0
            else:
                print(f"WARNING: Question header was not found: '{line_stripped}'")
        elif parse_state == ParseSectionState.QUESTION_HEADER:
            # Question header was read -> expect question block or answer block
            # (if separator is found move content from answer to question)
            if line_stripped == "---":
                temp_anki_note.question += f"\n\n{temp_anki_note.answer}"
                temp_anki_note.answer = ""
                parse_state = ParseSectionState.QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(
                        f"> Found question answer separator (question={temp_anki_note.question})"
                    )
            else:
                if len(temp_anki_note.answer.rstrip()) != 0:
                    temp_anki_note.answer += "\n" * (empty_lines + 1)
                temp_anki_note.answer += line.rstrip()
                parse_state = ParseSectionState.ANSWER
                empty_lines = 0
                if debug:
                    print(f"> Found new answer line (answer={temp_anki_note.answer})")
        elif parse_state == ParseSectionState.ANSWER:
            # Question answer was read -> expect more answer lines or answer/question/separator or next question header
            if line_stripped == "---":
                temp_anki_note.question += f"\n\n{temp_anki_note.answer}"
                temp_anki_note.answer = ""
                parse_state = ParseSectionState.QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(
                        f"> Found question answer separator (question={temp_anki_note.question})"
                    )
            else:
                temp_optional_anki_note = parse_question_header(line, debug_this=debug)
                if temp_optional_anki_note is not None:
                    temp_anki_deck.notes.append(temp_anki_note)
                    if debug:
                        print(
                            f"> new note was appended to deck (notes={temp_anki_deck.notes})"
                        )
                    temp_anki_note = temp_optional_anki_note
                    parse_state = ParseSectionState.QUESTION_HEADER
                    empty_lines = 0
                else:
                    if len(temp_anki_note.answer.rstrip()) != 0:
                        temp_anki_note.answer += "\n" * (empty_lines + 1)
                    temp_anki_note.answer += line.rstrip()
                    parse_state = ParseSectionState.ANSWER
                    empty_lines = 0
                    if debug:
                        print(
                            f"> Found new answer line (answer={temp_anki_note.answer})"
                        )
        elif parse_state == ParseSectionState.QUESTION_ANSWER_SEPERATOR:
            # Question answer separator was read -> expect answer block or new question block
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_deck.notes.append(temp_anki_note)
                if debug:
                    print(
                        f"> new note was appended to deck (notes={temp_anki_deck.notes})"
                    )
                temp_anki_note = temp_optional_anki_note
                parse_state = ParseSectionState.QUESTION_HEADER
                empty_lines = 0
            else:
                if len(temp_anki_note.answer.rstrip()) != 0:
                    temp_anki_note.answer += "\n" * (empty_lines + 1)
                temp_anki_note.answer += line.rstrip()
                parse_state = ParseSectionState.ANSWER
                empty_lines = 0
                if debug:
                    print(f"> Found answer line (answer={temp_anki_note.answer})")

    if parse_state == ParseSectionState.ANSWER:
        temp_anki_deck.notes.append(temp_anki_note)
        if debug:
            print(f"> new note was appended to deck (notes={temp_anki_deck.notes})")

    return temp_anki_deck


# Main method (This will not be executed when file is imported)
if __name__ == "__main__":

    debug_flag_found = False

    nextAnkiOutFilePath: bool = False
    nextMdOutFilePath: bool = False
    nextRmResPrefix: bool = False
    nextBackupDirFilePath: bool = False

    argsToRemove: List[str] = [sys.argv[0]]

    # Simple (activate) options
    for x in sys.argv:
        if x == "--help" or x == "-help" or x == "-h":
            cli_help()
            exit(0)
        if x == "--version" or x == "-version" or x == "-v":
            cli_version()
            exit(0)

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    if len(sys.argv) < 1:
        print("No input file was specified!")
        sys.exit(1)

    md_input_file_path = sys.argv[0]
    md_output_file_path = sys.argv[0]
    argsToRemove.append(sys.argv[0])
    anki_output_file_path = f"{os.path.basename(md_input_file_path)}.apkg"
    backup_dir_output_file_path = None

    if not os.path.isfile(md_input_file_path):
        print(f"Input file was not found: '{md_input_file_path}'")
        sys.exit(1)

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    additional_file_dirs: List[str] = []

    for x in sys.argv:
        if x == "-d":
            argsToRemove.append(x)
            debug_flag_found = True
            print("> Debugging was turned on")
        elif nextAnkiOutFilePath:
            nextAnkiOutFilePath = False
            anki_output_file_path = x
            argsToRemove.append(x)
        elif nextMdOutFilePath:
            nextMdOutFilePath = False
            md_output_file_path = x
            argsToRemove.append(x)
        elif nextRmResPrefix:
            nextRmResPrefix = False
            additional_file_dirs.append(x)
            argsToRemove.append(x)
        elif nextBackupDirFilePath:
            nextBackupDirFilePath = False
            backup_dir_output_file_path = x
            argsToRemove.append(x)
        elif x == "-o-anki":
            nextAnkiOutFilePath = True
            argsToRemove.append(x)
        elif x == "-o-md":
            nextMdOutFilePath = True
            argsToRemove.append(x)
        elif x == "-file-dir":
            nextRmResPrefix = True
            argsToRemove.append(x)
        elif x == "-o-backup-dir":
            nextBackupDirFilePath = True
            argsToRemove.append(x)
        else:
            print(f"Unknown option found: '{x}'")
            sys.exit(1)

    anki_deck: AnkiDeck
    with open(md_input_file_path, "r", encoding="utf-8") as md_file:
        anki_deck = parse_md_file_to_anki_deck(md_file, debug=debug_flag_found)

    anki_deck.additional_file_dirs = additional_file_dirs
    anki_deck.model = create_katex_highlightjs_anki_deck_model(
        online=True, debug=debug_flag_found
    )

    anki_deck.genanki_write_deck_to_file(anki_output_file_path, debug=debug_flag_found)

    if md_output_file_path is not None:
        anki_deck.md_write_deck_to_file(md_output_file_path, debug=debug_flag_found)
    if backup_dir_output_file_path is not None:
        anki_deck.md_backup_deck_to_directory(
            backup_dir_output_file_path, debug=debug_flag_found
        )
