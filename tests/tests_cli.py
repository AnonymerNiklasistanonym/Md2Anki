#!/usr/bin/env python3

# Internal packages
import sys
import unittest
from pathlib import Path
from typing import List, Tuple, Final

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.cli import (
    parse_cli_args,
    Md2AnkiArgs,
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
                    md_input_file_paths=[Path(__file__)],
                    md_output_file_paths=[Path(__file__)],
                    anki_output_file_path=Path(__file__).parent.joinpath(
                        f"{Path(__file__).stem}.apkg"
                    ),
                    custom_program=parse_cli_args([__file__]).custom_program,
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
            (
                [__file__, "-file-dir", str(Path(__file__).parent)],
                Md2AnkiArgs(
                    md_input_file_paths=[Path(__file__)],
                    md_output_file_paths=[Path(__file__)],
                    additional_file_dirs=[Path(__file__).parent],
                    anki_output_file_path=Path(__file__).parent.joinpath(
                        f"{Path(__file__).stem}.apkg"
                    ),
                    custom_program=parse_cli_args([__file__]).custom_program,
                    custom_program_args=parse_cli_args([__file__]).custom_program_args,
                ),
            ),
            (
                [__file__, str(Path(__file__).parent.joinpath("__init__.py"))],
                Md2AnkiArgs(
                    md_input_file_paths=[
                        Path(__file__),
                        Path(__file__).parent.joinpath("__init__.py"),
                    ],
                    md_output_file_paths=[
                        Path(__file__),
                        Path(__file__).parent.joinpath("__init__.py"),
                    ],
                    anki_output_file_path=Path(__file__).parent.joinpath(
                        f"{Path(__file__).stem}.apkg"
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
                    md_input_file_paths=[Path(__file__)],
                    md_output_file_paths=[Path(__file__)],
                    anki_output_file_path=Path(__file__).parent.joinpath(
                        f"{Path(__file__).stem}.apkg"
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
        # Detect not existing files
        file_path_not_found: Final = Path("not_found.md")
        error_file_not_found: Final = parse_cli_args([str(file_path_not_found)]).error
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
        file_dir_not_found: Final = Path("not_found")
        error_file_dir_not_found: Final = parse_cli_args(
            [__file__, "-file-dir", str(file_dir_not_found)]
        ).error
        # Don't throw errors if file exists
        self.assertIsNone(parse_cli_args([*self.valid_args]).error)
        # Don't throw errors if additional file directory exists
        self.assertIsNone(
            parse_cli_args(
                [*self.valid_args, "-file-dir", str(Path(__file__).parent)]
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
