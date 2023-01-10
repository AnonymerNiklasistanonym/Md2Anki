#!/usr/bin/env python3

import glob
import os
import sys
from os.path import dirname, join
from pathlib import Path
from typing import List, Optional

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "..", "src"))

from md2anki.info import md2anki_name
from md2anki.cli import parse_cli_args, AnkiCardModelId
from md2anki.main import main


def run_example(
    input_files: List[str],
    o_anki: Optional[str] = None,
    o_md: Optional[str] = None,
    o_md_dir: Optional[str] = None,
    o_pdf: Optional[str] = None,
    file_dir: Optional[List[str]] = None,
    o_backup_dir: Optional[str] = None,
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
):
    args = input_files
    if debug is True:
        args.append("-d")
    if o_anki is not None:
        args.extend(["-o-anki", o_anki])
    if o_md is not None:
        args.extend(["-o-md", o_md])
    if o_md_dir is not None:
        args.extend(["-o-md-dir", o_md_dir])
    if o_pdf is not None:
        args.extend(["-o-pdf", o_pdf])
    if file_dir is not None:
        args.extend(["-file-dir", *file_dir])
    if anki_model is not None:
        args.extend(["-anki-model", anki_model.value])
    if o_backup_dir is not None:
        args.extend(["-o-backup-dir", o_backup_dir])
    print(f"{md2anki_name} {' '.join(args)}")
    cli_args = parse_cli_args(args)
    assert main(cli_args) == 0


def run_example_glob(
    dir_path: str,
    glob_str: str,
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
):
    os.chdir(dir_path)
    for glob_file in glob.glob(glob_str, recursive=False):
        run_example(
            [glob_file],
            o_anki=f"{Path(glob_file).stem}.apkg",
            o_md=f"{Path(glob_file).stem}.md",
            o_md_dir=".",
            anki_model=anki_model,
            file_dir=["."],
            o_backup_dir=f"backup_{Path(glob_file).stem}",
            debug=debug,
        )


EXAMPLE_DIR = dirname(__file__)

# Main method
if __name__ == "__main__":
    debug_examples = "-d" in sys.argv[1:] or "--debug" in sys.argv[1:]

    # Make it easy to only run a small subset of examples
    multi_part_examples = True
    single_part_examples = True
    pdf_examples = True

    if multi_part_examples:
        # Merge multi part examples
        run_example(
            [
                "multi_page_example_part_01.md",
                "multi_page_example_part_02.md",
                "multi_page_example_part_03.md",
            ],
            o_anki="multi_page_example.apkg",
            o_md="multi_page_all_parts_example.md",
            o_md_dir=".",
            file_dir=["."],
            o_backup_dir="backup_multi_page_example",
            debug=debug_examples,
        )
        run_example(
            [
                "subdeck_multi_page_example_part_01.md",
                "subdeck_multi_page_example_part_02.md",
            ],
            o_anki="subdeck_multi_page_example.apkg",
            o_md="subdeck_multi_page_all_parts_example.md",
            o_md_dir=".",
            file_dir=["."],
            o_backup_dir="backup_subdeck_multi_page_example",
            debug=debug_examples,
        )

    if single_part_examples:
        # Run all examples
        run_example_glob(EXAMPLE_DIR, "*_example.md", debug=debug_examples)
        run_example_glob(
            EXAMPLE_DIR,
            "*_example_type_answer.md",
            anki_model=AnkiCardModelId.TYPE_ANSWER,
            debug=debug_examples,
        )

        # Rerun all created backups
        os.chdir(EXAMPLE_DIR)
        for backup_dir in glob.glob("backup_*", recursive=False):
            run_example(
                glob.glob(os.path.join(backup_dir, "*.md")),
                o_anki=os.path.join(backup_dir, f"{backup_dir}.apkg"),
                o_md=os.path.join(backup_dir, f"document.md"),
                o_md_dir=backup_dir,
                file_dir=[backup_dir],
                debug=debug_examples,
            )

    if pdf_examples:
        # Create PDFs
        for pdf_example in ["basic", "code", "code_run", "images"]:
            run_example(
                [f"{pdf_example}_example.md"],
                o_pdf=os.path.join(EXAMPLE_DIR, f"{pdf_example}_example.pdf"),
                debug=debug_examples,
            )
