import glob
import os
import shutil
from dataclasses import dataclass, field
from typing import Set, Optional, List, Tuple

import genanki

from md2anki.anki_model import AnkiModel
from md2anki.anki_note import AnkiNote, MdSection
from md2anki.create_id import create_unique_id_int
from md2anki.info import (
    ANKI_SUBDECK_SEPARATOR,
    md2anki_url_git,
    md2anki_name,
    md2anki_version,
    MD_ANKI_DECK_HEADING_SUBDECK_PREFIX,
)
from md2anki.md_util import md_get_used_md2anki_tags


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
    tags: Set[str] = field(default_factory=lambda: set())
    """List of anki tags"""
    md_document_order: int = -1
    """The order of the anki deck in the read md document"""

    def genanki_create_deck(
        self,
        anki_card_model: genanki.Model,
        dir_dynamic_files: str,
        debug=False,
    ) -> genanki.Deck:
        tmp_anki_deck = genanki.Deck(self.guid, self.name)
        for note in self.notes:
            tmp_anki_deck.add_note(
                note.genanki_create_note(
                    anki_card_model=anki_card_model,
                    dir_dynamic_files=dir_dynamic_files,
                    debug=debug,
                )
            )
        return tmp_anki_deck

    def get_used_global_tags(self) -> Set[str]:
        """Get the used global tags of the anki deck"""
        return self.tags.union(md_get_used_md2anki_tags(self.description))

    def get_local_files_from_notes(self, debug=False) -> List[str]:
        files: Set[str] = set()
        for note in self.notes:
            files.update(note.get_used_local_files())
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

    def genanki_create_anki_deck(
        self, dir_dynamic_files: str, debug=False
    ) -> Tuple[genanki.Deck, List[str]]:
        genanki_anki_deck = self.genanki_create_deck(
            self.model.genanki_create_model(),
            dir_dynamic_files=dir_dynamic_files,
            debug=debug,
        )
        media_files = self.get_local_files_from_notes(debug=debug)
        media_files.extend(glob.glob(os.path.join(dir_dynamic_files, "*")))
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
            MdSection(self.name, str(self.guid), self.description),
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


def md_merge_anki_decks_to_md_file(
    anki_decks: List[AnkiDeck],
    output_file_path: str,
    local_asset_dir_path: Optional[str] = None,
    initial_heading_depth: int = 1,
    remove_ids=False,
    debug=False,
):
    """Merge anki decks to a single markdown output file"""
    heading_stack: List[Tuple[str, str]] = []
    """Store what headings were currently written"""
    first_heading = True
    with open(output_file_path, "w", encoding="utf-8") as file:
        for anki_deck in anki_decks:
            # Create a markdown section for the notes and the heading
            anki_deck_heading, anki_deck_notes = anki_deck.create_md_sections(
                local_asset_dir_path=local_asset_dir_path
            )
            # Determine the heading depth
            heading_names = anki_deck_heading.heading.split(ANKI_SUBDECK_SEPARATOR)
            heading_depth = len(heading_names)
            # Check if heading was already written
            heading_same_as_previous_heading = [
                a[0] for a in heading_stack
            ] == heading_names
            heading_parent_deck_of_previous_heading = (
                len(heading_names) < len(heading_stack)
                and [a[0] for a in heading_stack[: len(heading_names)]] == heading_names
            )
            heading_description_same = (
                len(heading_stack) >= len(heading_names)
                and heading_stack[len(heading_names) - 1][1]
                == anki_deck_heading.content
            )
            if not (
                (heading_same_as_previous_heading and heading_description_same)
                or (
                    heading_parent_deck_of_previous_heading and heading_description_same
                )
            ):
                # Fix heading name
                if heading_depth > 1:
                    anki_deck_heading.heading = heading_names[-1]
                # Write notes and heading to file
                if not first_heading:
                    file.write("\n")
                first_heading = False
                file.write(
                    anki_deck_heading.create_string(
                        depth=heading_depth + initial_heading_depth - 1,
                        heading_prefix=MD_ANKI_DECK_HEADING_SUBDECK_PREFIX
                        if heading_depth > 1
                        else "",
                        with_heading_id=not remove_ids,
                    )
                )
                new_heading_stack = []
                for index, heading_name in enumerate(heading_names):
                    heading_content = ""
                    if index == len(heading_names) - 1:
                        heading_content = anki_deck_heading.content
                    elif (
                        len(heading_stack) >= index - 1
                        and heading_name == heading_stack[index][0]
                    ):
                        heading_content = heading_stack[index][1]
                    new_heading_stack.append((heading_name, heading_content))
                heading_stack = new_heading_stack
            for index, anki_deck_note in enumerate(anki_deck_notes):
                file.write("\n")
                file.write(
                    anki_deck_note.create_string(
                        depth=heading_depth + initial_heading_depth,
                        with_heading_id=not remove_ids,
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
        md_merge_anki_decks_to_md_file(
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
