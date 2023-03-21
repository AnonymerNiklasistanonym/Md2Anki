#!/usr/bin/env python3

# Internal packages
import tempfile
import shutil
from pathlib import Path


def rm_dir(dir_path: Path, dry_run=False):
    print(f"Remove directory {dir_path!r} ({dry_run=},isDir={dir_path.is_dir()})")
    if not dry_run and dir_path.is_dir():
        print("a")
        shutil.rmtree(dir_path)


def rm_file(file_path: Path, dry_run=False):
    print(f"Remove file {file_path!r} ({dry_run=},isFile={file_path.is_file()})")
    if not dry_run and file_path.is_file():
        file_path.unlink()


if __name__ == "__main__":
    dry_run_deletions = False

    dir_root = Path(__file__).parent.resolve()
    dir_dist = dir_root.joinpath("dist")
    dir_examples = dir_root.joinpath("examples")
    dir_src = dir_root.joinpath("src")
    dir_src_md2anki = dir_src.joinpath("md2anki")
    dir_src_md2anki_info = dir_src_md2anki.joinpath("info")
    dir_egg_info = dir_src.joinpath("md2anki.egg-info")
    dir_mypy_cache_list = [
        dir_root.joinpath(".mypy_cache"),
        dir_src.joinpath(".mypy_cache"),
        dir_src_md2anki.joinpath(".mypy_cache"),
        dir_src_md2anki_info.joinpath(".mypy_cache"),
    ]
    dir_temp = Path(tempfile.gettempdir())
    dir_coverage_html = dir_root.joinpath("htmlcov")
    coverage_file = dir_root.joinpath(".coverage")

    # Remove example files
    for example_backup_dir in dir_examples.rglob("backup_*"):
        rm_dir(example_backup_dir, dry_run=dry_run_deletions)
    for example_apkg in dir_examples.rglob("*.apkg"):
        rm_file(example_apkg, dry_run=dry_run_deletions)
    for example_pdf in dir_examples.rglob("*.pdf"):
        rm_file(example_pdf, dry_run=dry_run_deletions)
    for example_log in dir_examples.rglob("*.log"):
        rm_file(example_log, dry_run=dry_run_deletions)

    # Remove temporary files
    for md2anki_temp_dir in dir_temp.rglob("md2anki*"):
        try:
            rm_dir(md2anki_temp_dir, dry_run=dry_run_deletions)
        except PermissionError:
            pass

    # Remove dist directory
    rm_dir(dir_dist, dry_run=dry_run_deletions)

    # Remove egg-info directory
    rm_dir(dir_egg_info, dry_run=dry_run_deletions)

    # Remove mypy cache directory
    for dir_mypy_cache in dir_mypy_cache_list:
        rm_dir(dir_mypy_cache, dry_run=dry_run_deletions)

    # Remove pycache directories
    venv_directories = [
        dir_root.joinpath("venv_Md2Anki_pwsh"),
        dir_root.joinpath("venv_Md2Anki_sh"),
    ]
    for pycache_dir in dir_root.rglob("__pycache__"):
        skip = False
        for venv_directory in venv_directories:
            if pycache_dir.as_posix().startswith(venv_directory.as_posix()):
                skip = True
        if not skip:
            rm_dir(pycache_dir, dry_run=dry_run_deletions)

    # Remove coverage files
    rm_dir(dir_coverage_html, dry_run=dry_run_deletions)
    rm_file(coverage_file, dry_run=dry_run_deletions)
