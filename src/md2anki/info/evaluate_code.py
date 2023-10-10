#!/usr/bin/env python3

# Internal packages
import os
from typing import Dict, Final, List, Tuple

# Types
EvaluateCodeLanguageId = str
EvaluateCodeCommand = str
EvaluateCodeCommandArgument = str
EvaluateCodeInfo = Dict[
    EvaluateCodeLanguageId,
    List[Tuple[EvaluateCodeCommand, List[EvaluateCodeCommandArgument]]],
]

# evaluate code information
EVALUATE_CODE_PLACEHOLDER_CODE_STRING: Final = "MD2ANKI_CODE"
EVALUATE_CODE_PREFIX_CODE_FILE_NAME: Final = "MD2ANKI_CODE_FILE="
EVALUATE_CODE_DEFAULT_COMMANDS: Final[EvaluateCodeInfo] = {
    "py": [("python", ["-c", EVALUATE_CODE_PLACEHOLDER_CODE_STRING])],
    "js": [("node", ["-e", EVALUATE_CODE_PLACEHOLDER_CODE_STRING])],
    "ts": [
        (
            "ts-node.cmd" if os.name == "nt" else "ts-node",
            [f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.ts"],
        )
    ],
    "pl": [
        (
            "swipl",
            [
                "-O",
                "-s",
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.pl",
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
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}code.tex",
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
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}main.cpp",
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
                f"{EVALUATE_CODE_PREFIX_CODE_FILE_NAME}main.c",
                "-o",
                "main.exe",
            ],
        ),
        ("main.exe", []),
    ],
}
