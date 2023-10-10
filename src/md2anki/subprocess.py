#!/usr/bin/env python3

# Internal packages
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Final, Dict

log = logging.getLogger(__name__)


class ProgramNotFoundException(Exception):
    """Raised when a program cannot be found"""

    pass


class ProgramExitedWithWarningsException(Exception):
    """Raised when a program exists with warnings"""

    pass


def run_subprocess(
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[Path] = None,
    additional_env: Optional[Dict[str, str]] = None,
):
    """
    Run an external process sequentially.

    @param command: Command/exe that should be run.
    @param args: Optional arguments of command.
    @param cwd: Optional directory from which the command should be run.
    @param additional_env: Optional additional environment variables with which the command should be run.
    @return:
    """
    command_path: Optional[str] = None
    if cwd is not None:
        command_path = shutil.which(str(cwd.joinpath(command)))
    if command_path is None and Path(command).is_file() and os.access(command, os.X_OK):
        command_path = command
        log.debug(f"Found command path os.access=OK {command_path=}")
    if command_path is None:
        command_path = shutil.which(command)
        log.debug(f"Found command path shutil.which {command_path=}")
    if command_path is None:
        raise ProgramNotFoundException(f"{command=} could not be found")
    command_args: Final[List[str]] = list() if args is None else args
    command_env = os.environ.copy()
    if additional_env is not None:
        for key, value in additional_env.items():
            command_env[key] = value
    log.debug(
        f"Run subprocess {command=}/{command_path=} {command_args=} ({cwd=},{additional_env=})"
    )
    p = subprocess.run(
        [command_path] + command_args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=command_env,
    )
    log.debug(f"Subprocess exited {p.stdout=} {p.returncode=}")
    if p.returncode != 0:
        raise ProgramExitedWithWarningsException(
            f"Subprocess exited with warnings ({command=},{args=},{cwd=},"
            f"{p.returncode=},{p.stdout=},{p.stderr=})"
        )
    return p.stdout
