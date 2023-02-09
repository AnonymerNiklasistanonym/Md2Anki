#!/usr/bin/env python3

# Internal packages
import shutil
import tempfile
from pathlib import Path
from typing import Final, List

# Local modules
from md2anki.anki_deck import (
    AnkiDeck,
    genanki_package_anki_decks_to_file,
    md_merge_anki_decks_to_md_file,
    backup_anki_decks_to_dir,
)
from md2anki.cli import Md2AnkiArgs, AnkiCardModelId
from md2anki.info import md2anki_name
from md2anki.md_parser import parse_md_content_to_anki_deck_list
from md2anki.md_to_pdf import create_pdf_from_md_content
from md2anki.note_models import (
    create_default_anki_deck_model,
    create_type_answer_anki_deck_model,
)
from md2anki.print import debug_print


def main(args: Md2AnkiArgs) -> int:
    if args.debug:
        print(f"> Args: {args}")

    if args.error is not None:
        print(f"Error: {args.error}")
        return 1

    if args.anki_card_model == AnkiCardModelId.DEFAULT:
        anki_deck_model = create_default_anki_deck_model()
    elif args.anki_card_model == AnkiCardModelId.TYPE_ANSWER:
        anki_deck_model = create_type_answer_anki_deck_model()
    else:
        raise RuntimeError(f"Unknown anki card model ID '{args.anki_card_model}'")

    anki_decks: Final[List[List[AnkiDeck]]] = []
    for md_input_file_path in args.md_input_file_paths:
        with open(md_input_file_path, "r", encoding="utf-8") as md_file:
            debug_print(
                f"> Parse {md_input_file_path!r} to anki deck list", debug=args.debug
            )
            anki_deck_list = parse_md_content_to_anki_deck_list(
                md_file, initial_heading_depth=args.md_heading_depth, debug=args.debug
            )
            for anki_deck in anki_deck_list:
                anki_deck.additional_file_dirs = args.additional_file_dirs
                anki_deck.model = anki_deck_model
            anki_decks.append(anki_deck_list)

    anki_decks_flat: Final[List[AnkiDeck]] = [
        item for sublist in anki_decks for item in sublist
    ]

    if args.anki_output_file_path is not None:
        tmp_dir_dynamic_files_anki = Path(
            tempfile.mkdtemp(
                prefix=f"{md2anki_name}_tmp_dir_dynamic_files_anki_output_"
            )
        )
        try:
            genanki_package_anki_decks_to_file(
                [
                    anki_deck.genanki_create_anki_deck(
                        dir_dynamic_files=tmp_dir_dynamic_files_anki,
                        custom_program=args.custom_program,
                        custom_program_args=args.custom_program_args,
                        debug=args.debug,
                    )
                    for anki_deck in anki_decks_flat
                ],
                args.anki_output_file_path,
                debug=args.debug,
            )
        finally:
            if not args.debug:
                shutil.rmtree(tmp_dir_dynamic_files_anki)

    if args.md_output_file_paths is not None:
        # Don't update local file paths when merging or updating files
        if len(args.md_output_file_paths) == 1:
            md_merge_anki_decks_to_md_file(
                anki_decks_flat,
                args.md_output_file_paths[0],
                initial_heading_depth=args.md_heading_depth,
                debug=args.debug,
            )
        elif len(args.md_output_file_paths) > 1:
            for output_file_path, anki_deck_list in zip(
                args.md_output_file_paths, anki_decks, strict=True
            ):
                md_merge_anki_decks_to_md_file(
                    anki_deck_list,
                    output_file_path,
                    initial_heading_depth=args.md_heading_depth,
                    debug=args.debug,
                )
    if args.md_output_dir_path is not None:
        if not args.md_output_dir_path.exists():
            args.md_output_dir_path.mkdir()
        for anki_deck_list, md_input_file_path in zip(
            anki_decks, args.md_input_file_paths
        ):
            md_merge_anki_decks_to_md_file(
                anki_deck_list,
                args.md_output_dir_path.joinpath(f"{md_input_file_path.stem}.apkg"),
                initial_heading_depth=args.md_heading_depth,
                debug=args.debug,
            )

    if args.backup_output_dir_path is not None:
        backup_anki_decks_to_dir(
            anki_decks,
            args.backup_output_dir_path,
            initial_heading_depth=args.md_heading_depth,
            debug=args.debug,
        )

    if args.pdf_output_file_path is not None:
        tmp_dir_dynamic_files_pdf: Final = Path(
            tempfile.mkdtemp(prefix=f"{md2anki_name}_tmp_dir_dynamic_files_pdf_output_")
        )
        tmp_file_path_md_merge: Final = Path(
            tempfile.mktemp(prefix=f"{md2anki_name}_tmp_file_md_merge_pdf_output_")
        )
        try:
            md_merge_anki_decks_to_md_file(
                anki_decks_flat,
                tmp_file_path_md_merge,
                remove_ids=True,
                debug=args.debug,
            )
            local_assets: List[Path] = []
            for anki_deck in anki_decks_flat:
                local_assets.extend(
                    anki_deck.get_local_files_from_notes(debug=args.debug)
                )
            with open(tmp_file_path_md_merge, "r") as reader:
                create_pdf_from_md_content(
                    reader.read(),
                    args.pdf_output_file_path,
                    local_assets,
                    dir_dynamic_files=tmp_dir_dynamic_files_pdf,
                    custom_program=args.custom_program,
                    custom_program_args=args.custom_program_args,
                    debug=args.debug,
                )
        finally:
            if not args.debug:
                tmp_file_path_md_merge.unlink()
                shutil.rmtree(tmp_dir_dynamic_files_pdf)

    return 0
