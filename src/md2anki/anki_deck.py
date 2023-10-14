#!/usr/bin/env python3

# Internal packages
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Optional, List, Tuple, Dict, Final

# Installed packages
import genanki

# Local modules
from md2anki.anki_model import AnkiModel
from md2anki.anki_note import AnkiNote, MdSection
from md2anki.create_id import create_unique_id_int
from md2anki.info.anki import ANKI_SUBDECK_SEPARATOR, ANKI_SUPPORTED_FILE_FORMATS
from md2anki.info.general import (
    MD2ANKI_URL_GIT,
    MD2ANKI_NAME,
    MD2ANKI_VERSION,
    MD2ANKI_MD_PP_ANKI_DECK_HEADING_SUBDECK_PREFIX,
)
from md2anki.md_util import md_get_used_md2anki_tags

# Logger
log = logging.getLogger(__name__)


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
    additional_file_dirs: List[Path] = field(default_factory=lambda: list())
    """List of additional file dirs that should be searched for missing files used in notes"""
    tags: Set[str] = field(default_factory=lambda: set())
    """List of anki tags"""
    md_document_order: int = -1
    """The order of the anki deck in the read md document"""

    def genanki_create_deck(
        self,
        anki_card_model: genanki.Model,
        dir_dynamic_files: Path,
        custom_program: Dict[str, List[str]],
        custom_program_args: Dict[str, List[List[str]]],
        external_file_dirs: List[Path],
        evaluate_code: bool = False,
        evaluate_code_cache_dir: Optional[Path] = None,
        keep_temp_files: bool = False,
    ) -> genanki.Deck:
        tmp_anki_deck = genanki.Deck(self.guid, self.name)
        for note in self.notes:
            tmp_anki_deck.add_note(
                note.genanki_create_note(
                    anki_card_model=anki_card_model,
                    dir_dynamic_files=dir_dynamic_files,
                    custom_program=custom_program,
                    custom_program_args=custom_program_args,
                    evaluate_code=evaluate_code,
                    evaluate_code_cache_dir=evaluate_code_cache_dir,
                    external_file_dirs=external_file_dirs,
                    keep_temp_files=keep_temp_files,
                    merge_fields=len(self.model.fields) == 1,
                )
            )
        return tmp_anki_deck

    def get_used_global_tags(self) -> Set[str]:
        """Get the used global tags of the anki deck"""
        return self.tags.union(md_get_used_md2anki_tags(self.description))

    def get_local_files_from_notes(self) -> List[Path]:
        files: Set[Path] = set()
        for note in self.notes:
            files.update(note.get_used_local_files())
        file_list: List[Path] = list()
        for file in files:
            # Check if every file can be found
            if file.is_file():
                file_list.append(file)
            else:
                file_found = False
                # Check if file is located in one of the additional file dirs
                for additional_file_dir in self.additional_file_dirs:
                    file_path = additional_file_dir.joinpath(file)
                    log.debug(
                        f"{file=} not found check in {additional_file_dir=}: {file_path=}"
                    )
                    if file_path.is_file():
                        file_list.append(file_path)
                        file_found = True
                        break
                if not file_found:
                    raise Exception(f"{file=} not found ({self.additional_file_dirs=})")
        return file_list

    def genanki_create_anki_deck(
        self,
        dir_dynamic_files: Path,
        custom_program: Dict[str, List[str]],
        custom_program_args: Dict[str, List[List[str]]],
        external_file_dirs: List[Path],
        evaluate_code: bool = False,
        evaluate_code_cache_dir: Optional[Path] = None,
        keep_temp_files: bool = False,
    ) -> Tuple[genanki.Deck, List[Path]]:
        """Return anki deck and a list of all media files."""
        genanki_anki_deck = self.genanki_create_deck(
            self.model.genanki_create_model(),
            dir_dynamic_files=dir_dynamic_files,
            custom_program=custom_program,
            custom_program_args=custom_program_args,
            evaluate_code=evaluate_code,
            evaluate_code_cache_dir=evaluate_code_cache_dir,
            external_file_dirs=external_file_dirs,
            keep_temp_files=keep_temp_files,
        )
        media_files = self.get_local_files_from_notes()
        # Add all supported dynamic media files
        for supported_file_format in ANKI_SUPPORTED_FILE_FORMATS:
            media_files.extend(dir_dynamic_files.rglob(f"*{supported_file_format}"))
        return genanki_anki_deck, media_files

    def create_md_sections(
        self, local_asset_dir_path: Optional[Path] = None
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
    anki_decks: List[Tuple[genanki.Deck, List[Path]]], output_file_path: Path
):
    anki_deck_package = genanki.Package([a[0] for a in anki_decks])
    media_files = [a[1] for a in anki_decks]
    anki_deck_package.media_files = [
        item for sublist in media_files for item in sublist
    ]
    anki_deck_package.write_to_file(output_file_path)
    log.debug(
        f"Write anki decks {', '.join([a[0].name + ' (' + str(len(a[0].notes)) + ')' for a in anki_decks])} to "
        f"'{output_file_path}' [.apkg]"
    )


