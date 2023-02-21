#!/usr/bin/env python3

# Internal packages
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Final, Dict, Tuple

# Local modules
from md2anki.info import md2anki_name

log = logging.getLogger(__name__)


class UnableToEvaluateCodeException(Exception):
    """Raised when not able to evaluate code"""

    pass


class ProgramNotFoundException(Exception):
    """Raised when a program cannot be found"""

    pass


class ProgramExitedWithWarningsException(Exception):
    """Raised when a program exists with warnings"""

    pass


def run_subprocess(
    command: str, arguments: Optional[List[str]] = None, cwd: Optional[Path] = None
):
    command_path_global: Final = shutil.which(command)
    command_path_local = (
        command_path_global if cwd is None else shutil.which(str(cwd.joinpath(command)))
    )
    if (
        command_path_global is None
        and command_path_local is None
        and Path(command).is_file()
        and os.access(command, os.X_OK)
    ):
        command_path_local = command
    command_path: Final = (
        command_path_local if command_path_local is not None else command_path_global
    )
    if command_path is None:
        raise ProgramNotFoundException(f"{command=} could not be found")
    if arguments is None:
        arguments = list()
    log.debug(f"Run subprocess {command=}/{command_path=} {arguments=} ({cwd=})")
    p = subprocess.run(
        [command_path, *arguments], capture_output=True, text=True, cwd=cwd
    )
    log.debug(f"Subprocess output {p.stdout=} {p.returncode=}")
    if p.returncode != 0:
        raise ProgramExitedWithWarningsException(
            f"Program exited with warnings ({command=},{arguments=},{cwd=},"
            f"{p.returncode=},{p.stdout=},{p.stderr=})"
        )
    return p.stdout


DEFAULT_CODE_NAME: Final = "MD2ANKI_CODE"
DEFAULT_CODE_FILE_NAME_START: Final = "MD2ANKI_CODE_FILE="
DEFAULT_CUSTOM_PROGRAM: Final[Dict[str, List[Tuple[str, List[str]]]]] = {
    "py": [("python", ["-c", DEFAULT_CODE_NAME])],
    "js": [("node", ["-e", DEFAULT_CODE_NAME])],
    "ts": [("ts-node", [f"{DEFAULT_CODE_FILE_NAME_START}code.ts"])],
    "latex": [
        (
            "latexmk",
            [
                "-shell-escape",
                "-pdf",
                f"{DEFAULT_CODE_FILE_NAME_START}code.tex",
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
                f"{DEFAULT_CODE_FILE_NAME_START}main.cpp",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
    "c": [
        (
            "clang",
            ["-std=c17", f"{DEFAULT_CODE_FILE_NAME_START}main.c", "-o", "main.exe"],
        ),
        ("main.exe", []),
    ],
}


def subprocess_evaluate_code(
    program: str,
    code: str,
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Optional[Path] = None,
    keep_temp_files: bool = False,
) -> Tuple[List[str], List[Path]]:
    """Return the command outputs and the found images."""
    log.debug(f"Evaluate code ({program=},{code=})")

    dir_path_temp = Path(tempfile.mkdtemp(prefix=f"{md2anki_name}_evaluate_code_"))

    if program in custom_program:
        program_binaries = custom_program[program]
    else:
        raise UnableToEvaluateCodeException(f"Unsupported {program=} ({code=})")
    if program in custom_program_args:

        def insert_code_or_code_file(program_bin_arg: str) -> str:
            if program_bin_arg == DEFAULT_CODE_NAME:
                return code
            if program_bin_arg.startswith(DEFAULT_CODE_FILE_NAME_START):
                code_file_name = program_bin_arg[len(DEFAULT_CODE_FILE_NAME_START) :]
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
                run_subprocess(program_binary, program_binary_args, cwd=dir_path_temp)
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
