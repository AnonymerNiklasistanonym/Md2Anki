import html
import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Set, Optional, List, Tuple

import genanki
import markdown

from md2anki.create_id import create_unique_id_int, create_unique_id
from md2anki.info import (
    ANKI_SUBDECK_SEPARATOR,
    md2anki_url_git,
    md2anki_name,
    md2anki_version,
)

REGEX_MD_TAG = re.compile(r"`{=:(.*?):=}`")
"""
Regex expression to parse a markdown tag notation: '`{=:tag list string:=}`'
The first group is the 'tag list string'.
"""

REGEX_MD_IMAGE_FILE = re.compile(
    r"!\[(.*?)]\((.*?)\)(?:\{(?:\s*?width\s*?=(.+?)[\s,;]*?)?(?:\s*?height\s*?=(.+?)[\s,;]*?)?})?"
)
"""
Regex expression to parse a markdown image notation: '![alt text](source path){ width=100px, height=200px }'
The first group is the 'alt text' and the second one the 'source path' while optionally there is a third and fourth
group for the width and height if found.
"""


@dataclass
class MdSection:
    """
    Represents a markdown section of anki deck notes.
    """

    heading: str = ""
    content: str = ""
    section_name: str = ""

    def create_string(
        self, depth: int = 1, heading_prefix: Optional[str] = None
    ) -> str:
        output = f"{'#' * depth} {heading_prefix if heading_prefix is not None else ''}{self.heading}\n"
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

    def get_used_files(self) -> Set[str]:
        """Get the used local files of the note"""
        files: Set[str] = set()

        def add_used_files(regex_group_match):
            """Detect and add all local image path to the created set"""
            filepath = regex_group_match.group(2)
            # Only add file path if it is not a URL
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
        markdown_to_anki_html=True,
        debug=False,
    ) -> genanki.Note:
        """
        Args:
            anki_card_model: The card model
            additional_file_dirs_to_escape: File directories that contain (image) resources and should be escaped
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
        question_header = self.update_local_file_paths(
            question_header, local_asset_dir_path=local_asset_dir_path
        )
        question_body = self.update_local_file_paths(
            question_body, local_asset_dir_path=local_asset_dir_path
        )
        answer = self.update_local_file_paths(
            self.answer, local_asset_dir_path=local_asset_dir_path
        )
        return MdSection(
            f"{question_header} ({self.guid})", f"{question_body}\n\n{answer}".strip()
        )


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
    model: AnkiModel = field(default_factory=lambda: AnkiModel())
    """Model of cards of anki deck"""
    guid: int = create_unique_id_int()
    """Unique id of anki deck"""
    description: str = ""
    """Description of anki deck"""
    notes: List[AnkiNote] = field(default_factory=lambda: list())
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

    def genanki_create_anki_deck(self, debug=False) -> Tuple[genanki.Deck, List[str]]:
        genanki_anki_deck = self.genanki_create_deck(
            self.model.genanki_create_model(), self.additional_file_dirs, debug=debug
        )
        media_files = self.get_local_files_from_notes(debug=debug)
        return genanki_anki_deck, media_files

    def create_md_sections(
        self, local_asset_dir_path: Optional[str] = None
    ) -> Tuple[MdSection, List[MdSection]]:
        output: List[MdSection] = []
        for note in self.notes:
            output.append(
                note.create_md_section(local_asset_dir_path=local_asset_dir_path)
            )
        return (
            MdSection(
                f"{self.name} ({self.guid})", self.description, section_name=self.name
            ),
            output,
        )


def genanki_package_anki_decks_to_file(
    anki_decks: List[Tuple[genanki.Deck, List[str]]], output_file_path: str, debug=False
):
    anki_deck_package = genanki.Package([a[0] for a in anki_decks])
    media_files = [a[1] for a in anki_decks]
    anki_deck_package.media_files = [
        item for sublist in media_files for item in sublist
    ]
    anki_deck_package.write_to_file(output_file_path)
    if debug:
        print(
            f"Write anki decks {', '.join([a[0].name + ' (' + str(len(a[0].notes)) + ')' for a in anki_decks])} to "
            f"'{output_file_path}' [.apkg]"
        )


def md_merge_anki_decks_to_file(
    anki_decks: List[AnkiDeck],
    output_file_path: str,
    local_asset_dir_path: Optional[str] = None,
    initial_heading_depth: int = 1,
    debug=False,
):
    with open(output_file_path, "w", encoding="utf-8") as file:
        current_deck_heading_stack: List[str] = []
        for anki_deck in anki_decks:
            anki_deck_heading, anki_deck_notes = anki_deck.create_md_sections(
                local_asset_dir_path=local_asset_dir_path
            )
            heading_names = anki_deck_heading.section_name.split(ANKI_SUBDECK_SEPARATOR)
            headings = anki_deck_heading.heading.split(ANKI_SUBDECK_SEPARATOR)

            is_subdeck = len(heading_names) > 1
            if is_subdeck:
                anki_deck_heading.heading = heading_names[-1]
                for index, (new_heading_name, new_heading) in enumerate(
                    zip(heading_names, headings)
                ):
                    old_heading = (
                        current_deck_heading_stack[index]
                        if index < len(current_deck_heading_stack)
                        else None
                    )
                    if old_heading is None or not old_heading == new_heading_name:
                        file.write("\n")
                        file.write(
                            MdSection(new_heading).create_string(
                                depth=initial_heading_depth + len(heading_names) - 1
                            )
                        )
            else:
                if len(current_deck_heading_stack) > 0:
                    file.write("\n")
                file.write(anki_deck_heading.create_string(depth=initial_heading_depth))

            current_deck_heading_stack = heading_names

            for anki_deck_note in anki_deck_notes:
                file.write("\n")
                file.write(
                    anki_deck_note.create_string(
                        depth=initial_heading_depth + len(heading_names)
                    )
                )
    if debug:
        print(
            f"Write anki decks {', '.join([a.name + ' (' + str(len(a.notes)) + ')' for a in anki_decks])} to "
            f"'{output_file_path}' [.md]"
        )


def backup_anki_decks_to_dir(
    anki_decks_list: List[List[AnkiDeck]],
    output_dir_path: str,
    initial_heading_depth: int = 1,
    debug=False,
):
    if not os.path.isdir(output_dir_path):
        os.mkdir(output_dir_path)
    asset_dir_path = os.path.join(output_dir_path, "assets")
    local_asset_dir_path = os.path.relpath(asset_dir_path, output_dir_path)
    local_assets: List[str] = []

    # Backup each anki deck
    for index, anki_decks in enumerate(anki_decks_list):
        if len(anki_decks_list) > 1:
            document_name = f"document_part_{index + 1:02}.md"
        else:
            document_name = "document.md"
        md_merge_anki_decks_to_file(
            anki_decks,
            output_file_path=os.path.join(output_dir_path, document_name),
            initial_heading_depth=initial_heading_depth,
            local_asset_dir_path=local_asset_dir_path,
            debug=debug,
        )
        for anki_deck in anki_decks:
            local_assets.extend(anki_deck.get_local_files_from_notes(debug=debug))

    if len(local_assets) > 0:
        if not os.path.isdir(asset_dir_path):
            os.mkdir(asset_dir_path)
        for local_asset in local_assets:
            shutil.copyfile(
                local_asset, os.path.join(asset_dir_path, os.path.basename(local_asset))
            )
    bash_build = os.path.join(output_dir_path, "build.sh")
    pwsh_build = os.path.join(output_dir_path, "build.ps1")
    with open(bash_build, "w", encoding="utf-8") as bash_file, open(
        pwsh_build, "w", encoding="utf-8"
    ) as pwsh_file:
        document_name = "document"
        anki_deck_name = "anki_deck"
        info_string = f"Automatically created using {md2anki_name} {md2anki_version}"
        # Shebang and version
        bash_file.write(f"#!/usr/bin/env bash\n\n# {info_string}\n\n")
        pwsh_file.write(f"#!/usr/bin/env pwsh\n\n# {info_string}\n\n")
        # Git clone
        bash_file.write(
            f'Md2AnkiGitDir="{md2anki_name}"\n'
            'if [ ! -d "$Md2AnkiGitDir" ] ; then\n'
            f'    git clone "{md2anki_url_git}" {md2anki_name}\n'
            "fi\n\n"
        )
        pwsh_file.write(
            f'$Md2AnkiGitDir = Join-Path $PSScriptRoot -ChildPath "{md2anki_name}"\n'
            "if (-not (Test-Path -LiteralPath $Md2AnkiGitDir)) {\n"
            f'    git clone "{md2anki_url_git} {md2anki_name}"\n'
            "}\n\n"
        )
        # Run command
        bash_file.write(f"./$Md2AnkiGitDir/run.sh")
        pwsh_file.write(
            "$Md2AnkiRun = Join-Path $Md2AnkiGitDir -ChildPath run.ps1\n"
            'Invoke-Expression "$Md2AnkiRun'
        )
        # > Document list
        if len(anki_decks_list) > 1:
            for index in range(1, len(anki_decks_list) + 1):
                bash_file.write(f' "{document_name}_part_{index:02}.md"')
                pwsh_file.write(f' `"{document_name}_part_{index:02}.md`"')
        else:
            bash_file.write(f' "{document_name}.md"')
            pwsh_file.write(f' `"{document_name}.md`"')
        # > File directories
        bash_file.write(' -file-dir "."')
        pwsh_file.write(' -file-dir `".`"')
        # > Anki deck output
        bash_file.write(f' -o-anki "{anki_deck_name}.apkg" "$@"\n')
        pwsh_file.write(f' -o-anki `"{anki_deck_name}.apkg`" $args"\n')

    if debug:
        print(f"Write anki deck backup to '{output_dir_path}'")
