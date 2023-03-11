#!/usr/bin/env python3

# Internal packages
import logging
import shutil
import tempfile
from os import fdopen
from pathlib import Path
from typing import List, Dict, Final, Tuple, Optional

# Local modules
from md2anki.info.general import MD2ANKI_NAME
from md2anki.preprocessor import md_preprocessor_md2anki
from md2anki.subprocess import run_subprocess


PANDOC_ARGS_PDF_KEY_NAME: Final = "pandoc_pdf"
PANDOC_ARGS_PDF: Final[Dict[str, List[Tuple[str, List[str]]]]] = {
    PANDOC_ARGS_PDF_KEY_NAME: [
        (
            "pandoc",
            [
                "--from",
                "markdown",
                "--to",
                "pdf",
                "--table-of-contents",
                "-V",
                "geometry:a4paper",
                "-V",
                "geometry:margin=2cm",
                "--pdf-engine=xelatex",
                "--pdf-engine-opt=-shell-escape",
            ],
        )
    ]
}
"""Pandoc args for pdf export."""

log = logging.getLogger(__name__)


def create_pdf_from_md_content(
    md_content: str,
    output_file_path: Path,
    local_assets: List[Path],
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Path,
    external_file_dirs: List[Path],
    evaluate_code: bool = False,
    evaluate_code_cache_dir: Optional[Path] = None,
    keep_temp_files: bool = False,
):
    md_content = md_preprocessor_md2anki(
        md_content,
        dir_dynamic_files=dir_dynamic_files,
        custom_program=custom_program,
        custom_program_args=custom_program_args,
        evaluate_code=evaluate_code,
        evaluate_code_cache_dir=evaluate_code_cache_dir,
        external_file_dirs=external_file_dirs,
        keep_temp_files=keep_temp_files,
    )

    fd, md_file_path_temp_str = tempfile.mkstemp(
        prefix=f"{MD2ANKI_NAME}_tmp_file_pandoc_md_", suffix=".md"
    )
    md_file_path_temp: Final = Path(md_file_path_temp_str)
    asset_dir_path_temp: Final = Path(
        tempfile.mkdtemp(prefix=f"{MD2ANKI_NAME}_tmp_file_pandoc_md_assets_")
    )
    try:
        log.debug(f"Copy {local_assets=} to {asset_dir_path_temp=}")
        for local_asset in local_assets:
            log.debug(f"> Copy {local_asset=} to {asset_dir_path_temp=}")
            shutil.copy2(local_asset, asset_dir_path_temp)
        log.debug(f"Copy {dir_dynamic_files=} to {asset_dir_path_temp=}")
        for dir_dynamic_file in dir_dynamic_files.rglob("*"):
            log.debug(f"> Copy {dir_dynamic_file=} to {asset_dir_path_temp=}")
            shutil.copy2(dir_dynamic_file, asset_dir_path_temp)
        with fdopen(fd, "w") as tmp:
            tmp.write(md_content)
        pandoc = custom_program[PANDOC_ARGS_PDF_KEY_NAME][0]
        pandoc_args = custom_program_args[PANDOC_ARGS_PDF_KEY_NAME][0]
        cli_args: List[str] = [
            *pandoc_args,
            "-f",
            "markdown",
            str(md_file_path_temp),
            "-o",
            str(output_file_path.resolve()),
        ]
        subprocess_stdout = run_subprocess(pandoc, cli_args, cwd=asset_dir_path_temp)
        log.debug(f"> Stdout:         {subprocess_stdout=}")
    finally:
        if not keep_temp_files:
            md_file_path_temp.unlink()
            shutil.rmtree(asset_dir_path_temp)
