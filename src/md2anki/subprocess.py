import glob
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional
from enum import StrEnum

from md2anki.info import md2anki_name
from md2anki.print import debug_print


class SubprocessPrograms(StrEnum):
    PYTHON = ("python",)
    JAVASCRIPT = ("javascript",)
    TYPESCRIPT = ("typescript",)
    JUPYTER_NOTEBOOK_MATPLOTLIB = ("jupyter_notebook_matplotlib",)
    CPP = ("cpp",)
    C = ("c",)


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
    command_path = shutil.which(command)
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


def evaluate_code(program: str, code: str, debug=False, dir_dynamic_files: str = None):
    dir_path_temp = tempfile.mkdtemp(prefix=f"{md2anki_name}_evaluate_code_")
    try:
        if program == SubprocessPrograms.PYTHON:
            return run_subprocess(
                "python", ["-c", code], cwd=dir_path_temp, debug=debug
            )
        elif program == SubprocessPrograms.JAVASCRIPT:
            return run_subprocess("node", ["-e", code], cwd=dir_path_temp, debug=debug)
        elif program == SubprocessPrograms.TYPESCRIPT:
            return run_subprocess(
                "ts-node",
                ["-e", code.replace("\n", ";")],
                cwd=dir_path_temp,
                debug=debug,
            )
        elif program == SubprocessPrograms.JUPYTER_NOTEBOOK_MATPLOTLIB:
            result = run_subprocess(
                "python", ["-c", code], cwd=dir_path_temp, debug=debug
            )
            pwd = os.getcwd()
            os.chdir(dir_path_temp)
            images_output = ""
            for glob_file in (
                glob.glob("*.svg") + glob.glob("*.png") + glob.glob("*.pdf")
            ):
                debug_print(
                    f"Copy created file {glob_file=} to {dir_dynamic_files=}",
                    debug=debug,
                )
                shutil.copy2(glob_file, dir_dynamic_files)
                images_output += (
                    f"\n![]({os.path.join(dir_dynamic_files, glob_file)})\n"
                )
            os.chdir(pwd)
            debug_print(f"{images_output=} {result=}", debug=debug)
            return images_output if len(images_output) > 0 else result
        elif program == SubprocessPrograms.CPP:
            with open(os.path.join(dir_path_temp, "main.cpp"), "w") as file:
                file.write(code)
            run_subprocess(
                "clang++",
                ["-Wall", "-std=c++20", "main.cpp", "-o", "main.exe"],
                cwd=dir_path_temp,
                debug=debug,
            )
            return run_subprocess(
                os.path.join(dir_path_temp, "main.exe"),
                [],
                cwd=dir_path_temp,
                debug=debug,
            )
        elif program == SubprocessPrograms.C:
            with open(os.path.join(dir_path_temp, "main.c"), "w") as file:
                file.write(code)
            run_subprocess(
                "clang",
                ["-std=c17", "main.c", "-o", "main.exe"],
                cwd=dir_path_temp,
                debug=debug,
            )
            return run_subprocess(
                os.path.join(dir_path_temp, "main.exe"),
                [],
                cwd=dir_path_temp,
                debug=debug,
            )
        else:
            raise UnableToEvaluateCodeException(f"Unsupported {program=} ({code=})")
    finally:
        if not debug:
            shutil.rmtree(dir_path_temp)
