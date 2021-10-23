#!/usr/bin/env python3

# Internal packages
import os.path
import random
import re
import sys
import urllib.request
import html
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, TextIO, Set, Tuple
from uuid import uuid4

# Installed packages (via pip)
import genanki
import markdown

VERSION_MAJOR: int = 2
VERSION_MINOR: int = 5
VERSION_PATCH: int = 2

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CSS_GENERAL_FILE_PATH = os.path.join(CURRENT_DIR, "stylesheet.css")
HIGHLIGHTJS_SCRIPT_FILE_PATH = os.path.join(CURRENT_DIR, "highlightJs_renderer.js")
KATEXT_FILE_SCRIPT_PATH = os.path.join(CURRENT_DIR, "kaTex_renderer.js")

HLJS_VERSION = "11.3.1"
HLJS_CSS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/styles/default.min.css"
HLJS_CSS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.css"
HLJS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/highlight.min.js"
HLJS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.js"

KATEX_VERSION = "0.13.18"
KATEX_CSS_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css"
KATEX_CSS_FILE_NAME = f"katex_{KATEX_VERSION}.min.css"
KATEX_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js"
KATEX_FILE_NAME = f"katex_{KATEX_VERSION}.min.js"
KATEX_AUTO_RENDERER_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js"
KATEX_AUTO_RENDERER_FILE_NAME = f"katex_auto_render_{KATEX_VERSION}.min.js"


