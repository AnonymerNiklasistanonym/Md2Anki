#!/usr/bin/env python3

# Internal packages
import html
import logging
import shutil
import tempfile
from os import fdopen
from pathlib import Path
from typing import List, Optional, Dict, Final, Tuple

# Local modules
from md2anki.info import md2anki_name
from md2anki.md_util import md_update_code_parts
from md2anki.subprocess import (
    subprocess_evaluate_code,
    UnableToEvaluateCodeException,
    run_subprocess,
)

PANDOC_ARGS_PDF_KEY_NAME: Final = "pandoc_pdf"
PANDOC_ARGS_PDF: Final[Dict[str, List[Tuple[str, List[str]]]]] = {
    PANDOC_ARGS_PDF_KEY_NAME: [
        (
            "pandoc",
            [
                "-t",
                "pdf",
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
    evaluate_code: bool = False,
    keep_temp_files: bool = False,
):
    # Evaluate code before running pandoc on it

    def md_code_replacer(code: str, code_block: bool, language: Optional[str]):
        if language is not None and language.startswith("."):
            language = language[1:]
        # Detect executable code
        try:
            if evaluate_code and language is not None and language.startswith("="):
                code_output, image_list = subprocess_evaluate_code(
                    language[1:],
                    code,
                    dir_dynamic_files=dir_dynamic_files,
                    custom_program=custom_program,
                    custom_program_args=custom_program_args,
                    keep_temp_files=keep_temp_files,
                )
                log.debug(f"> Evaluate {code=}: {code_output=}, {image_list=}")
                if len(image_list) > 0:
                    return "".join(map(lambda x: f"![]({x})\n", image_list))
                else:
                    return html.escape("".join(code_output))
        except UnableToEvaluateCodeException as err:
            log.error(err)
        if code_block:
            return f"```{language}\n{code}```\n"
        else:
            return f"`{code}`" + (
                ("{." + language + "}") if language is not None else ""
            )

    md_content = md_update_code_parts(md_content, md_code_replacer)

    fd, md_file_path_temp_str = tempfile.mkstemp(prefix=f"{md2anki_name}_tmp_file_pandoc_md_", suffix=".md")
    md_file_path_temp: Final = Path(md_file_path_temp_str)
    asset_dir_path_temp: Final = Path(
        tempfile.mkdtemp(prefix=f"{md2anki_name}_tmp_file_pandoc_md_assets_")
    )
    try:
        for local_asset in local_assets:
            log.debug(f"> Copy {local_asset=} to {asset_dir_path_temp=}")
            shutil.copy2(local_asset, asset_dir_path_temp)
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
