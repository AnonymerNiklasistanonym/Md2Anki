#!/usr/bin/env python3

# Future import to support Python 3.9
from __future__ import annotations

# Internal packages
import argparse
import json
import logging
import sys
import tempfile
from dataclasses import dataclass, field
from operator import attrgetter
from pathlib import Path
from typing import Optional, List, Dict, Final, Tuple, TypeVar, Callable

# Local modules
from md2anki.info.evaluate_code import (
    EVALUATE_CODE_DEFAULT_COMMANDS,
    EVALUATE_CODE_PLACEHOLDER_CODE_STRING,
)
from md2anki.info.general import (
    MD2ANKI_VERSION,
    MD2ANKI_NAME,
    MD2ANKI_MD_EVALUATE_CODE_LANGUAGE_PREFIX,
)
from md2anki.md_to_pdf import PANDOC_ARGS_PDF
from md2anki.note_models import AnkiCardModelId


class SortedArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter("option_strings"))
        super(argparse.ArgumentDefaultsHelpFormatter, self).add_arguments(actions)


class MdInputFileNotFoundException(Exception):
    """Raised when a markdown input file is not found"""

    md_input_file_path: Final[Path]

    def __init__(self, md_input_file_path: Path):
        absolute_path: Final = md_input_file_path.absolute()
        super().__init__(
            f"Markdown input file was not found ({md_input_file_path!r}, {absolute_path=})"
        )
        self.md_input_file_path = md_input_file_path


@dataclass
class Md2AnkiArgs:
    """
    Contains all information of the md2anki command line arguments.
    """

    additional_file_dirs: List[Path] = field(default_factory=lambda: list())
    """Additional file directories for external file references (i.e. images)."""
    anki_card_model: AnkiCardModelId = AnkiCardModelId.DEFAULT
    """Anki card model."""
    md_input_file_paths: List[Path] = field(default_factory=lambda: list())
    """The markdown input file paths."""
    md_output_file_paths: Optional[List[Path]] = None
    """The optional output file paths of the updated markdown files (i.e. with added IDs)."""
    md_output_dir_path: Optional[Path] = None
    """The optional output dir path of the updated markdown files (i.e. with added IDs)."""
    anki_output_file_path: Optional[Path] = None
    """The output file path of the anki deck output file."""
    backup_output_dir_path: Optional[Path] = None
    """The output dir path of the backup of the anki deck."""
    pdf_output_file_path: Optional[Path] = None
    """The output file path of the anki deck."""
    md_heading_depth: int = 1
    """The default heading depth for the anki deck heading (increases for each subdeck/question by 1)."""
    custom_program: Dict[str, List[str]] = field(default_factory=lambda: dict())
    """Custom programs for languages used for code evaluation."""
    custom_program_args: Dict[str, List[List[str]]] = field(
        default_factory=lambda: dict()
    )
    """Custom program args for languages used for code evaluation."""
    evaluate_code_cache_dir_path: Optional[Path] = None
    """The optional cache dir path of the evaluated code."""

    evaluate_code = False
    """Evaluate code."""
    evaluate_code_ignore_cache = False
    """Ignore cache of already evaluated code."""
    evaluate_code_delete_cache = False
    """Delete cache of already evaluated code."""
    keep_temp_files = False
    """Remove temporary files."""
    error: Optional[MdInputFileNotFoundException] = None
    """Error message in case there was an error parsing CLI args."""


T = TypeVar("T")
U = TypeVar("U")


def convert_list_to_dict_merged(
    list_object: List[Tuple[str, T]],
    value_func: Callable[[T], U],
) -> Dict[str, List[U]]:
    dict_object: Dict[str, List[U]] = dict()
    for key, value in list_object:
        dict_object.setdefault(key, []).append(value_func(value))
    return dict_object


DEFAULT_CUSTOM_PROGRAMS: Final = [
    (key, program)
    for key, values in EVALUATE_CODE_DEFAULT_COMMANDS.items()
    for program, _ in values
] + [(key, program) for key, values in PANDOC_ARGS_PDF.items() for program, _ in values]
DEFAULT_CUSTOM_PROGRAM_ARGS: Final = [
    (key, json.dumps(program_args))
    for key, values in EVALUATE_CODE_DEFAULT_COMMANDS.items()
    for _, program_args in values
] + [
    (key, json.dumps(program_args))
    for key, values in PANDOC_ARGS_PDF.items()
    for _, program_args in values
]

log = logging.getLogger(__name__)


def str_to_str(a: str) -> str:
    return a


