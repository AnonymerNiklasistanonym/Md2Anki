#!/usr/bin/env python3

import sys
import glob, os
from os.path import dirname, join
from typing import List, Optional
from pathlib import Path

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "..", "src"))

import md2anki
from md2anki.info import md2anki_name


def run_example(
    input_files: List[str],
    o_anki: Optional[str] = None,
    o_md: Optional[str] = None,
    o_md_dir: Optional[str] = None,
    file_dir: Optional[List[str]] = None,
    o_backup_dir: Optional[str] = None,
    anki_model: Optional[str] = None,
    debug: bool = False,
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
    if file_dir is not None:
        args.extend(["-file-dir", *file_dir])
    if anki_model is not None:
        args.extend(["-anki-model", anki_model])
    if o_backup_dir is not None:
        args.extend(["-o-backup-dir", o_backup_dir])
    print(f"{md2anki_name} {' '.join(args)}")
    cli_args = md2anki.parse_cli_args(args)
    assert md2anki.main(cli_args) == 0


def run_example_glob(dir_path: str, glob_str: str, anki_model: Optional[str] = None):
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
        )


# Main method
if __name__ == "__main__":
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
    )

    # Run all examples
    run_example_glob(dirname(__file__), "*_example.md")
    run_example_glob(
        dirname(__file__), "*_example_type_answer.md", anki_model="md2anki_type_answer"
    )
    run_example_glob(
        dirname(__file__), "*_example_offline.md", anki_model="md2anki_offline"
    )

    # Rerun all created backups
    os.chdir(dirname(__file__))
    for backup_dir in glob.glob("backup_*", recursive=False):
        run_example(
            glob.glob(os.path.join(backup_dir, "*.md")),
            o_anki=os.path.join(backup_dir, f"{backup_dir}.apkg"),
            o_md=os.path.join(backup_dir, f"{backup_dir}.md"),
            o_md_dir=backup_dir,
            file_dir=[backup_dir],
        )
