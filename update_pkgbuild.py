#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Final, Optional, Union

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.joinpath("src")))

from md2anki.info.general import (
    MD2ANKI_NAME,
    MD2ANKI_NAME_GIT,
    MD2ANKI_DESCRIPTION,
    MD2ANKI_VERSION,
    MD2ANKI_URL,
)

ROOT_DIR_FILE_PATH: Final = Path(__file__).parent
PKGBUILD_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath("pkgbuild", "PKGBUILD")

UPDATE_KEYS: Final[dict[str, Union[str, list[str]]]] = {
    "depends": [
        "'python'",
        "'python-genanki-git'",
        "'python-beautifulsoup4'",
        "'python-markdown'",
        "'python-pygments'",
    ],
    "makedepends": [
        "'python-build'",
        "'python-installer'",
        "'python-wheel'",
        "'python-setuptools'",
    ],
    "optdepends": ["'pandoc-cli: export to pdf files'"],
    "pkgdesc": f"'{MD2ANKI_DESCRIPTION}'",
    "pkgname": f"python-{MD2ANKI_NAME}",
    "pkgver": f"{MD2ANKI_VERSION}",
    "sha256sums": [f"'SKIP'"],
    "source": [
        f'"$_name-$pkgver.tar.gz::{MD2ANKI_URL}/archive/refs/tags/v$pkgver.tar.gz"'
    ],
    "url": f"'{MD2ANKI_URL}'",
    "_name": f"{MD2ANKI_NAME_GIT}",
}


def update_pkgbuild_key(
    line: str, key: str, value: Union[str, list[str]]
) -> Optional[str]:
    if line.startswith(f"{key}="):
        if isinstance(value, list):
            return f"{key}=({' '.join(sorted(value))})\n"
        else:
            return f"{key}={value}\n"
    return None


def update_pkgbuild_content(pkgbuild_content: list[str]) -> str:
    out: str = ""
    for line in pkgbuild_content:
        updated_line = False
        for key, value in UPDATE_KEYS.items():
            content = update_pkgbuild_key(line, key, value)
            if content:
                out += content
                updated_line = True
                break
        if not updated_line:
            out += line
    return out


# Main method
if __name__ == "__main__":
    with open(PKGBUILD_FILE_PATH, "r") as input_file:
        pkgbuild_content_input = input_file.readlines()
    pkgbuild_content_output = update_pkgbuild_content(pkgbuild_content_input)
    with open(PKGBUILD_FILE_PATH, "w") as output_file:
        output_file.write(pkgbuild_content_output)
