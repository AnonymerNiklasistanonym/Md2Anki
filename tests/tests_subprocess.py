#!/usr/bin/env python3

# Internal packages
import unittest
import sys
from pathlib import Path
from typing import List, Tuple

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.cli import (
    convert_list_to_dict_merged,
    DEFAULT_CUSTOM_PROGRAMS,
    DEFAULT_CUSTOM_PROGRAM_ARGS,
    str_to_str,
    json_str_to_str_list,
)
from md2anki.subprocess import evaluate_code


class TestEvaluateCode(unittest.TestCase):
    def setUp(self):
        self.code: List[Tuple[str, str]] = list()
        self.results: List[Tuple[List[str], List[Path]]] = list()
        self.expected: List[Tuple[List[str], List[Path]]] = list()

        test_data: List[Tuple[str, str, Tuple[List[str], List[Path]]]] = [
            ("", "py", ([""], [])),
            (
                'print("Hello world!")',
                "py",
                (["Hello world!\n"], []),
            ),
            (
                "a = 42\n" 'print(f"The answer is {a}")',
                "py",
                (["The answer is 42\n"], []),
            ),
            ("", "js", ([""], [])),
            (
                'console.log("Hello world!")',
                "js",
                (["Hello world!\n"], []),
            ),
            (
                "const a = 42\n" "console.log(`The answer is ${a}`)",
                "js",
                (["The answer is 42\n"], []),
            ),
            (
                'let message: string = "Hello world!"\nconsole.log(message)',
                "ts",
                (["Hello world!\n"], []),
            ),
            (
                "#include<stdio.h>\n"
                "int main() {\n"
                '	printf("Hello world!\\n");\n'
                "	return 0;\n"
                "}",
                "c",
                (["", "Hello world!\n"], []),
            ),
            (
                "#include <iostream>\n"
                "int main() {\n"
                '	std::cout << "Hello world!" << std::endl;\n'
                "	return 0;\n"
                "}",
                "cpp",
                (["", "Hello world!\n"], []),
            ),
        ]

        for test_input, test_program, test_expected in test_data:
            self.code.append((test_program, test_input))
            self.results.append(
                evaluate_code(
                    test_program,
                    test_input,
                    custom_program=convert_list_to_dict_merged(
                        DEFAULT_CUSTOM_PROGRAMS, str_to_str
                    ),
                    custom_program_args=convert_list_to_dict_merged(
                        DEFAULT_CUSTOM_PROGRAM_ARGS, json_str_to_str_list
                    ),
                )
            )
            self.expected.append(test_expected)

    def test_evaluated_code_output_matches(self):
        for (language, code), result, expected in zip(
            self.code, self.results, self.expected
        ):
            with self.subTest(language=language, code=code):
                self.assertEqual(
                    result, expected, f"Check if output {result=}=={expected=}"
                )
