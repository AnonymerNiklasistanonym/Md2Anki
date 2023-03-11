#!/usr/bin/env python3

# Future import to support Python 3.9
from __future__ import annotations

# Internal modules
import sys
from pathlib import Path
from setuptools import setup, find_packages
from typing import Final

# Append the module path for md2anki standalone information files
sys.path.append(str(Path(__file__).parent.joinpath("src", "md2anki")))

# Local modules
# These imports will only import the self-contained constants of the files and not require the module dependencies
from info.general import (
    MD2ANKI_VERSION,
    MD2ANKI_NAME,
    MD2ANKI_AUTHOR,
    MD2ANKI_DESCRIPTION,
    MD2ANKI_URL,
    MD2ANKI_URL_BUG_TRACKER,
)
from info.files import (
    RELATIVE_RES_CSS_FILE_PATH,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER,
)


with open("README.md", "r", encoding="utf-8") as f:
    long_description: Final = f.read()


setup(
    name=MD2ANKI_NAME,
    version=str(MD2ANKI_VERSION),
    author=MD2ANKI_AUTHOR,
    description=MD2ANKI_DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=MD2ANKI_URL,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "beautifulsoup4>=4.11.2",
        "genanki>=0.13.0",
        "Markdown>=3.4.1",
        "Pygments>=2.14.0",
    ],
    package_data={
        MD2ANKI_NAME: [
            str(RELATIVE_RES_CSS_FILE_PATH),
            str(RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER),
        ],
    },
    entry_points={
        "console_scripts": [
            f"{MD2ANKI_NAME}={MD2ANKI_NAME}:_main",
        ],
    },
    project_urls={
        "Bug Tracker": MD2ANKI_URL_BUG_TRACKER,
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
