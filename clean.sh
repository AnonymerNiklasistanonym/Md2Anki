#!/usr/bin/env bash

CALL_DIR="$( pwd )"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Make script stop when an error happens
set -e

# Go to script directory even when run from another one
cd "$SCRIPT_DIR"

rm -rf dist
find . -maxdepth 1 -type d -name "venv_*" -exec rm -rf {} \;
find . -type d -name "*__pycache__" -exec rm -rf {} \;
find examples -maxdepth 1 -type d -name "backup_*" -exec rm -rf {} \;
find examples -maxdepth 1 -type f -name "*.apkg" -exec rm -f {} \;

cd "$CALL_DIR"
