import io
import os
import sys
import tempfile
from typing import Optional, Tuple, List

# Append the module path for md2anki
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from md2anki.cli import get_argument_parser
from md2anki.info import (
    md2anki_name,
    md2anki_description,
)

md_comment = ("[//]: <> (", ")")
md_comment_begin_end = ("BEGIN: ", "END: ")
md_code_block = ("```", "```")

ROOT_DIR_FILE_PATH = os.path.dirname(__file__)
README_FILE_PATH = os.path.join(ROOT_DIR_FILE_PATH, "README.md")
EXAMPLE_BASIC_FILE_PATH = os.path.join(
    ROOT_DIR_FILE_PATH, "examples", "basic_example.md"
)
EXAMPLE_SUBDECK_FILE_PATH = os.path.join(
    ROOT_DIR_FILE_PATH, "examples", "subdeck_example.md"
)


def create_md_content(id: str, old_content: str) -> str:
    out: str = md_comment[0] + md_comment_begin_end[0] + id + md_comment[1] + "\n\n"
    if id == "HEADER":
        out += f"# {md2anki_name}\n\n{md2anki_description}\n"
    elif id == "EXAMPLES":
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_BASIC_FILE_PATH, "r") as example_basic:
            out += example_basic.read()
        out += f"{md_code_block[1]}\n\n"
        out += f"{md_code_block[0]}markdown\n"
        with open(EXAMPLE_SUBDECK_FILE_PATH, "r") as example_subdeck:
            out += example_subdeck.read()
        out += f"{md_code_block[1]}\n"
    elif id == "USAGE":
        out += f"{md_code_block[0]}text\n"
        path = tempfile.mktemp(prefix=f"{md2anki_name}_capture_help_")
        try:
            with open(path, "w") as tmp:
                get_argument_parser().print_help(file=tmp)
            with open(path, "r") as tmp:
                out += tmp.read()
        finally:
            os.remove(path)
        out += f"{md_code_block[1]}\n"
    else:
        raise RuntimeError(f"Unsupported md content creation id ({id=})")
    return (
        out + "\n" + md_comment[0] + md_comment_begin_end[1] + id + md_comment[1] + "\n"
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
                out += create_md_content(current_comment[0], current_comment[1])
                current_comment = None
                continue
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
    with open(README_FILE_PATH, "r") as input_file:
        md_content_input = input_file.readlines()
    md_content_output = update_md_content(md_content_input)
    with open(README_FILE_PATH, "w") as output_file:
        output_file.write(md_content_output)
