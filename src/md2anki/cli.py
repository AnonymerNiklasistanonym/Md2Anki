import argparse
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Final, Tuple, TypeVar, Generic, Callable
import json

from md2anki.info import md2anki_version, md2anki_name
from md2anki.note_models import AnkiCardModelId
from md2anki.subprocess import DEFAULT_CUSTOM_PROGRAM


class MdInputFileNotFoundException(Exception):
    """Raised when a markdown input file is not found"""

    md_input_file_path: str

    def __init__(self, md_input_file_path: str):
        absolute_path = os.path.abspath(md_input_file_path)
        super().__init__(
            f"Markdown input file was not found ({md_input_file_path!r}, {absolute_path=})"
        )
        self.md_input_file_path = md_input_file_path


class AdditionalFileDirNotFoundException(Exception):
    """Raised when an additional file directory is not found"""

    additional_file_dir_path: str

    def __init__(self, additional_file_dir_path: str):
        absolute_path = os.path.abspath(additional_file_dir_path)
        super().__init__(
            f"Additional file directory was not found ({additional_file_dir_path!r}, {absolute_path=})"
        )
        self.additional_file_dir_path = additional_file_dir_path


@dataclass
class Md2AnkiArgs:
    """
    Contains all information of the md2anki command line arguments.
    """

    additional_file_dirs: List[str] = field(default_factory=lambda: list())
    """Additional file directories for external file references (i.e. images)."""
    anki_card_model: AnkiCardModelId = AnkiCardModelId.DEFAULT
    """Anki card model."""
    md_input_file_paths: List[str] = field(default_factory=lambda: list())
    """The markdown input file paths."""
    md_output_file_paths: Optional[List[str]] = None
    """The optional output file paths of the updated markdown files (i.e. with added IDs)."""
    md_output_dir_path: Optional[str] = None
    """The optional output dir path of the updated markdown files (i.e. with added IDs)."""
    anki_output_file_path: Optional[str] = None
    """The output file path of the anki deck output file."""
    backup_output_dir_path: Optional[str] = None
    """The output dir path of the backup of the anki deck."""
    pdf_output_file_path: Optional[str] = None
    """The output file path of the anki deck."""
    md_heading_depth: int = 1
    """The default heading depth for the anki deck heading (increases for each subdeck/question by 1)."""
    custom_program: Dict[str, List[str]] = field(default_factory=lambda: dict())
    """Custom programs for languages used for code evaluation."""
    custom_program_args: Dict[str, List[List[str]]] = field(
        default_factory=lambda: dict()
    )
    """Custom program args for languages used for code evaluation."""

    debug = False
    """Enable debugging."""
    error: Optional[
        MdInputFileNotFoundException | AdditionalFileDirNotFoundException
    ] = None
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
    for key, values in DEFAULT_CUSTOM_PROGRAM.items()
    for program, program_args in values
]
DEFAULT_CUSTOM_PROGRAM_ARGS: Final = [
    (key, json.dumps(program_args))
    for key, values in DEFAULT_CUSTOM_PROGRAM.items()
    for program, program_args in values
]


def str_to_str(a: str) -> str:
    return a


def json_str_to_str_list(a: str) -> List[str]:
    possible_list: List[str] = json.loads(a)
    if not all(isinstance(elem, str) for elem in possible_list):
        raise RuntimeError(
            f"Custom program args need to be a JSON string list ({possible_list!r})"
        )
    return possible_list


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=md2anki_name,
        description="Create an anki deck file (.apkg) from one or more Markdown documents. "
        "If no custom output path is given the file name of the document (+ .apkg) is used.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {md2anki_version}"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug output"
    )
    parser.add_argument(
        "-anki-model",
        type=AnkiCardModelId,
        default=AnkiCardModelId.DEFAULT,
        choices=list(AnkiCardModelId),
        metavar="MODEL_ID",
        help=f"custom anki card model (%(choices)s)",
    )
    parser.add_argument(
        "-o-anki",
        metavar="APKG_FILE",
        help="custom anki deck (.apkg) output file path [if not given: md input file "
        "name + .apkg]",
    )
    parser.add_argument(
        "-o-md",
        metavar="MD_FILE",
        help="custom updated (and merged if multiple input files) Markdown (.md) output file path for all input files",
    )
    parser.add_argument(
        "-o-md-dir",
        metavar="MD_DIR",
        help="custom output directory for all updated Markdown (.md) input files",
    )
    parser.add_argument(
        "-o-backup-dir",
        metavar="BACKUP_DIR",
        help="create a backup of the anki deck (i.e. merges input files and copies external files) in a directory",
    )
    parser.add_argument(
        "-o-pdf",
        metavar="PDF_FILE",
        help="create a PDF (.pdf) file of the anki deck (i.e. merges input files and removes IDs)",
    )
    parser.add_argument(
        "-file-dir",
        action="extend",
        default=[],
        nargs="*",
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
        nargs=2,
        action="append",
        type=str,
        default=DEFAULT_CUSTOM_PROGRAMS,
        help="use custom program for code evaluation",
    )
    parser.add_argument(
        "-custom-program-args",
        metavar=("language", "program-args"),
        nargs=2,
        action="append",
        type=str,
        default=DEFAULT_CUSTOM_PROGRAM_ARGS,
        help="use custom program args for code evaluation",
    )
    parser.add_argument(
        "md_input_files",
        metavar="MD_INPUT_FILE",
        nargs="+",
        help="Markdown (.md) input file that contains anki deck notes",
    )
    return parser


def parse_cli_args(cli_args: List[str]) -> Md2AnkiArgs:
    """
    Parse the supplied CLI arguments.

    @return: Object that contains all parsed information.
    """
    parser = get_argument_parser()
    args = parser.parse_args(cli_args)
    parsed_args = Md2AnkiArgs()

    if args.debug:
        parsed_args.debug = True
        print("> Debugging was enabled")
        print(f"> CLI args: {cli_args}")
        print(f"> Argparse args: {args}")

    parsed_args.additional_file_dirs = args.file_dir
    parsed_args.anki_card_model = args.anki_model
    parsed_args.md_heading_depth = args.md_heading_depth
    parsed_args.md_input_file_paths = args.md_input_files
    parsed_args.backup_output_dir_path = args.o_backup_dir
    parsed_args.pdf_output_file_path = args.o_pdf

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
        if not os.path.isfile(md_input_file_path):
            parsed_args.error = MdInputFileNotFoundException(md_input_file_path)
            return parsed_args

    # If an additional file directory is not found throw error
    for additional_file_dir in parsed_args.additional_file_dirs:
        if not os.path.isdir(additional_file_dir):
            parsed_args.error = AdditionalFileDirNotFoundException(additional_file_dir)
            return parsed_args

    parsed_args.anki_output_file_path = (
        args.o_anki
        if args.o_anki
        else os.path.join(
            os.path.dirname(parsed_args.md_input_file_paths[0]),
            f"{os.path.splitext(os.path.basename(parsed_args.md_input_file_paths[0]))[0]}.apkg",
        )
    )

    if args.o_md:
        parsed_args.md_output_file_paths = [args.o_md]
    elif args.o_md_dir:
        parsed_args.md_output_dir_path = args.o_md_dir
    else:
        parsed_args.md_output_file_paths = parsed_args.md_input_file_paths.copy()

    return parsed_args
