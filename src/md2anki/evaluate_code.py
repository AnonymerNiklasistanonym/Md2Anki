#!/usr/bin/env python3

# Internal packages
import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Final, Dict, Tuple

# Local modules
from md2anki.info import MD2ANKI_NAME
from md2anki.subprocess import run_subprocess

# Logger
log = logging.getLogger(__name__)

# Types
EvaluateCodeLanguageId = str
EvaluateCodeCommand = str
EvaluateCodeCommandArgument = str
EvaluateCodeInfo = Dict[
    EvaluateCodeLanguageId,
    List[Tuple[EvaluateCodeCommand, List[EvaluateCodeCommandArgument]]],
]

# Constants
EVALUATE_CODE_PLACEHOLDER_CODE_STRING: Final = "MD2ANKI_CODE"
EVALUATE_CODE_PREFIX_CODE_FILE_NAME: Final = "MD2ANKI_CODE_FILE="
DEFAULT_CUSTOM_PROGRAM: Final[EvaluateCodeInfo] = {
    "py": [("python", ["-c", EVALUATE_CODE_PLACEHOLDER_CODE_STRING])],
    "js": [("node", ["-e", EVALUATE_CODE_PLACEHOLDER_CODE_STRING])],
    "ts": [("ts-node", [f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.ts"])],
    "pl": [
        (
            "swipl",
            [
                "-O",
                "-s",
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.pl",
                "-g",
                "true",
                "-t",
                "halt.",
            ],
        )
    ],
    "latex": [
        (
            "latexmk",
            [
                "-shell-escape",
                "-pdf",
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.tex",
            ],
        ),
        (
            "inkscape",
            ["--export-filename=code.svg", "code.pdf"],
        ),
    ],
    "cpp": [
        (
            "clang++",
            [
                "-Wall",
                "-std=c++20",
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}main.cpp",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
    "c": [
        (
            "clang",
            [
                "-std=c17",
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}main.c",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
}


class UnableToEvaluateCodeException(Exception):
    """Raised when not able to evaluate code"""

    pass


def evaluate_code_in_subprocess(
    program: str,
    code: str,
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Optional[Path] = None,
    keep_temp_files: bool = False,
    custom_env: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], List[Path]]:
    """Return the command outputs and the found images."""
    log.debug(f"Evaluate code ({program=},{code=})")

    dir_path_temp = Path(tempfile.mkdtemp(prefix=f"{MD2ANKI_NAME}_evaluate_code_"))

    if program in custom_program:
        program_binaries = custom_program[program]
    else:
        raise UnableToEvaluateCodeException(f"Unsupported {program=} ({code=})")
    if program in custom_program_args:

        def insert_code_or_code_file(program_bin_arg: str) -> str:
            if program_bin_arg == EVALUATE_CODE_PLACEHOLDER_CODE_STRING:
                return code
            if program_bin_arg.startswith(EVALUATE_CODE_PREFIX_CODE_FILE_NAME):
                code_file_name = program_bin_arg[
                    len(EVALUATE_CODE_PREFIX_CODE_FILE_NAME) :
                ]
                if len(code_file_name) == 0:
                    raise RuntimeError(
                        f"Custom code file name had 0 length: {program_bin_arg!r}"
                    )
                with open(dir_path_temp.joinpath(code_file_name), "w") as temp_file:
                    temp_file.write(code)
                return code_file_name
            return program_bin_arg

        def update_list(program_bin_arg_dict_entry: List[str]) -> List[str]:
            return list(map(insert_code_or_code_file, program_bin_arg_dict_entry))

        program_binaries_args: List[List[str]] = list(
            map(update_list, custom_program_args[program])
        )
    else:
        program_binaries_args = list()
    while len(program_binaries_args) < len(program_binaries):
        program_binaries_args.append(list())

    try:
        results: List[str] = list()
        if len(program_binaries) != len(program_binaries_args):
            raise RuntimeError(
                f"Program binary ({len(program_binaries)}) and args list ({len(program_binaries_args)}) had different sizes"
            )
        for program_binary, program_binary_args in zip(
            program_binaries, program_binaries_args
        ):
            results.append(
                run_subprocess(
                    program_binary,
                    program_binary_args,
                    cwd=dir_path_temp,
                    additional_env=custom_env,
                )
            )
        images_list = list()
        if dir_dynamic_files is not None:
            for supported_media_files in [".svg", ".png", ".jpg"]:
                for glob_file in dir_path_temp.rglob(f"*{supported_media_files}"):
                    log.debug(
                        f"Copy created file {glob_file=} to {dir_dynamic_files=}",
                    )
                    shutil.copy2(glob_file, dir_dynamic_files)
                    images_list.append(dir_dynamic_files.joinpath(glob_file.name))
            log.debug(f"{images_list=} {results=}")
        return results, images_list

    finally:
        if not keep_temp_files:
            shutil.rmtree(dir_path_temp)