def cli_help(is_package=False):
    if is_package:
        runCommand = "md2anki"
    else:
        runCommand = "python3 md2anki.py"
    print(
        f"$ {runCommand} MD_FILE [MD_FILE...] [OPTIONS]\n\n"
        + "Create an anki deck file (.apkg) from one or more markdown\n"
        + "documents. If no custom output path is given the file name\n"
        + "of the document (+ .apkg) is used.\n\n"
        + "Options:\n"
        + "\t-d\t\t\tActivate debugging output\n"
        + "\t-o-anki FILE_PATH\tCustom anki deck output\n"
        + "\t                 \tfile path\n"
        + "\t-o-md FILE_PATH\t\tCustom markdown output\n"
        + "\t               \t\tfile path (multiple files\n"
        + "\t               \t\twill be merged into one)\n"
        + "\t-o-md-dir DIR_PATH\tCustom markdown output\n"
        + "\t                  \tdirectory path\n"
        + "\t-o-backup-dir DIR_PATH\tBackup the input and its\n"
        + "\t                      \tlocal assets with a build\n"
        + "\t                      \tscript\n"
        + "\t-file-dir DIR_PATH\tAdditional file directory\n"
        + "\t                  \twhich can be supplied\n"
        + "\t                  \tmultiple times\n"
        + "\n"
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


REGEX_MD_TAG = re.compile(r"\`{=:(.*?):=}\`")
"""
Regex expression to parse a markdown tag notation: '`{=:tag list string:=}`'
The first group is the 'tag list string'.
"""

REGEX_MD_IMAGE_FILE = re.compile(
    r"!\[(.*?)\]\((.*?)\)(?:\{(?:\s*?width\s*?=(.+?)[\s,;]*?)?(?:\s*?height\s*?=(.+?)[\s,;]*?)?\})?"
)
"""
Regex expression to parse a markdown image notation: '![alt text](source path){ width=100px, height=200px }'
The first group is the 'alt text' and the second one the 'source path' while optionally there is a third and fourth
group for the width and height if found.
"""


@dataclass
class Md2AnkiArgs:
    """
    Contains all information of the md2anki command line arguments
    """

    additional_file_dirs: List[str] = field(default_factory=lambda: list())
    md_input_file_paths: List[str] = field(default_factory=lambda: list())
    md_output_file_path: Optional[str] = None
    md_output_dir_path: Optional[str] = None
    anki_output_file_path: Optional[str] = None
    backup_output_dir_path: Optional[str] = None

    enable_debugging: bool = False
    show_help: bool = False
    show_version: bool = False

    error_message: Optional[str] = None
    error_code: int = 0


def parse_cli_args(args: List[str]) -> Md2AnkiArgs:
    """Parse the command line args"""
    md2AnkiArgs = Md2AnkiArgs()
    argsToRemove: List[str] = []

    # Simple "global" options
    for arg in args:
        if arg == "-d":
            md2AnkiArgs.enable_debugging = True
            print("> Debugging was enabled")
            argsToRemove.append(arg)
        if arg == "--help":
            md2AnkiArgs.show_help = True
            return md2AnkiArgs
        if arg == "--version":
            md2AnkiArgs.show_version = True
            return md2AnkiArgs

    # Remove all parsed "global" options from the arg list
    for argToRemove in argsToRemove:
        args.pop(args.index(argToRemove))
    argsToRemove = []

    for arg in args:
        # If a supported option is found break out of the loop
        if (
            arg == "-o-anki"
            or arg == "-o-md"
            or arg == "-o-md-dir"
            or arg == "-o-backup-dir"
            or arg == "-file-dir"
        ):
            break
        else:
            md2AnkiArgs.md_input_file_paths.append(arg)
            argsToRemove.append(arg)

    # Remove all parsed input file paths from the arg list
    for argToRemove in argsToRemove:
        args.pop(args.index(argToRemove))
    argsToRemove = []

    # If no args are found throw error
    if len(md2AnkiArgs.md_input_file_paths) == 0:
        md2AnkiArgs.error_code = 1
        md2AnkiArgs.error_message = "No input file was specified!"
        return md2AnkiArgs

    # If an input file is not found throw error
    for md_input_file_path in md2AnkiArgs.md_input_file_paths:
        if not os.path.isfile(md_input_file_path):
            md2AnkiArgs.error_code = 1
            absolute_path = os.path.abspath(md_input_file_path)
            md2AnkiArgs.error_message = (
                f"Input file was not found: '{md_input_file_path}'/'{absolute_path=}'"
            )
            return md2AnkiArgs

    nextAnkiOutFilePath: Optional[bool] = False
    nextMdOutFilePath: Optional[bool] = False
    nextMdOutDirPath: Optional[bool] = False
    nextFileDirPath: bool = False
    nextBackupDirFilePath: Optional[bool] = False

    # Set default arguments
    md2AnkiArgs.anki_output_file_path = os.path.join(
        os.path.dirname(md2AnkiArgs.md_input_file_paths[0]),
        f"{os.path.splitext(os.path.basename(md2AnkiArgs.md_input_file_paths[0]))[0]}.apkg",
    )

    for x in args:
        if nextAnkiOutFilePath:
            nextAnkiOutFilePath = None
            md2AnkiArgs.anki_output_file_path = x
            argsToRemove.append(x)
        elif nextMdOutFilePath:
            nextMdOutFilePath = None
            md2AnkiArgs.md_output_file_path = x
            argsToRemove.append(x)
        elif nextMdOutDirPath:
            nextMdOutDirPath = None
            md2AnkiArgs.md_output_dir_path = x
            argsToRemove.append(x)
        elif nextFileDirPath:
            nextFileDirPath = None
            md2AnkiArgs.additional_file_dirs.append(x)
            argsToRemove.append(x)
        elif nextBackupDirFilePath:
            nextBackupDirFilePath = None
            md2AnkiArgs.backup_output_dir_path = x
            argsToRemove.append(x)
        elif x == "-o-anki":
            if nextAnkiOutFilePath is None:
                md2AnkiArgs.error_code = 1
                md2AnkiArgs.error_message = f"Option was found multiple times: '{x}'"
                return md2AnkiArgs
            nextAnkiOutFilePath = True
            argsToRemove.append(x)
        elif x == "-o-md":
            if nextMdOutFilePath is None:
                md2AnkiArgs.error_code = 1
                md2AnkiArgs.error_message = f"Option was found multiple times: '{x}'"
                return md2AnkiArgs
            nextMdOutFilePath = True
            argsToRemove.append(x)
        elif x == "-o-md-dir":
            if nextMdOutDirPath is None:
                md2AnkiArgs.error_code = 1
                md2AnkiArgs.error_message = f"Option was found multiple times: '{x}'"
                return md2AnkiArgs
            nextMdOutDirPath = True
            argsToRemove.append(x)
        elif x == "-file-dir":
            nextFileDirPath = True
            argsToRemove.append(x)
        elif x == "-o-backup-dir":
            if nextBackupDirFilePath is None:
                md2AnkiArgs.error_code = 1
                md2AnkiArgs.error_message = f"Option was found multiple times: '{x}'"
                return md2AnkiArgs
            nextBackupDirFilePath = True
            argsToRemove.append(x)
        else:
            md2AnkiArgs.error_code = 1
            md2AnkiArgs.error_message = f"Unknown option found: '{x}'"
            return md2AnkiArgs

    return md2AnkiArgs


@dataclass
class AnkiDeckNote:
    """
    Contains all information of an anki deck note
    """

    question: str = ""
    """Question multi line string"""
    answer: str = ""
    """Answer multi line string"""
    tags: Set[str] = field(default_factory=lambda: set())
    """Tags"""
    guid: str = create_unique_id()
    """Unique id"""

    def get_used_files(self) -> Set[str]:
        """Get the used local files of the note"""
        files: Set[str] = set()

        def add_used_files(regex_group_match):
            """Detect and add all local image path to the created set"""
            filepath = regex_group_match.group(2)
            # Only add file path if it is not an URL
            if not filepath.startswith("https://") and not filepath.startswith(
                "http://"
            ):
                files.add(filepath)
            # Only return string for correct type checking
            return ""

        re.sub(REGEX_MD_IMAGE_FILE, add_used_files, self.question)
        re.sub(REGEX_MD_IMAGE_FILE, add_used_files, self.answer)
        return files

    def get_used_tags(self) -> Set[str]:
        """Get the used tags of the note"""
        tags: Set[str] = set()

        def add_used_tags(regex_group_match):
            """Detect and add all local found tags to the created set"""
            tag_strings = regex_group_match.group(1).split(",")
            for tag_string in tag_strings:
                tag = tag_string.strip()
                if " " in tag:
                    old_tag = tag
                    tag = tag.replace(" ", "_")
                    print(
                        f"WARNING: A tag with spaces was found: '{old_tag}'",
                        f"and rewritten to: '{tag}'",
                    )
                if len(tag) > 0:
                    tags.add(tag)
            # Only return string for correct type checking
            return ""

        re.sub(REGEX_MD_TAG, add_used_tags, self.question)
        re.sub(REGEX_MD_TAG, add_used_tags, self.answer)
        return tags

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

        # Extract tags
        tags = self.get_used_tags()

        if debug:
            print(f"found_tags={tags}")
            print(f"temp_question_tag_fix={temp_question}")

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
            REGEX_MD_IMAGE_FILE,
            extract_image_info_and_update_image_path,
            temp_question,
        )
        temp_answer = re.sub(
            REGEX_MD_IMAGE_FILE, extract_image_info_and_update_image_path, temp_answer
        )

        if debug:
            print(
                f">> Card text for question before markdown module parsing: '{temp_question}'"
            )
            print(
                f">> Card text for question before markdown module parsing: '{temp_answer}'"
            )

        # Dumb fix (1): Collect all math sections to later overwrite the from python markdown updated sections
        regex_dumb = r"(\${2}(?:[^\$]|\n)+?\${2}|\${1}.+?\${1})"
        all_math_sections_question = re.findall(regex_dumb, temp_question)
        all_math_sections_answer = re.findall(regex_dumb, temp_answer)
        temp_question = re.sub(regex_dumb, "$placeholder$", temp_question)
        temp_answer = re.sub(regex_dumb, "$placeholder$", temp_answer)
        if debug:
            print(f"all_math_sections_question={all_math_sections_question}")
            print(f"all_math_sections_answer={all_math_sections_answer}")

        # Render tables
        temp_question = markdown.markdown(
            temp_question, extensions=["markdown.extensions.tables"], tab_length=2
        )
        temp_answer = markdown.markdown(
            temp_answer, extensions=["markdown.extensions.tables"], tab_length=2
        )

        if debug:
            print(
                f">> Card text for question after markdown module parsing: '{temp_question}'"
            )
            print(
                f">> Card text for question after markdown module parsing: '{temp_answer}'"
            )

        # This is for now dropped since the rendering does not seem to be faster
        # or look as good as the current kaTex rendering
        # def return_math_section_in_new_format(math_section: str):
        #    if math_section.startswith("$$"):
        #        math_section_fixed_end = re.sub(r"\$\$$", "\\]", math_section)
        #        math_section_fixed = re.sub(r"^\$\$", "\\[", math_section_fixed_end)
        #        print(f"{math_section=}{math_section_fixed=}")
        #        return math_section_fixed
        #    else:
        #        math_section_fixed_end = re.sub(r"\$$", "\\)", math_section)
        #        math_section_fixed = re.sub(r"^\$", "\\(", math_section_fixed_end)
        #        print(f"{math_section=}{math_section_fixed=}")
        #        return math_section_fixed

        # Dumb fix (2): Collect all math sections to later overwrite the from python markdown updated sections
        temp_question = re.sub(
            regex_dumb,
            lambda regex_group_match: html.escape(all_math_sections_question.pop(0)),
            temp_question,
        )
        temp_answer = re.sub(
            regex_dumb,
            lambda regex_group_match: html.escape(all_math_sections_answer.pop(0)),
            temp_answer,
        )
        if debug:
            print(f"temp_question_math_fix={temp_question}")
            print(f"temp_answer_math_fix={temp_answer}")

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
            guid=self.guid,
            model=anki_card_model,
            fields=[temp_question, temp_answer],
            tags=list(tags.union(self.tags)),
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
            REGEX_MD_IMAGE_FILE, extract_image_info_and_update_image_path, text_input
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
        # Uncomment to debug what is a question_body and what is an answer
        # question_body = f"[question_body]{question_body}[/question_body]"
        # answer = f"[answer]{answer}[/answer]"
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
    description: str = ""
    """Description of anki deck"""
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

    def get_used_global_tags(self) -> Set[str]:
        """Get the used global tags of the anki deck"""
        tags: Set[str] = set()

        def add_used_global_tags(regex_group_match):
            """Detect and add all local found tags to the created set"""
            tag_strings = regex_group_match.group(1).split(",")
            for tag_string in tag_strings:
                tag = tag_string.strip()
                if " " in tag:
                    old_tag = tag
                    tag = tag.replace(" ", "_")
                    print(
                        f"WARNING: A global tag with spaces was found: '{old_tag}'",
                        f"and rewritten to: '{tag}'",
                    )
                if len(tag) > 0:
                    tags.add(tag)
            # Only return string for correct type checking
            return ""

        re.sub(REGEX_MD_TAG, add_used_global_tags, self.description)
        return tags

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
                    raise Exception(
                        f"File was not found: {file} ({self.additional_file_dirs=})"
                    )
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
            if len(self.description) > 0:
                file.write(f"\n{self.description}")
            for note in self.notes:
                file.write("\n\n")
                file.write(
                    note.md_create_string(local_asset_dir_path=local_asset_dir_path)
                )
            file.write("\n")

    def md_backup_deck_to_directory(
        self,
        output_dir_path: str,
        multi_page_part_of: Optional[Tuple[int, int]] = None,
        another_page_has_assets=False,
        debug=False,
    ):
        if not os.path.isdir(output_dir_path):
            os.mkdir(output_dir_path)
        asset_dir_path = os.path.join(output_dir_path, "assets")
        local_asset_dir_path = os.path.relpath(asset_dir_path, output_dir_path)
        if multi_page_part_of is not None:
            document_name = f"document_part_{multi_page_part_of[0]}.md"
        else:
            document_name = "document.md"
        self.md_write_deck_to_file(
            os.path.join(output_dir_path, document_name),
            local_asset_dir_path=local_asset_dir_path,
        )
        filesToCopy = self.get_local_files_from_notes(debug=debug)
        if len(filesToCopy) > 0:
            if not os.path.isdir(asset_dir_path):
                os.mkdir(asset_dir_path)
            for file in filesToCopy:
                shutil.copyfile(
                    file, os.path.join(asset_dir_path, os.path.basename(file))
                )
        bash_build_script = os.path.join(output_dir_path, "build.sh")
        with open(bash_build_script, "w", encoding="utf-8") as file:
            file.write("#!/usr/bin/env bash\n\n")
            file.write('if [ ! -d "Md2Anki" ] ; then\n')
            file.write(
                '    git clone "https://github.com/AnonymerNiklasistanonym/Md2Anki.git"\n'
            )
            file.write("fi\n")
            file.write(f"./Md2Anki/run.sh")
            if multi_page_part_of is not None:
                for x in range(1, multi_page_part_of[1] + 1):
                    file.write(f' "../document_part_{x}.md"')
            else:
                file.write(f' "../{document_name}"')
            if len(filesToCopy) > 0 or another_page_has_assets:
                file.write(' -file-dir "../"')
            file.write(' -o-anki "../anki_deck.apkg" "$@"\n')
        pwsh_build_script = os.path.join(output_dir_path, "build.ps1")
        with open(pwsh_build_script, "w", encoding="utf-8") as file:
            file.write("#!/usr/bin/env pwsh\n\n")
            file.write(
                "$Md2AnkiGitDir = Join-Path $PSScriptRoot -ChildPath Md2Anki\n\n"
            )
            file.write("if (-not (Test-Path -LiteralPath $Md2AnkiGitDir)) {\n")
            file.write(
                '    git clone "https://github.com/AnonymerNiklasistanonym/Md2Anki.git"\n'
            )
            file.write("}\n\n")
            file.write("$Md2AnkiRun = Join-Path $Md2AnkiGitDir -ChildPath run.ps1\n")
            if multi_page_part_of is not None:
                for x in range(1, multi_page_part_of[1] + 1):
                    file.write(
                        f"$Md2AnkiDocumentPart{x} = Join-Path $PSScriptRoot -ChildPath document_part_{x}.md\n"
                    )
            else:
                file.write(
                    "$Md2AnkiDocument = Join-Path $PSScriptRoot -ChildPath document.md\n"
                )
            file.write(
                "$Md2AnkiApkg = Join-Path $PSScriptRoot -ChildPath anki_deck.apkg\n\n"
            )
            file.write('Invoke-Expression "$Md2AnkiRun')
            if multi_page_part_of is not None:
                for x in range(1, multi_page_part_of[1] + 1):
                    file.write(f" $Md2AnkiDocumentPart{x}")
            else:
                file.write(" $Md2AnkiDocument")
            if len(filesToCopy) > 0 or another_page_has_assets:
                file.write(" -file-dir $PSScriptRoot")
            file.write(' -o-anki $Md2AnkiApkg $args"\n')


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
        guid=999990002,
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
    ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR = ("ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR",)


