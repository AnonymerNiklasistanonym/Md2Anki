import os.path
import sys
import unittest
from os.path import dirname, join
from pathlib import Path
from typing import List, Tuple

from md2anki.cli import (
    parse_cli_args,
    Md2AnkiArgs,
    AdditionalFileDirNotFoundException,
    MdInputFileNotFoundException,
)


class TestCliArgs(unittest.TestCase):
    def setUp(self):
        self.valid_args = [__file__]

        self.cli_args: List[List[str]] = list()
        self.results: List[Md2AnkiArgs] = list()
        self.expected: List[Md2AnkiArgs] = list()

        test_data: List[Tuple[List[str], Md2AnkiArgs]] = [
            (
                [__file__],
                Md2AnkiArgs(
                    md_input_file_paths=[__file__],
                    md_output_file_paths=[__file__],
                    anki_output_file_path=os.path.join(
                        os.path.dirname(__file__), Path(__file__).stem + ".apkg"
                    ),
                    custom_program=parse_cli_args([__file__]).custom_program,
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
            (
                [__file__, "-file-dir", os.path.dirname(__file__)],
                Md2AnkiArgs(
                    md_input_file_paths=[__file__],
                    md_output_file_paths=[__file__],
                    additional_file_dirs=[os.path.dirname(__file__)],
                    anki_output_file_path=os.path.join(
                        os.path.dirname(__file__), Path(__file__).stem + ".apkg"
                    ),
                    custom_program=parse_cli_args([__file__]).custom_program,
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
            (
                [__file__, os.path.join(os.path.dirname(__file__), "__init__.py")],
                Md2AnkiArgs(
                    md_input_file_paths=[
                        __file__,
                        os.path.join(os.path.dirname(__file__), "__init__.py"),
                    ],
                    md_output_file_paths=[
                        __file__,
                        os.path.join(os.path.dirname(__file__), "__init__.py"),
                    ],
                    anki_output_file_path=os.path.join(
                        os.path.dirname(__file__), Path(__file__).stem + ".apkg"
                    ),
                    custom_program=parse_cli_args([__file__]).custom_program,
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
            (
                [
                    __file__,
                    "-custom-program",
                    "py",
                    "python3.8",
                    "-custom-program",
                    "cpp",
                    "gcc",
                ],
                Md2AnkiArgs(
                    md_input_file_paths=[__file__],
                    md_output_file_paths=[__file__],
                    anki_output_file_path=os.path.join(
                        os.path.dirname(__file__), Path(__file__).stem + ".apkg"
                    ),
                    custom_program={
                        **parse_cli_args([__file__]).custom_program,
                        **{"py": ["python3.8"], "cpp": ["gcc"]},
                    },
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
        ]

        for test_cli_args, test_expected in test_data:
            self.cli_args.append(test_cli_args)
            self.results.append(parse_cli_args(test_cli_args))
            self.expected.append(test_expected)

    def test_cli_logic(self):
        # Debug flag
        self.assertTrue(
            parse_cli_args(["-d", *self.valid_args]).debug,
            "Debug flag -d enables debugging",
        )
        self.assertTrue(
            parse_cli_args(["--debug", *self.valid_args]).debug,
            "Debug flag --debug enables debugging",
        )
        # Detect not existing files
        file_path_not_found = "not_found.md"
        error_file_not_found = parse_cli_args([file_path_not_found]).error
        if error_file_not_found is not None and isinstance(
            error_file_not_found, MdInputFileNotFoundException
        ):
            self.assertEqual(
                error_file_not_found.md_input_file_path,
                file_path_not_found,
                "Error is thrown if file can not be found",
            )
        else:
            self.fail(f"Expected file not found error ({error_file_not_found=})")
        # Detect not existing additional file directories
        file_dir_not_found = "not_found"
        error_file_not_found = parse_cli_args(
            [__file__, "-file-dir", file_dir_not_found]
        ).error
        if error_file_not_found is not None and isinstance(
            error_file_not_found, AdditionalFileDirNotFoundException
        ):
            self.assertEqual(
                error_file_not_found.additional_file_dir_path,
                file_dir_not_found,
                "Error is thrown if additional file directory can not be found",
            )
        else:
            self.fail(f"Expected file not found error ({error_file_not_found=})")
        # Don't throw errors if file exists
        self.assertIsNone(parse_cli_args([*self.valid_args]).error)
        # Don't throw errors if additional file directory exists
        self.assertIsNone(
            parse_cli_args(
                [*self.valid_args, "-file-dir", os.path.dirname(__file__)]
            ).error
        )

    def test_parsed_cli_args_same(self):
        for cli_args, result, expected in zip(
            self.cli_args, self.results, self.expected
        ):
            with self.subTest(cli_args=cli_args):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if parsed cli args {result=}=={expected=}",
                )
