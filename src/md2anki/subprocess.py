import glob
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional, Final, Dict, Tuple

from md2anki.info import md2anki_name
from md2anki.print import debug_print


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
    command: str,
    arguments: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    debug=False,
):
    command_path_global: Final = shutil.which(command)
    command_path_local: Final = (
        command_path_global if cwd is None else shutil.which(os.path.join(cwd, command))
    )
    command_path: Final = (
        command_path_local if command_path_local is not None else command_path_global
    )
    if command_path is None:
        raise ProgramNotFoundException(f"{command=} could not be found")
    if arguments is None:
        arguments = list()
    debug_print(
        f"Run subprocess {command=}/{command_path=} {arguments=} ({cwd=})", debug=debug
    )
    p = subprocess.run(
        [command_path, *arguments], capture_output=True, text=True, cwd=cwd
    )
    if p.returncode != 0:
        raise ProgramExitedWithWarningsException(
            f"Program exited with warnings ({command=},{arguments=},{cwd=},"
            f"{p.returncode=},{p.stdout=},{p.stderr=})"
        )
    return p.stdout


DEFAULT_CODE_NAME: Final = "MD2ANKI_CODE"
DEFAULT_CODE_FILE_NAME_START: Final = "DEFAULT_CODE_FILE_NAME_BEGIN="
DEFAULT_CUSTOM_PROGRAM: Final[Dict[str, List[Tuple[str, List[str]]]]] = {
    "py": [("python", ["-c", DEFAULT_CODE_NAME])],
    "js": [("node", ["-e", DEFAULT_CODE_NAME])],
    "ts": [("ts-node", [f"{DEFAULT_CODE_FILE_NAME_START}code.ts"])],
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


def evaluate_code(
    program: str,
    code: str,
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Optional[str] = None,
    debug=False,
) -> Tuple[List[str], List[str]]:
    """Return the command outputs and the found images."""
    dir_path_temp = tempfile.mkdtemp(prefix=f"{md2anki_name}_evaluate_code_")

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
                with open(
                    os.path.join(dir_path_temp, code_file_name), "w"
                ) as temp_file:
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
        for program_binary, program_binary_args in zip(
            program_binaries, program_binaries_args, strict=True
        ):
            results.append(
                run_subprocess(
                    program_binary, program_binary_args, cwd=dir_path_temp, debug=debug
                )
            )
        images_list = list()
        if dir_dynamic_files:
            pwd = os.getcwd()
            os.chdir(dir_path_temp)
            for glob_file in (
                glob.glob("*.svg") + glob.glob("*.png") + glob.glob("*.pdf")
            ):
                if dir_dynamic_files is None:
                    raise RuntimeError("Directory for dynamic files is None")
                debug_print(
                    f"Copy created file {glob_file=} to {dir_dynamic_files=}",
                    debug=debug,
                )
                shutil.copy2(glob_file, dir_dynamic_files)
                images_list.append(os.path.join(dir_dynamic_files, glob_file))
            os.chdir(pwd)
            debug_print(f"{images_list=} {results=}", debug=debug)
        return results, images_list

    finally:
        if not debug:
            shutil.rmtree(dir_path_temp)
