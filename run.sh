#!/usr/bin/env bash

CALL_DIR="$( pwd )"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_VENV_DIR=$SCRIPT_DIR/venv_Md2Anki_sh
PYTHON_VENV_REQUIREMENTS_FILE=$SCRIPT_DIR/requirements.txt

# Make script stop when an error happens
set -e

# Go to script directory even when run from another one
cd "$SCRIPT_DIR"

# (Create and) Enter virtual environment
if ! [ -d "$PYTHON_VENV_DIR" ]; then
    python3 -m venv "$PYTHON_VENV_DIR"
    source "$PYTHON_VENV_DIR/bin/activate"
    python3 -m pip install --upgrade pip
    if ! [ -f "$PYTHON_VENV_REQUIREMENTS_FILE" ]; then
        echo "Requirements file was not found: '$PYTHON_VENV_REQUIREMENTS_FILE'"
        exit 1
        #Uncomment for fresh install of latest versions of used 3rd party packages
        #pip install genanki markdown
        #pip freeze > "$PYTHON_VENV_REQUIREMENTS_FILE"
    else
        pip install -r "$PYTHON_VENV_REQUIREMENTS_FILE"
    fi
else
    source "$PYTHON_VENV_DIR/bin/activate"
fi

# Run script from call directory
cd "$CALL_DIR"
python3 "$SCRIPT_DIR/main.py" "$@"
