import argparse
from enum import Enum
import os
from dataclasses import dataclass, field
from typing import Optional, List

from md2anki.info import md2anki_version, md2anki_name


class AnkiCardModelId(Enum):
    ONLINE = "md2anki_online"
    OFFLINE = "md2anki_offline"
    TYPE_ANSWER = "md2anki_type_answer"

    def __str__(self):
        return self.value


@dataclass
class Md2AnkiArgs:
    """
    Contains all information of the md2anki command line arguments.
    """

    additional_file_dirs: List[str] = field(default_factory=lambda: list())
    """Additional file directories for external file references (i.e. images)."""
    anki_card_model: Optional[AnkiCardModelId] = None
    """Anki card model."""
    md_input_file_paths: List[str] = field(default_factory=lambda: list())
    """The markdown input file paths."""
    md_output_file_path: Optional[str] = None
    """The optional output file path of the updated markdown file (i.e. with added IDs)."""
    md_output_dir_path: Optional[str] = None
    """The optional output dir path of the updated markdown files (i.e. with added IDs)."""
    anki_output_file_path: Optional[str] = None
    """The output file path of the anki deck output file."""
    backup_output_dir_path: Optional[str] = None
    """The output dir path of the backup of the anki deck."""
    md_heading_depth: int = 1
    """The default heading depth for the anki deck heading (increases for each subdeck/question by 1)."""

    debug: bool = False
    """Enable debugging."""
    error: Optional[str] = None
    """Error message in case there was an error parsing CLI args."""


def parse_cli_args(cli_args: List[str]) -> Md2AnkiArgs:
    """
    Parse the supplied CLI arguments.

    @return: Object that contains all parsed information.
    """
    parser = argparse.ArgumentParser(
        prog=md2anki_name,
        description="Create an anki deck file (.apkg) from one or more Markdown documents. "
        "If no custom output path is given the file name of the document (+ .apkg) is used.",
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
        default=AnkiCardModelId.ONLINE,
        choices=list(AnkiCardModelId),
        metavar="MODEL_ID",
        help=f"custom anki card model (%(choices)s) [default: %(default)s]",
    )
    parser.add_argument(
        "-o-anki", metavar="APKG_FILE", help="custom anki deck (.apkg) output file path"
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
        "-file-dir",
        action="extend",
        default=[],
        nargs="*",
        help="add directories that should be checked for referenced files (like relative path images)",
    )

    def check_heading_depth(x: str) -> int:
        x = int(x)
        if x < 1:
            raise argparse.ArgumentTypeError("Minimum heading depth is 1")
        return x

    parser.add_argument(
        "-md-heading-depth",
        metavar="HEADING_DEPTH",
        type=check_heading_depth,
        default=1,
        help="use a custom Markdown heading depth (>=1) [default: %(default)s]",
    )
    parser.add_argument(
        "md_input_files",
        metavar="MD_INPUT_FILE",
        nargs="+",
        help="Markdown (.md) input file that contains anki deck notes",
    )
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

    # If an input file is not found throw error
    for md_input_file_path in parsed_args.md_input_file_paths:
        if not os.path.isfile(md_input_file_path):
            absolute_path = os.path.abspath(md_input_file_path)
            parsed_args.error = f"Markdown input file was not found ({md_input_file_path}, {absolute_path=})"
            return parsed_args

    # If an additional file directory is not found throw error
    for additional_file_dir in parsed_args.additional_file_dirs:
        if not os.path.isdir(additional_file_dir):
            absolute_path = os.path.abspath(additional_file_dir)
            parsed_args.error = f"Additional file directory was not found ({additional_file_dir}, {absolute_path=})"
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
        parsed_args.md_output_file_path = args.o_md
    elif len(parsed_args.md_input_file_paths) == 1:
        parsed_args.md_output_file_path = parsed_args.md_input_file_paths[0]

    if args.o_md_dir:
        parsed_args.md_output_dir_path = args.o_md_dir
    elif len(parsed_args.md_input_file_paths) > 1:
        parsed_args.md_output_dir_path = os.path.join(
            os.path.dirname(parsed_args.md_input_file_paths[0]),
            f"{os.path.splitext(os.path.basename(parsed_args.md_input_file_paths[0]))[0]}",
        )

    return parsed_args
