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
    input_files: List[Path],
    o_anki: Optional[Path] = None,
    o_md: Optional[Path] = None,
    o_md_dir: Optional[Path] = None,
    o_pdf: Optional[Path] = None,
    file_dirs: Optional[List[Path]] = None,
    o_backup_dir: Optional[Path] = None,
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
):
    args: List[str] = [str(input_file) for input_file in input_files]
    if debug is True:
        args.append("-d")
    if o_anki is not None:
        args.extend(["-o-anki", str(o_anki)])
    if o_md is not None:
        args.extend(["-o-md", str(o_md)])
    if o_md_dir is not None:
        args.extend(["-o-md-dir", str(o_md_dir)])
    if o_pdf is not None:
        args.extend(["-o-pdf", str(o_pdf)])
    if file_dirs is not None:
        args.extend(["-file-dir", *[str(file_dir) for file_dir in file_dirs]])
    if anki_model is not None:
        args.extend(["-anki-model", anki_model.value])
    if o_backup_dir is not None:
        args.extend(["-o-backup-dir", str(o_backup_dir)])
    print(f"{md2anki_name} {' '.join(args)}")
    cli_args = parse_cli_args(args)
    assert main(cli_args) == 0


def run_example_glob(
    dir_path: Path,
    glob_str: str,
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
):
    for glob_file in dir_path.glob(glob_str):
        run_example(
            [glob_file],
            o_anki=glob_file.parent.joinpath(f"{glob_file.stem}.apkg"),
            o_md=glob_file.parent.joinpath(f"{glob_file.stem}.md"),
            o_md_dir=glob_file.parent,
            anki_model=anki_model,
            file_dirs=[glob_file.parent],
            o_backup_dir=glob_file.parent.joinpath(f"backup_{glob_file.stem}"),
            debug=debug,
        )


EXAMPLE_DIR = Path(__file__).parent.resolve()

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
            list(EXAMPLE_DIR.glob("multi_page_example_part_*.md")),
            o_anki=EXAMPLE_DIR.joinpath("multi_page_example.apkg"),
            o_md=EXAMPLE_DIR.joinpath("multi_page_all_parts_example.md"),
            o_md_dir=EXAMPLE_DIR,
            file_dirs=[EXAMPLE_DIR],
            o_backup_dir=EXAMPLE_DIR.joinpath("backup_multi_page_example"),
            debug=debug_examples,
        )
        run_example(
            list(EXAMPLE_DIR.glob("subdeck_multi_page_example_part_*.md")),
            o_anki=EXAMPLE_DIR.joinpath("subdeck_multi_page_example.apkg"),
            o_md=EXAMPLE_DIR.joinpath("subdeck_multi_page_all_parts_example.md"),
            o_md_dir=EXAMPLE_DIR,
            file_dirs=[EXAMPLE_DIR],
            o_backup_dir=EXAMPLE_DIR.joinpath("backup_subdeck_multi_page_example"),
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
        for backup_dir in EXAMPLE_DIR.glob("backup_*"):
            run_example(
                list(backup_dir.glob("*.md")),
                o_anki=backup_dir.joinpath(f"{backup_dir.stem}.apkg"),
                o_md=backup_dir.joinpath("document.md"),
                o_md_dir=backup_dir,
                file_dirs=[backup_dir],
                debug=debug_examples,
            )

    if pdf_examples:
        # Create PDFs
        for pdf_example in ["basic", "code", "code_run", "images"]:
            run_example(
                [EXAMPLE_DIR.joinpath(f"{pdf_example}_example.md")],
                o_pdf=EXAMPLE_DIR.joinpath(f"{pdf_example}_example.pdf"),
                debug=debug_examples,
            )
