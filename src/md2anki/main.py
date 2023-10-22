#!/usr/bin/env python3

# Internal packages
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Final, List, Tuple

# Local modules
from md2anki.anki_deck import (
    AnkiDeck,
    AnkiNote,
    genanki_package_anki_decks_to_file,
    md_merge_anki_decks_to_md_file,
    backup_anki_decks_to_dir,
)
from md2anki.cli import Md2AnkiArgs, AnkiCardModelId
from md2anki.info.general import MD2ANKI_NAME
from md2anki.md_parser import parse_md_content_to_anki_deck_list
from md2anki.md_to_pdf import create_pdf_from_md_content
from md2anki.note_models import (
    create_default_anki_deck_model,
    create_type_answer_anki_deck_model,
    create_type_cloze_anki_deck_model,
)

log = logging.getLogger(__name__)


def main(args: Md2AnkiArgs) -> int:
    log.debug(f"{args=}")

    # Check if there were any critical errors when parsing the CLI args
    if args.error is not None:
        log.error(args.error)
        return 1

    # Other routines
    if (
        args.evaluate_code_delete_cache
        and args.evaluate_code_cache_dir_path is not None
    ):
        log.debug(
            f"Delete evaluate code cache dir {args.evaluate_code_cache_dir_path!r}"
        )
        if args.evaluate_code_cache_dir_path.is_dir():
            shutil.rmtree(args.evaluate_code_cache_dir_path)
    if args.evaluate_code_cache_dir_path is not None and args.evaluate_code:
        args.evaluate_code_cache_dir_path.mkdir(parents=True, exist_ok=True)

    # Stop parsing if no outputs are specified
    if (
        args.anki_output_file_path is None
        and args.md_output_file_paths is None
        and args.md_output_dir_path is None
        and args.pdf_output_file_path is None
        and args.backup_output_dir_path is None
    ):
        log.warning("Stop parsing because no outputs are specified!")
        return 0

    # Parse all Markdown input files to Anki decks
    anki_decks: Final[List[List[AnkiDeck]]] = []
    for md_input_file_path in args.md_input_file_paths:
        log.debug(f"Parse {md_input_file_path!r} to anki deck list...")
        with open(md_input_file_path, "r", encoding="utf-8") as md_file:
            anki_deck_list = parse_md_content_to_anki_deck_list(
                md_file,
                [md_input_file_path.parent],
                initial_heading_depth=args.md_heading_depth,
            )
            for anki_deck in anki_deck_list:
                anki_deck.additional_file_dirs.extend(args.additional_file_dirs)
            anki_decks.append(anki_deck_list)

    anki_decks_flat: Final[List[AnkiDeck]] = [
        item for sublist in anki_decks for item in sublist
    ]

    guids: Dict[str, Tuple[AnkiDeck, AnkiNote]] = dict()
    guids_deck: Dict[int, AnkiDeck] = dict()
    for anki_deck in anki_decks_flat:
        if (
            anki_deck.guid in guids_deck
            and guids_deck[anki_deck.guid].name != anki_deck.name
        ):
            log.warning(
                f"Found a duplicated deck guid with different name ({anki_deck.guid}): "
                f"{guids_deck[anki_deck.guid].name!r} <-> {anki_deck.name!r}"
            )
        guids_deck[anki_deck.guid] = anki_deck
        for anki_deck_note in anki_deck.notes:
            if anki_deck_note.guid in guids:
                log.warning(
                    f"Found a duplicated note guid ({anki_deck_note.guid}): "
                    f"{guids[anki_deck_note.guid][0].name!r}>{guids[anki_deck_note.guid][1].question!r} <-> "
                    f"{anki_deck.name!r}>{anki_deck_note.question!r}"
                )
            guids[anki_deck_note.guid] = (anki_deck, anki_deck_note)

    if args.anki_output_file_path is not None:
        log.debug(f"Create anki deck file {args.anki_output_file_path!r}...")
        tmp_dir_dynamic_files_anki = Path(
            tempfile.mkdtemp(
                prefix=f"{MD2ANKI_NAME}_tmp_dir_dynamic_files_anki_output_"
            )
        )
        try:
            genanki_package_anki_decks_to_file(
                [
                    anki_deck.genanki_create_anki_deck(
                        default_anki_card_model=f"{args.anki_card_model}",
                        dir_dynamic_files=tmp_dir_dynamic_files_anki,
                        custom_program=args.custom_program,
                        custom_program_args=args.custom_program_args,
                        evaluate_code=args.evaluate_code,
                        evaluate_code_cache_dir=None
                        if args.evaluate_code_ignore_cache
                        else args.evaluate_code_cache_dir_path,
                        external_file_dirs=args.additional_file_dirs,
                        keep_temp_files=args.keep_temp_files,
                    )
                    for anki_deck in anki_decks_flat
                ],
                args.anki_output_file_path,
            )
        except Exception as err:
            log.error(err)
            raise err
        finally:
            if not args.keep_temp_files:
                shutil.rmtree(tmp_dir_dynamic_files_anki)

    if args.md_output_file_paths is not None:
        log.debug(f"Create markdown file {args.md_output_file_paths!r}...")
        # Don't update local file paths when merging or updating files
        if len(args.md_output_file_paths) == 1:
            md_merge_anki_decks_to_md_file(
                anki_decks_flat,
                args.md_output_file_paths[0],
                initial_heading_depth=args.md_heading_depth,
            )
        elif len(args.md_output_file_paths) > 1:
            if len(args.md_output_file_paths) != len(anki_decks):
                raise RuntimeError(
                    f"Output file path ({len(args.md_output_file_paths)}) and anki deck list ({len(anki_decks)}) had different sizes"
                )
            for output_file_path, anki_deck_list in zip(
                args.md_output_file_paths, anki_decks
            ):
                md_merge_anki_decks_to_md_file(
                    anki_deck_list,
                    output_file_path,
                    initial_heading_depth=args.md_heading_depth,
                )

    if args.md_output_dir_path is not None:
        log.debug(f"Create markdown files in {args.md_output_dir_path!r}...")
        if not args.md_output_dir_path.exists():
            args.md_output_dir_path.mkdir()
        for anki_deck_list, md_input_file_path in zip(
            anki_decks, args.md_input_file_paths
        ):
            md_merge_anki_decks_to_md_file(
                anki_deck_list,
                args.md_output_dir_path.joinpath(f"{md_input_file_path.stem}.apkg"),
                initial_heading_depth=args.md_heading_depth,
            )

    if args.backup_output_dir_path is not None:
        log.debug(f"Create backup in {args.backup_output_dir_path!r}...")
        backup_anki_decks_to_dir(
            anki_decks,
            args.backup_output_dir_path,
            initial_heading_depth=args.md_heading_depth,
        )

    if args.pdf_output_file_path is not None:
        log.debug(f"Create pdf in {args.backup_output_dir_path!r}...")
        tmp_dir_dynamic_files_pdf: Final = Path(
            tempfile.mkdtemp(prefix=f"{MD2ANKI_NAME}_tmp_dir_dynamic_files_pdf_output_")
        )
        tmp_file_path_md_merge: Final = Path(
            tempfile.mktemp(prefix=f"{MD2ANKI_NAME}_tmp_file_md_merge_pdf_output_")
        )
        try:
            md_merge_anki_decks_to_md_file(
                anki_decks_flat,
                tmp_file_path_md_merge,
                local_asset_dir_path=Path("."),
                remove_ids=True,
            )
            local_assets: List[Path] = []
            for anki_deck in anki_decks_flat:
                local_assets.extend(anki_deck.get_local_files_from_notes())
            with open(tmp_file_path_md_merge, "r") as reader:
                create_pdf_from_md_content(
                    reader.read(),
                    args.pdf_output_file_path,
                    local_assets,
                    custom_program=args.custom_program,
                    custom_program_args=args.custom_program_args,
                    dir_dynamic_files=tmp_dir_dynamic_files_pdf,
                    evaluate_code=args.evaluate_code,
                    evaluate_code_cache_dir=None
                    if args.evaluate_code_ignore_cache
                    else args.evaluate_code_cache_dir_path,
                    external_file_dirs=args.additional_file_dirs,
                    keep_temp_files=args.keep_temp_files,
                )
        except Exception as err:
            log.error(err)
            raise err
        finally:
            if not args.keep_temp_files:
                tmp_file_path_md_merge.unlink()
                shutil.rmtree(tmp_dir_dynamic_files_pdf)

    return 0
