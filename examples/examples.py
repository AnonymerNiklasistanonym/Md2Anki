#!/usr/bin/env python3

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
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
    evaluate_code: Optional[bool] = None,
    file_dirs: Optional[List[Path]] = None,
    keep_temporary_files: Optional[bool] = None,
    log_file: Optional[Path] = None,
    o_anki: Optional[Path] = None,
    o_backup_dir: Optional[Path] = None,
    o_md: Optional[Path] = None,
    o_md_dir: Optional[Path] = None,
    o_pdf: Optional[Path] = None,
):
    args: List[str] = [str(input_file) for input_file in input_files]
    if debug is True:
        args.append("--debug")
    if evaluate_code is True:
        args.append("--evaluate-code")
    if keep_temporary_files is True:
        args.append("--keep-temp-files")
    if log_file is not None:
        args.extend(["-log-file", str(log_file)])
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
    evaluate_code: Optional[bool] = None,
    file_dirs: Optional[List[Path]] = None,
    keep_temporary_files: Optional[bool] = None,
):
    for glob_file in dir_path.glob(glob_str):
        run_example(
            [glob_file],
            anki_model=anki_model,
            debug=debug,
            evaluate_code=evaluate_code,
            file_dirs=file_dirs,
            keep_temporary_files=keep_temporary_files,
            log_file=glob_file.parent.joinpath(f"{glob_file.stem}.log"),
            o_anki=glob_file.parent.joinpath(f"{glob_file.stem}.apkg"),
            o_backup_dir=glob_file.parent.joinpath(f"backup_{glob_file.stem}"),
            o_md=glob_file.parent.joinpath(f"{glob_file.stem}.md"),
            o_md_dir=glob_file.parent,
        )


def run_example_glob_multi_part(
    dir_path: Path,
    multi_part_name: str,
    anki_model: Optional[AnkiCardModelId] = None,
    debug: Optional[bool] = False,
    evaluate_code: Optional[bool] = None,
    file_dirs: Optional[List[Path]] = None,
    keep_temporary_files: Optional[bool] = None,
):
    all_parts = list(dir_path.glob(f"{multi_part_name}_part_*.md"))
    all_parts.sort()
    run_example(
        all_parts,
        anki_model=anki_model,
        debug=debug,
        evaluate_code=evaluate_code,
        file_dirs=file_dirs,
        keep_temporary_files=keep_temporary_files,
        log_file=dir_path.joinpath(f"{multi_part_name}_all_parts.log"),
        o_anki=dir_path.joinpath(f"{multi_part_name}_all_parts.apkg"),
        o_backup_dir=dir_path.joinpath(f"backup_{multi_part_name}"),
        o_md=dir_path.joinpath(f"{multi_part_name}_all_parts.md"),
    )


EXAMPLE_DIR = Path(__file__).parent.resolve()

# Main method
if __name__ == "__main__":
    debug_examples = "-d" in sys.argv[1:] or "--debug" in sys.argv[1:]

    # Make it easy to only run a small subset of examples
    toggle_multi_part_examples = True
    toggle_single_part_examples = True
    toggle_pdf_examples = True
    toggle_evaluate_code = True
    toogle_keep_temporary_files = True

    example_file_dirs: List[Path] = [EXAMPLE_DIR.joinpath("res")]

    run_example(
        [Path("code_run_example.md")],
        debug=debug_examples,
        evaluate_code=toggle_evaluate_code,
        file_dirs=example_file_dirs,
        keep_temporary_files=toogle_keep_temporary_files,
        o_pdf=Path("code_run_example.pdf"),
    )
    exit(0)

    if toggle_multi_part_examples:
        # Merge multi part examples
        run_example_glob_multi_part(
            EXAMPLE_DIR,
            "multi_page_example",
            debug=debug_examples,
            evaluate_code=toggle_evaluate_code,
            file_dirs=example_file_dirs,
            keep_temporary_files=toogle_keep_temporary_files,
        )
        run_example_glob_multi_part(
            EXAMPLE_DIR,
            "subdeck_multi_page_example",
            debug=debug_examples,
            evaluate_code=toggle_evaluate_code,
            file_dirs=example_file_dirs,
            keep_temporary_files=toogle_keep_temporary_files,
        )

    if toggle_single_part_examples:
        # Run all examples
        run_example_glob(
            EXAMPLE_DIR,
            "*_example.md",
            debug=debug_examples,
            evaluate_code=toggle_evaluate_code,
            file_dirs=example_file_dirs,
            keep_temporary_files=toogle_keep_temporary_files,
        )
        run_example_glob(
            EXAMPLE_DIR,
            "*_example_type_answer.md",
            anki_model=AnkiCardModelId.TYPE_ANSWER,
            debug=debug_examples,
            evaluate_code=toggle_evaluate_code,
            file_dirs=example_file_dirs,
            keep_temporary_files=toogle_keep_temporary_files,
        )

        # Rerun all created backups
        for backup_dir in EXAMPLE_DIR.glob("backup_*"):
            run_example(
                list(backup_dir.glob("*.md")),
                anki_model=AnkiCardModelId.TYPE_ANSWER
                if backup_dir.stem.endswith("_type_answer")
                else None,
                debug=debug_examples,
                evaluate_code=toggle_evaluate_code,
                file_dirs=[backup_dir.joinpath("assets")],
                keep_temporary_files=toogle_keep_temporary_files,
                log_file=backup_dir.joinpath(f"{backup_dir.stem}.log"),
                o_anki=backup_dir.joinpath(f"{backup_dir.stem}.apkg"),
                o_md=backup_dir.joinpath("document.md"),
            )

    if toggle_pdf_examples:
        # Create PDFs
        for pdf_example in ["basic", "code", "code_run", "images"]:
            run_example(
                [EXAMPLE_DIR.joinpath(f"{pdf_example}_example.md")],
                debug=debug_examples,
                evaluate_code=toggle_evaluate_code,
                file_dirs=example_file_dirs,
                keep_temporary_files=toogle_keep_temporary_files,
                log_file=EXAMPLE_DIR.joinpath(f"{pdf_example}_example_pdf.log"),
                o_pdf=EXAMPLE_DIR.joinpath(f"{pdf_example}_example.pdf"),
            )