def parse_header(md_file_line: str, debug_this=False) -> Optional[AnkiDeck]:
    regex_header = re.compile(r"^# (.+?)\s+\((\d+)\)\s+$")
    regex_header_without_id = re.compile(r"^# (.+?)\s+$")

    regex_header_match = regex_header.match(md_file_line)
    regex_header_without_id_match = regex_header_without_id.match(md_file_line)

    if regex_header_match is not None:
        temp_anki_deck = AnkiDeck(
            name=regex_header_match.group(1),
            guid=int(regex_header_match.group(2)),
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
    regex_question_header = re.compile(r"^## (.+?)\s+\(([^()\s]+?)\)\s+$")
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
                if temp_anki_deck is not None:
                    temp_anki_deck.description = temp_anki_deck.description.rstrip()
            elif temp_anki_deck is not None:
                temp_anki_deck.description += (
                    (empty_lines * "\n") + line_stripped + "\n"
                )
                empty_lines = 0
                if debug:
                    print(
                        f"> Found anki deck description line (question={temp_anki_deck.description})"
                    )
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
                    temp_anki_note.tags = temp_anki_note.tags.union(
                        temp_anki_deck.get_used_global_tags()
                    )
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
        elif parse_state == ParseSectionState.ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR:
            # Question answer seperator was read -> expect more answer lines or next question header
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_note.tags = temp_anki_note.tags.union(
                    temp_anki_deck.get_used_global_tags()
                )
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
                parse_state = ParseSectionState.ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(f"> Found new answer line (answer={temp_anki_note.answer})")
                if line_stripped == "---":
                    print(
                        f"WARNING: Found another question answer separator (question={temp_anki_note.question},"
                        f"current_answer={temp_anki_note.answer})"
                    )
        elif parse_state == ParseSectionState.QUESTION_ANSWER_SEPERATOR:
            # Question answer separator was read -> expect answer block or new question block
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_note.tags = temp_anki_note.tags.union(
                    temp_anki_deck.get_used_global_tags()
                )
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
                parse_state = ParseSectionState.ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(f"> Found answer line (answer={temp_anki_note.answer})")

    an_note_is_still_unprocessed_in_answer_state = (
        parse_state == ParseSectionState.ANSWER
        or parse_state == ParseSectionState.ANSWER_AFTER_QUESTION_ANSWER_SEPERATOR
    )
    if an_note_is_still_unprocessed_in_answer_state:
        temp_anki_note.tags = temp_anki_note.tags.union(
            temp_anki_deck.get_used_global_tags()
        )
        temp_anki_deck.notes.append(temp_anki_note)
        if debug:
            print(f"> new note was appended to deck (notes={temp_anki_deck.notes})")

    return temp_anki_deck


def main_method(args: Md2AnkiArgs, is_package=False) -> int:
    debug_flag_found = args.enable_debugging

    if args.error_code != 0:
        if args.error_message is not None:
            print(args.error_message)
        return args.error_code
    if args.show_help:
        cli_help()
        return 0
    if args.show_version:
        cli_version()
        return 0

    anki_decks: List[AnkiDeck] = list()
    for md_input_file_path in args.md_input_file_paths:
        with open(md_input_file_path, "r", encoding="utf-8") as md_file:
            anki_deck = parse_md_file_to_anki_deck(md_file, debug=debug_flag_found)
            anki_deck.additional_file_dirs = args.additional_file_dirs
            anki_decks.append(anki_deck)

    for anki_deck in anki_decks:
        if anki_deck.name != anki_decks[0].name:
            print(
                f"The by the input files created decks have different names: {anki_deck.name}!={anki_decks[0].name}"
            )
            return 1
        if anki_deck.guid != anki_decks[0].guid:
            print(
                f"The by the input files created decks have different guids: {anki_deck.guid}!={anki_decks[0].guid}"
            )
            return 1

    if args.md_output_dir_path is not None:
        for anki_deck, md_input_file_path in zip(anki_decks, args.md_input_file_paths):
            anki_output_file_path = os.path.join(
                args.md_output_dir_path, os.path.basename(md_input_file_path)
            )
            anki_deck.md_write_deck_to_file(
                anki_output_file_path, debug=debug_flag_found
            )

    # Combine all decks into one
    final_anki_deck = anki_decks[0]
    for anki_deck in anki_decks[1:]:
        final_anki_deck.description += f"\n{anki_deck.description}"
        final_anki_deck.notes += anki_deck.notes

    final_anki_deck.model = create_katex_highlightjs_anki_deck_model(
        online=True, debug=debug_flag_found
    )

    final_anki_deck.genanki_write_deck_to_file(
        args.anki_output_file_path, debug=debug_flag_found
    )

    if args.md_output_file_path is not None:
        final_global_tags = final_anki_deck.get_used_global_tags()
        if len(anki_decks) > 1 and len(final_global_tags) > 0:
            print(
                f"WARNING: Global tags were found in the anki decks: '{final_global_tags}'",
                f"which will now apply to ALL cards!",
            )
        final_anki_deck.md_write_deck_to_file(
            args.md_output_file_path, debug=debug_flag_found
        )

    if args.backup_output_dir_path is not None:
        another_page_has_assets = False
        for anki_deck in anki_decks:
            if anki_deck.get_local_files_from_notes(debug=debug_flag_found):
                another_page_has_assets = True
                break
        for num, anki_deck in enumerate(anki_decks, start=1):
            if len(anki_decks) == 1:
                multi_page_part_of = None
            else:
                multi_page_part_of = (num, len(anki_decks))
            anki_deck.md_backup_deck_to_directory(
                args.backup_output_dir_path,
                multi_page_part_of,
                another_page_has_assets,
                debug=debug_flag_found,
            )
    return 0


# Main method (This will not be executed when file is imported)
if __name__ == "__main__":
    cliArgs = parse_cli_args(sys.argv[1:])
    exitCode = main_method(cliArgs)
    exit(exitCode)
