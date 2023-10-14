#!/usr/bin/env python3

# Internal packages
from pathlib import Path
from typing import Final

# Relative file paths to res files
RELATIVE_RES_DIR: Final = Path("res")
RELATIVE_RES_CSS_FILE_PATH: Final = RELATIVE_RES_DIR.joinpath("stylesheet.css")
RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER: Final = RELATIVE_RES_DIR.joinpath(
    "stylesheet_type_answer.css"
)
RELATIVE_RES_CSS_FILE_PATH_TYPE_CLOZE: Final = RELATIVE_RES_DIR.joinpath(
    "stylesheet_type_cloze.css"
)
