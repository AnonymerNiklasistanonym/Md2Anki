#!/usr/bin/env python3

# Internal packages
import os.path
from typing import List

# Local modules
from md2anki.cli import Md2AnkiArgs, AnkiCardModelId
from md2anki.anki_deck import (
    AnkiDeck,
    genanki_package_anki_decks_to_file,
    md_merge_anki_decks_to_file,
    backup_anki_decks_to_dir,
)
from md2anki.md_parser import parse_md_file_to_anki_deck_list
from md2anki.note_models import (
    create_katex_highlightjs_anki_deck_model,
    create_type_answer_anki_deck_model,
)


def main(args: Md2AnkiArgs) -> int:
    if args.debug:
        print(f"> Args: {args}")

    if args.error is not None:
        print(f"Error: {args.error}")
        return 1

    if args.anki_card_model == AnkiCardModelId.ONLINE:
        anki_deck_model = create_katex_highlightjs_anki_deck_model(
            online=True, debug=args.debug
        )
    elif args.anki_card_model == AnkiCardModelId.OFFLINE:
        anki_deck_model = create_katex_highlightjs_anki_deck_model(
            online=False, debug=args.debug
        )
    elif args.anki_card_model == AnkiCardModelId.TYPE_ANSWER:
        anki_deck_model = create_type_answer_anki_deck_model()
    else:
        raise RuntimeError(f"Unknown anki card model ID '{args.anki_card_model}'")

    anki_decks: List[List[AnkiDeck]] = []
    for md_input_file_path in args.md_input_file_paths:
        with open(md_input_file_path, "r", encoding="utf-8") as md_file:
            if args.debug:
                print(f"> Parse '{md_input_file_path!r}' to anki deck list")
            anki_deck_list = parse_md_file_to_anki_deck_list(
                md_file, initial_heading_depth=args.md_heading_depth, debug=args.debug
            )
            for anki_deck in anki_deck_list:
                anki_deck.additional_file_dirs = args.additional_file_dirs
                anki_deck.model = anki_deck_model
            anki_decks.append(anki_deck_list)

    anki_decks_flat: List[AnkiDeck] = [
        item for sublist in anki_decks for item in sublist
    ]

    if args.anki_output_file_path is not None:
        genanki_package_anki_decks_to_file(
            [
                anki_deck.genanki_create_anki_deck(debug=args.debug)
                for anki_deck in anki_decks_flat
            ],
            args.anki_output_file_path,
            debug=args.debug,
        )

    if args.md_output_file_path is not None:
        md_merge_anki_decks_to_file(
            anki_decks_flat,
            args.md_output_file_path,
            initial_heading_depth=args.md_heading_depth,
            debug=args.debug,
        )

    if args.md_output_dir_path is not None:
        if not os.path.isdir(args.md_output_dir_path):
            os.mkdir(args.md_output_dir_path)
        for anki_deck_list, md_input_file_path in zip(
            anki_decks, args.md_input_file_paths
        ):
            anki_output_file_path = os.path.join(
                args.md_output_dir_path, os.path.basename(md_input_file_path)
            )
            md_merge_anki_decks_to_file(
                anki_deck_list,
                anki_output_file_path,
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
    return 0