def json_str_to_str_list(possible_json_string: str) -> List[str]:
    try:
        possible_string_list: List[str] = json.loads(possible_json_string)
        if not all(isinstance(elem, str) for elem in possible_string_list):
            raise RuntimeError(
                f"Supplied json string was not a string list ({possible_json_string=},{possible_string_list=})"
            )
        return possible_string_list
    except ValueError as err:
        raise RuntimeError(
            f"Supplied json string {possible_json_string!r} was not a valid JSON string ({err})"
        )


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an anki deck file (.apkg) from one or more Markdown documents. "
        "If no custom output path is given the file name of the document (+ .apkg) is used.",
        formatter_class=SortedArgumentDefaultsHelpFormatter,
        prog=MD2ANKI_NAME,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {MD2ANKI_VERSION}"
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="log_level",
        const="DEBUG",
        default="INFO",
        action="store",
        nargs="?",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="custom log level to the console",
    )

    parser.add_argument(
        "-e",
        "--evaluate-code",
        action="store_true",
        help="evaluate markdown inline code/code blocks with the language prefix "
        f"{MD2ANKI_MD_EVALUATE_CODE_LANGUAGE_PREFIX!r} "
        "i.e. '`print(1+1)`{=python} or '```{=python} [newline] print(1+1) [newline] ```'",
    )
    parser.add_argument(
        "--evaluate-code-ignore-cache",
        action="store_true",
        help="ignore the cached files from previous code evaluations",
    )
    parser.add_argument(
        "--evaluate-code-delete-cache",
        action="store_true",
        help="delete all cached files from previous code evaluations",
    )
    parser.add_argument(
        "-k",
        "--keep-temp-files",
        action="store_true",
        help="keep temporary files",
    )
    parser.add_argument(
        "-anki-model",
        metavar="MODEL_ID",
        type=AnkiCardModelId,
        choices=list(AnkiCardModelId),
        default=AnkiCardModelId.DEFAULT,
        help=f"custom anki card model (%(choices)s)",
    )
    parser.add_argument(
        "-o-anki",
        metavar="APKG_FILE",
        type=Path,
        help="custom anki deck (.apkg) output file path [if not given: md input file "
        "name + .apkg]",
    )
    parser.add_argument(
        "-o-md",
        metavar="MD_FILE",
        type=Path,
        help="custom updated (and merged if multiple input files) Markdown (.md) output file path for all input files",
    )
    parser.add_argument(
        "-o-md-dir",
        metavar="MD_DIR",
        type=Path,
        help="custom output directory for all updated Markdown (.md) input files",
    )
    parser.add_argument(
        "-o-backup-dir",
        metavar="BACKUP_DIR",
        type=Path,
        help="create a backup of the anki deck (i.e. merges input files and copies external files) in a directory",
    )
    parser.add_argument(
        "-o-pdf",
        metavar="PDF_FILE",
        type=Path,
        help="create a PDF (.pdf) file of the anki deck (i.e. merges input files and removes IDs)",
    )
    parser.add_argument(
        "-evaluate-code-cache-dir",
        metavar="CACHE_DIR",
        type=Path,
        help="use a custom cache dir for code evaluations",
    )
    parser.add_argument(
        "-log-file",
        metavar="LOG_FILE",
        type=Path,
        help="log all messages to a text file (.log)",
    )
    parser.add_argument(
        "-file-dir",
        metavar="FILE_DIR",
        type=Path,
        action="extend",
        nargs="*",
        default=[],
        help="add directories that should be checked for referenced files (like relative path images)",
    )

    def check_heading_depth(x: str) -> int:
        x_num = int(x)
        if x_num < 1:
            raise argparse.ArgumentTypeError("Minimum heading depth is 1")
        return x_num

    parser.add_argument(
        "-md-heading-depth",
        metavar="HEADING_DEPTH",
        type=check_heading_depth,
        default=1,
        help="use a custom Markdown heading depth (>=1)",
    )
    parser.add_argument(
        "-custom-program",
        metavar=("language", "program"),
        type=str,
        action="append",
        nargs=2,
        default=DEFAULT_CUSTOM_PROGRAMS,
        help='use custom program for code evaluation [i.e. "py" "python3.11"]',
    )
    parser.add_argument(
        "-custom-program-args",
        metavar=("language", "program-args"),
        type=str,
        action="append",
        nargs=2,
        default=DEFAULT_CUSTOM_PROGRAM_ARGS,
        help='use custom program args for code evaluation  [i.e. "py" "[\\"-c\\",\\"'
        f"{EVALUATE_CODE_PLACEHOLDER_CODE_STRING}"
        '\\"]"]',
    )
    parser.add_argument(
        "md_input_files",
        metavar="MD_INPUT_FILE",
        type=Path,
        nargs="+",
        help="Markdown (.md) input file that contains anki deck notes",
    )
    return parser


