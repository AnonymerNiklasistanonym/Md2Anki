#!/usr/bin/env python3

# Internal packages
import hashlib
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Tuple

# Local modules
from md2anki.info.evaluate_code import (
    EVALUATE_CODE_PLACEHOLDER_CODE_STRING,
    EVALUATE_CODE_PREFIX_CODE_FILE_NAME,
)
from md2anki.info.general import MD2ANKI_NAME
from md2anki.subprocess import run_subprocess

# Logger
log = logging.getLogger(__name__)


class UnableToEvaluateCodeException(Exception):
    """Raised when not able to evaluate code"""

    pass


def evaluate_code_get_hash(
    code: str,
    program_binary: str,
    program_binary_args: List[str],
    additional_env: Optional[Dict[str, str]] = None,
    additional_hash: Optional[str] = None,
) -> str:
    sha256_hash_code_evaluation = hashlib.sha256()
    sha256_hash_code_evaluation.update(code.encode("utf-8"))
    sha256_hash_code_evaluation.update(program_binary.encode("utf-8"))
    for argument in program_binary_args:
        sha256_hash_code_evaluation.update(argument.encode("utf-8"))
    if additional_env is not None:
        sha256_hash_code_evaluation.update(
            json.dumps(additional_env, sort_keys=True).encode("utf-8")
        )
    if additional_hash is not None:
        sha256_hash_code_evaluation.update(additional_hash.encode("utf-8"))
    return sha256_hash_code_evaluation.hexdigest()


def evaluate_code_check_cache(
    cache_dir: Optional[Path],
    code: str,
    program_binary: str,
    program_binary_args: List[str],
    additional_env: Optional[Dict[str, str]] = None,
    additional_hash: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    log.debug(f"Evaluate code check cache ({cache_dir=})")
    if cache_dir is None or not cache_dir.is_dir():
        log.debug("> False because cache dir None or not a dir")
        return False, None
    sha256_hash_code_evaluation = evaluate_code_get_hash(
        code,
        program_binary,
        program_binary_args,
        additional_env,
        additional_hash,
    )
    cached_code_evaluations_db = [x.name for x in cache_dir.glob("**/*") if x.is_dir()]
    if sha256_hash_code_evaluation in cached_code_evaluations_db:
        log.debug(f"> True because hit ({sha256_hash_code_evaluation=})")
        return True, sha256_hash_code_evaluation

    log.debug(f"> False because no hit ({sha256_hash_code_evaluation=})")
    return False, sha256_hash_code_evaluation


def evaluate_code_copy_and_get_cache(
    cache_dir: Path,
    target_dir: Path,
    cache_hash: str,
) -> str:
    log.debug(
        f"Evaluate code copy and get cache ({cache_dir=},{target_dir=},{cache_hash=})"
    )
    # Copy cached files
    cache_dir_code_evaluation = cache_dir.joinpath(cache_hash)
    if target_dir.is_dir():
        shutil.rmtree(target_dir)
    shutil.copytree(cache_dir_code_evaluation, target_dir)
    # Read command output
    cache_file_output_code_evaluation = cache_dir_code_evaluation.with_suffix(".txt")
    with open(cache_file_output_code_evaluation) as f:
        return f.read()


def evaluate_code_copy_and_store_cache(
    cache_dir: Optional[Path],
    target_dir: Path,
    command_output: str,
    cache_hash: Optional[str],
):
    log.debug(
        f"Evaluate code copy and store cache ({cache_dir=},{target_dir=},{cache_hash=})"
    )
    if cache_dir is None or cache_hash is None:
        # Do nothing if there is no cache directory
        return
    # Copy cached files
    cache_dir_code_evaluation = cache_dir.joinpath(cache_hash)
    if cache_dir_code_evaluation.is_dir():
        shutil.rmtree(cache_dir_code_evaluation)
    shutil.copytree(target_dir, cache_dir_code_evaluation)
    # Write command output
    cache_file_output_code_evaluation = cache_dir_code_evaluation.with_suffix(".txt")
    if cache_file_output_code_evaluation.is_file():
        cache_file_output_code_evaluation.unlink()
    with open(cache_file_output_code_evaluation, "w") as f:
        f.write(command_output)


def evaluate_code_in_subprocess(
    program: str,
    code: str,
    custom_program: Dict[str, List[str]],
    custom_program_args: Dict[str, List[List[str]]],
    dir_dynamic_files: Optional[Path] = None,
    keep_temp_files: bool = False,
    cache_dir: Optional[Path] = None,
    additional_env: Optional[Dict[str, str]] = None,
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
                f"Program binary ({len(program_binaries)}) and args list ({len(program_binaries_args)}) "
                "had different sizes"
            )
        previous_cache_hash: Optional[str] = None
        for program_binary, program_binary_args in zip(
            program_binaries, program_binaries_args
        ):
            # Check for cache
            cache_hit, cache_hash = evaluate_code_check_cache(
                cache_dir,
                code,
                program_binary,
                program_binary_args,
                additional_env,
                additional_hash=previous_cache_hash,
            )
            previous_cache_hash = cache_hash
            log.debug(f"Check cache {cache_dir=} ({cache_hit=},{cache_hash=})")
            if cache_hit and cache_hash is not None and cache_dir is not None:
                # Load cache
                p = evaluate_code_copy_and_get_cache(
                    cache_dir,
                    dir_path_temp,
                    cache_hash,
                )
                results.append(p)
            else:
                # Run subprocess
                try:
                    p = run_subprocess(
                        program_binary,
                        program_binary_args,
                        cwd=dir_path_temp,
                        additional_env=additional_env,
                    )
                except OSError as err:
                    log.error(
                        f"Error running the command {program_binary=} {program_binary_args=} cwd={dir_path_temp!r} {additional_env=} ({program=})"
                    )
                    raise err
                # Store cache
                evaluate_code_copy_and_store_cache(
                    cache_dir,
                    dir_path_temp,
                    p,
                    cache_hash,
                )
                results.append(p)
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
