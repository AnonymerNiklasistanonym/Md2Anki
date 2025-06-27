#!/usr/bin/env python3

# Internal packages
import os
from typing import Dict, Final, List, Tuple

# Local modules
from md2anki.info.general import MD2ANKI_NAME


# Types
EvaluateCodeLanguageId = str
EvaluateCodeCommand = str
EvaluateCodeCommandArgument = str
EvaluateCodeInfo = Dict[
    EvaluateCodeLanguageId,
    List[Tuple[EvaluateCodeCommand, List[EvaluateCodeCommandArgument]]],
]

# Evaluate code information
EVALUATE_CODE_MD2ANKI_PLACEHOLDER_CODE_STRING: Final = f"{MD2ANKI_NAME.upper()}_CODE"
EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME: Final = (
    f"{MD2ANKI_NAME.upper()}_CODE_FILE="
)
EVALUATE_CODE_DEFAULT_COMMANDS: Final[EvaluateCodeInfo] = {
    "py": [("python", ["-c", EVALUATE_CODE_MD2ANKI_PLACEHOLDER_CODE_STRING])],
    "js": [("node", ["-e", EVALUATE_CODE_MD2ANKI_PLACEHOLDER_CODE_STRING])],
    "ts": [
        (
            "npx",
            ["tsx", f"{EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME}code.ts"],
        )
    ],
    "pl": [
        (
            "swipl",
            [
                "-O",
                "-s",
                f"{EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME}code.pl",
                "-g",
                "true",
                "-t",
                "halt.",
            ],
        )
    ],
    "latex": [
        (
            "latexmk",
            [
                "-shell-escape",
                "-pdf",
                f"{EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME}code.tex",
            ],
        ),
        (
            "inkscape",
            ["--export-filename=code.svg", "code.pdf"],
        ),
    ],
    "cpp": [
        (
            "clang++",
            [
                "-Wall",
                "-std=c++20",
                f"{EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME}main.cpp",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
    "c": [
        (
            "clang",
            [
                "-std=c17",
                f"{EVALUATE_CODE_MD2ANKI_PREFIX_CODE_FILE_NAME}main.c",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
}
"""The commands that should per default be used to evaluate code of certain languages."""