class FormatterCleanInfo(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        else:
            self._style._fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        return super().format(record)


class Formatter(logging.Formatter):
    def format(self, record):
        self._style._fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        return super().format(record)


def parse_cli_args(cli_args: List[str]) -> Md2AnkiArgs:
    """
    Parse the supplied CLI arguments.

    @return: Object that contains all parsed information.
    """
    parser = get_argument_parser()
    args = parser.parse_args(cli_args)
    parsed_args = Md2AnkiArgs()

    handlers: List[logging.FileHandler | logging.StreamHandler] = []

    # Create a logging handler to stdout only for info
    hdlr_info = logging.StreamHandler(sys.stdout)
    hdlr_info.setFormatter(FormatterCleanInfo())
    hdlr_info.setLevel(getattr(logging, args.log_level))
    hdlr_info.addFilter(lambda record: record.levelno < logging.WARNING)
    handlers.append(hdlr_info)

    # Create a logging handler to stderr for warnings and errors
    hdlr_warn_err = logging.StreamHandler(sys.stderr)
    hdlr_warn_err.setFormatter(Formatter())
    hdlr_warn_err.setLevel(logging.WARNING)
    hdlr_warn_err.addFilter(lambda record: record.levelno >= logging.WARNING)
    handlers.append(hdlr_warn_err)

    if args.log_file is not None:
        # Create a logging handler to a file for everything
        hdlr_file = logging.FileHandler(args.log_file, mode="w")
        hdlr_file.setFormatter(Formatter())
        hdlr_file.setLevel(logging.DEBUG)
        handlers.append(hdlr_file)

    # This is necessary to fix the file handler
    logging.root.handlers = []

    # Setup global logging
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    log.debug(f"{cli_args=}, {args=}")

    parsed_args.additional_file_dirs = args.file_dir
    parsed_args.anki_card_model = args.anki_model
    parsed_args.md_heading_depth = args.md_heading_depth
    parsed_args.md_input_file_paths = args.md_input_files
    parsed_args.backup_output_dir_path = args.o_backup_dir
    parsed_args.pdf_output_file_path = args.o_pdf
    parsed_args.evaluate_code = args.evaluate_code
    parsed_args.evaluate_code_ignore_cache = args.evaluate_code_ignore_cache
    parsed_args.evaluate_code_delete_cache = args.evaluate_code_delete_cache
    parsed_args.evaluate_code_cache_dir_path = args.evaluate_code_cache_dir

    if parsed_args.evaluate_code_cache_dir_path is None:
        parsed_args.evaluate_code_cache_dir_path = Path(tempfile.gettempdir()).joinpath(
            f"{MD2ANKI_NAME}_evaluate_code_cache"
        )

    if args.keep_temp_files is not None:
        parsed_args.keep_temp_files = args.keep_temp_files

    temp_custom_program = convert_list_to_dict_merged(
        args.custom_program[: len(DEFAULT_CUSTOM_PROGRAMS)], str_to_str
    )
    if args.custom_program is not None:
        parsed_args.custom_program = convert_list_to_dict_merged(
            args.custom_program[len(DEFAULT_CUSTOM_PROGRAMS) :], str_to_str
        )
    parsed_args.custom_program = {
        **temp_custom_program,
        **parsed_args.custom_program,
    }

    temp_custom_program_args = convert_list_to_dict_merged(
        args.custom_program_args[: len(DEFAULT_CUSTOM_PROGRAM_ARGS)],
        json_str_to_str_list,
    )
    if args.custom_program_args is not None:
        parsed_args.custom_program_args = convert_list_to_dict_merged(
            args.custom_program_args[len(DEFAULT_CUSTOM_PROGRAM_ARGS) :],
            json_str_to_str_list,
        )
    parsed_args.custom_program_args = {
        **temp_custom_program_args,
        **parsed_args.custom_program_args,
    }

    # If an input file is not found throw error
    for md_input_file_path in parsed_args.md_input_file_paths:
        if not md_input_file_path.is_file():
            parsed_args.error = MdInputFileNotFoundException(md_input_file_path)
            return parsed_args

    # If an additional file directory is not found throw error
    for additional_file_dir in parsed_args.additional_file_dirs:
        if not additional_file_dir.is_dir():
            log.warning(
                f"Ignore {additional_file_dir=!r} because it's not a directory!"
            )
            parsed_args.additional_file_dirs.remove(additional_file_dir)

    if args.o_anki is not None:
        # Only automatically create an anki output file path if it was not none
        parsed_args.anki_output_file_path = (
            args.o_anki if f"{args.o_anki.name}".lower() != "none" else None
        )
    else:
        parsed_args.anki_output_file_path = parsed_args.md_input_file_paths[
            0
        ].parent.joinpath(f"{parsed_args.md_input_file_paths[0].stem}.apkg")

    if args.o_md is not None:
        parsed_args.md_output_file_paths = (
            [args.o_md] if f"{args.o_md.name}".lower() != "none" else None
        )
    elif args.o_md_dir:
        parsed_args.md_output_dir_path = args.o_md_dir
    else:
        parsed_args.md_output_file_paths = parsed_args.md_input_file_paths.copy()

    return parsed_args
