#!/usr/bin/env python3

import shutil
import glob
import os


def rm_dir(dir_path: str, dry_run=False):
    print(f"Remove directory {dir_path!r}")
    if not dry_run and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)


def rm_file(file_path: str, dry_run=False):
    print(f"Remove file {file_path!r}")
    if not dry_run and os.path.isfile(file_path):
        os.remove(file_path)


if __name__ == "__main__":
    dry_run_deletions = False

    dir_root = os.path.dirname(__file__)
    dir_dist = os.path.join(dir_root, "dist")
    dir_examples = os.path.join(dir_root, "examples")
    dir_src = os.path.join(dir_root, "src")
    dir_egg_info = os.path.join(dir_src, "md2anki.egg-info")

    # Remove example files
    os.chdir(dir_examples)
    for glob_example_backup_dir in glob.glob("backup_*", recursive=False):
        rm_dir(
            os.path.join(dir_examples, glob_example_backup_dir),
            dry_run=dry_run_deletions,
        )
    for glob_example_apkg in glob.glob("*.apkg", recursive=False):
        rm_file(
            os.path.join(dir_examples, glob_example_apkg), dry_run=dry_run_deletions
        )
    for glob_example_pdf in glob.glob("*.pdf", recursive=False):
        rm_file(os.path.join(dir_examples, glob_example_pdf), dry_run=dry_run_deletions)

    # Remove dist directory
    rm_dir(dir_dist, dry_run=dry_run_deletions)

    # Remove egg-info directory
    rm_dir(dir_egg_info, dry_run=dry_run_deletions)

    # Remove pycache directories
    os.chdir(dir_root)
    for glob_pycache_dir in glob.glob("*__pycache__", recursive=True):
        rm_dir(os.path.join(dir_root, glob_pycache_dir), dry_run=dry_run_deletions)