def md_merge_anki_decks_to_md_file(
    anki_decks: List[AnkiDeck],
    output_file_path: Path,
    local_asset_dir_path: Optional[Path] = None,
    initial_heading_depth: int = 1,
    remove_ids=False,
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
                        heading_prefix=MD2ANKI_MD_PP_ANKI_DECK_HEADING_SUBDECK_PREFIX
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
    log.debug(
        f"Write anki decks {', '.join([a.name + ' (' + str(len(a.notes)) + ')' for a in anki_decks])} to "
        f"'{output_file_path}' [.md]"
    )


def backup_anki_decks_to_dir(
    anki_decks_list: List[List[AnkiDeck]],
    output_dir_path: Path,
    initial_heading_depth: int = 1,
):
    if not output_dir_path.exists():
        output_dir_path.mkdir()
    asset_dir_path_relative = Path("assets")
    asset_dir_path = output_dir_path.joinpath(asset_dir_path_relative)
    local_assets: List[Path] = []

    # Backup each anki deck
    for index, anki_decks in enumerate(anki_decks_list):
        document_name = (
            f"document_part_{index + 1:02}.md"
            if len(anki_decks_list) > 1
            else "document.md"
        )
        md_merge_anki_decks_to_md_file(
            anki_decks,
            output_file_path=output_dir_path.joinpath(document_name),
            initial_heading_depth=initial_heading_depth,
            local_asset_dir_path=asset_dir_path_relative,
        )
        for anki_deck in anki_decks:
            local_assets.extend(anki_deck.get_local_files_from_notes())

    if len(local_assets) > 0:
        if not asset_dir_path.exists():
            asset_dir_path.mkdir()
        for local_asset in local_assets:
            shutil.copyfile(local_asset, asset_dir_path.joinpath(local_asset.name))
    bash_build: Final = output_dir_path.joinpath("build.sh")
    pwsh_build: Final = output_dir_path.joinpath("build.ps1")
    with open(bash_build, "w", encoding="utf-8") as bash_file, open(
        pwsh_build, "w", encoding="utf-8"
    ) as pwsh_file:
        document_name = "document"
        anki_deck_name = "anki_deck"
        info_string = f"Automatically created using {MD2ANKI_NAME} {MD2ANKI_VERSION}"
        # Shebang and version
        bash_file.write(f"#!/usr/bin/env bash\n\n# {info_string}\n\n")
        pwsh_file.write(f"#!/usr/bin/env pwsh\n\n# {info_string}\n\n")
        # Git clone
        bash_file.write(
            f'Md2AnkiGitDir="{MD2ANKI_NAME}"\n'
            'if [ ! -d "$Md2AnkiGitDir" ] ; then\n'
            f'    git clone "{MD2ANKI_URL_GIT}" {MD2ANKI_NAME}\n'
            "fi\n\n"
        )
        pwsh_file.write(
            f'$Md2AnkiGitDir = Join-Path $PSScriptRoot -ChildPath "{MD2ANKI_NAME}"\n'
            "if (-not (Test-Path -LiteralPath $Md2AnkiGitDir)) {\n"
            f'    git clone "{MD2ANKI_URL_GIT} {MD2ANKI_NAME}"\n'
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

    log.debug(f"Write anki deck backup to '{output_dir_path}'")
