#!/usr/bin/env python3

# Internal packages
import html
import shutil
import sys
import tempfile
from os import fdopen
from pathlib import Path
from typing import List, Optional, Dict, Final

# Local modules
from md2anki.info import md2anki_name
from md2anki.md_util import md_update_code_parts
from md2anki.print import debug_print
from md2anki.subprocess import (
    evaluate_code,
    UnableToEvaluateCodeException,
    run_subprocess,
)

pandoc_args_pdf: List[str] = [
    "-t",
    "pdf",
    "-V",
    "geometry:a4paper",
    "-V",
    "geometry:margin=2cm",
    "--pdf-engine=xelatex",
    "--pdf-engine-opt=-shell-escape",
]
"""Pandoc args for pdf export."""


def create_pdf_from_md_content(
    md_content: str,
    output_file_path: Path,
    local_assets: List[Path],
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Path,
    debug=False,
):
    # Evaluate code before running pandoc on it

    def md_code_replacer(language: Optional[str], code: str, code_block: bool):
        if language is not None and language.startswith("."):
            language = language[1:]
        # Detect executable code
        try:
            if language is not None and language.startswith("="):
                code_output, image_list = evaluate_code(
                    language[1:],
                    code,
                    debug=debug,
                    dir_dynamic_files=dir_dynamic_files,
                    custom_program=custom_program,
                    custom_program_args=custom_program_args,
                )
                debug_print(
                    f"> Evaluate {code=}: {code_output=}, {image_list=}", debug=debug
                )
                if len(image_list) > 0:
                    return "".join(map(lambda x: f"![]({x})\n", image_list))
                else:
                    return html.escape("".join(code_output))
        except UnableToEvaluateCodeException as err:
            print(err, file=sys.stderr)
        if code_block:
            return f"```{language}\n{code}```\n"
        else:
            return f"`{code}`" + (
                ("{." + language + "}") if language is not None else ""
            )

    md_content = md_update_code_parts(md_content, md_code_replacer)

    fd, md_file_path_temp_str = tempfile.mkstemp(f"{md2anki_name}_tmp_file_pandoc_md_")
    md_file_path_temp: Final = Path(md_file_path_temp_str)
    asset_dir_path_temp: Final = Path(
        tempfile.mkdtemp(f"{md2anki_name}_tmp_file_pandoc_md_assets_")
    )
    try:
        for local_asset in local_assets:
            debug_print(f"> Copy {local_asset=} to {asset_dir_path_temp=}", debug=debug)
            shutil.copy2(local_asset, asset_dir_path_temp)
        with fdopen(fd, "w") as tmp:
            tmp.write(md_content)
        pandoc = "pandoc"
        cli_args: List[str] = [
            *pandoc_args_pdf,
            "-f",
            "markdown",
            str(md_file_path_temp),
            "-o",
            str(output_file_path),
        ]
        if debug:
            cli_args.append("--verbose")
        subprocess_stdout = run_subprocess(
            pandoc, cli_args, cwd=asset_dir_path_temp, debug=debug
        )
        debug_print(f"> Stdout:         {subprocess_stdout=}", debug=debug)
        if len(subprocess_stdout) > 0:
            print(subprocess_stdout)
    finally:
        debug_print(
            f"Don't remove {md_file_path_temp=}, {asset_dir_path_temp}", debug=debug
        )
        if not debug:
            md_file_path_temp.unlink()
            shutil.rmtree(asset_dir_path_temp)
