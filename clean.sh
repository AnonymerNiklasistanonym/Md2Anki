#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Make script stop when an error happens
set -e

# Go to script directory even when run from another one
cd "$SCRIPT_DIR"

rm -rf __pycache__
rm -rf venv_Md2Anki

find examples -maxdepth 1 -type d -name "backup_*" -exec rm -rf {} \;
find examples -maxdepth 1 -type f -name "*.apkg" -exec rm -f {} \;
