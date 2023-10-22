#!/usr/bin/env python3

import black
import re
from pathlib import Path


dir_path = Path(__file__).parent.resolve()

python_source_code_dirs = [
    dir_path.joinpath("examples"),
    dir_path.joinpath("src"),
    dir_path.joinpath("tests"),
]
python_source_code_files = [
    dir_path.joinpath("clean.py"),
    dir_path.joinpath("format.py"),
    dir_path.joinpath("main.py"),
    dir_path.joinpath("setup.py"),
    dir_path.joinpath("update_pkgbuild.py"),
    dir_path.joinpath("update_readme.py"),
]

# Main method
if __name__ == "__main__":
    python_files = black.gen_python_files(
        paths=[*python_source_code_dirs, *python_source_code_files],
        root=dir_path,
        include=re.compile(r"\.py$"),
        exclude=re.compile(r""),
        extend_exclude=None,
        force_exclude=None,
        report=black.Report(),
        gitignore_dict={},
        verbose=False,
        quiet=False,
    )
    unchanged_files_count = 0
    formatted_files_count = 0
    for file in python_files:
        formatted = black.format_file_in_place(
            file, fast=False, mode=black.Mode(), write_back=black.WriteBack.YES
        )
        if formatted:
            print(f"The file {file} was formatted")
            formatted_files_count += 1
        else:
            unchanged_files_count += 1
    print(
        f"Formatted {formatted_files_count} file(s) of {unchanged_files_count + formatted_files_count}"
    )
