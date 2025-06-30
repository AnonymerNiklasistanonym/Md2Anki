#!/usr/bin/env python3

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Final

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.joinpath("src")))

from md2anki.cli import get_argument_parser
from md2anki.info.general import (
    MD2ANKI_NAME,
    MD2ANKI_DESCRIPTION,
)

md_comment: Final = ("[//]: <> (", ")")
md_comment_begin_end: Final = ("BEGIN: ", "END: ")
md_code_block: Final = ("````", "````")

ROOT_DIR_FILE_PATH: Final = Path(__file__).parent
README_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath("README.md")
EXAMPLE_BASIC_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath(
    "examples", "basic_example.md"
)
EXAMPLE_SUBDECK_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath(
    "examples", "subdeck_example.md"
)
EXAMPLE_FILL_IN_THE_BLANK_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath(
    "examples", "fill_in_the_blank_example_type_cloze.md"
)
EXAMPLE_MULTIPLE_TYPES_FILE_PATH: Final = ROOT_DIR_FILE_PATH.joinpath(
    "examples", "multiple_card_types_example.md"
)


def create_md_content(section_id: str, old_content: str) -> str:
    out: str = (
        md_comment[0] + md_comment_begin_end[0] + section_id + md_comment[1] + "\n\n"
    )
    if section_id == "HEADER":
        out += f"# {MD2ANKI_NAME}\n\n{MD2ANKI_DESCRIPTION}\n"
    elif section_id == "EXAMPLES":
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_BASIC_FILE_PATH, "r") as example_basic:
            out += example_basic.read()
        out += f"{md_code_block[1]}\n\n"
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_SUBDECK_FILE_PATH, "r") as example_subdeck:
            out += example_subdeck.read()
        out += f"{md_code_block[1]}\n"
    elif section_id == "EXAMPLE_CLOZE":
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_FILL_IN_THE_BLANK_FILE_PATH, "r") as example_cloze:
            out += example_cloze.read()
        out += f"{md_code_block[1]}\n"
    elif section_id == "EXAMPLE_MULTIPLE_TYPES":
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_MULTIPLE_TYPES_FILE_PATH, "r") as example_multi_types:
            out += example_multi_types.read()
        out += f"{md_code_block[1]}\n"
    elif section_id == "USAGE":
        out += f"{md_code_block[0]}text\n"
        path = tempfile.mktemp(prefix=f"{MD2ANKI_NAME}_capture_help_")
        try:
            with open(path, "w") as tmp:
                get_argument_parser().print_help(file=tmp)
            with open(path, "r") as tmp:
                out += tmp.read()
        finally:
            Path(path).unlink()
        out += f"{md_code_block[1]}\n"
    else:
        raise RuntimeError(f"Unsupported md content creation id ({section_id=})")
    return (
        out
        + "\n"
        + md_comment[0]
        + md_comment_begin_end[1]
        + section_id
        + md_comment[1]
        + "\n"
    )


def update_md_content(md_content: List[str]) -> str:
    out: str = ""
    current_comment: Optional[Tuple[str, str]] = None
    for line in md_content:
        stripped_line = line.strip()
        if stripped_line.startswith(md_comment[0]) and stripped_line.endswith(
            md_comment[1]
        ):
            comment_content = stripped_line[len(md_comment[0]) : -len(md_comment[1])]
            if comment_content.startswith(md_comment_begin_end[0]):
                if current_comment is not None:
                    raise RuntimeError(
                        f"Current comment was never ended [new] ({current_comment=})"
                    )
                current_comment = comment_content[len(md_comment_begin_end[0]) :], ""
                continue
            elif comment_content.startswith(md_comment_begin_end[1]):
                # Evaluate current comment
                if current_comment is not None:
                    out += create_md_content(current_comment[0], current_comment[1])
                    current_comment = None
                    continue
                else:
                    raise RuntimeError(
                        f"Found comment end line but no comment was found ({line=}, {current_comment=})"
                    )
        if current_comment is not None:
            current_comment = current_comment[0], current_comment[1] + line
        else:
            out += line
    if current_comment is not None:
        raise RuntimeError(
            f"Current comment was never ended [eof] ({current_comment=})"
        )
    return out


# Main method
if __name__ == "__main__":
    columns = shutil.get_terminal_size().columns
    print(f"Terminal width: {columns} columns (recommended 90)")

    with open(README_FILE_PATH, "r") as input_file:
        md_content_input = input_file.readlines()
    md_content_output = update_md_content(md_content_input)
    with open(README_FILE_PATH, "w") as output_file:
        output_file.write(md_content_output)
