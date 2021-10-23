#!/usr/bin/env bash

set -x
set -e

CALL_DIR="$( pwd )"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$SCRIPT_DIR/.."

DIST_DIRECTORY="dist"
SRC_DIRECTORY="src"
PACKAGE_NAME="md2anki"
PACKAGE_VERSION="2.5.2"
BUILD_ENVIRONMENT="venv_build_environment"
INSTALL_ENVIRONMENT="venv_install_environment"

rm -rf "$BUILD_ENVIRONMENT"
rm -rf "$DIST_DIRECTORY"
rm -rf "$SRC_DIRECTORY/$PACKAGE_NAME.egg-info"
rm -rf "$INSTALL_ENVIRONMENT"

python3 -m venv "$BUILD_ENVIRONMENT"
source "$BUILD_ENVIRONMENT/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
python3 -m build
deactivate

python3 -m venv "$INSTALL_ENVIRONMENT"
source "$INSTALL_ENVIRONMENT/bin/activate"
python3 -m pip install --upgrade pip
pip install "$DIST_DIRECTORY/$PACKAGE_NAME-$PACKAGE_VERSION-py3-none-any.whl"
md2anki --version
md2anki --help
md2anki /home/niklas/Documents/GitHub/Md2Anki/examples/basic_example.md -o-anki /home/niklas/Documents/GitHub/Md2Anki/examples/aaa_it_works.apkg
md2anki /home/niklas/Documents/GitHub/Md2Anki/examples/images_example.md -o-anki /home/niklas/Documents/GitHub/Md2Anki/examples/bbb_it_works.apkg -file-dir /home/niklas/Documents/GitHub/Md2Anki/examples/
deactivate

cd "$CALL_DIR"
