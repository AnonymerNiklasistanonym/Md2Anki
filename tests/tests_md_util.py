#!/usr/bin/env python3

# Internal packages
import unittest
import sys
from os import name
from pathlib import Path
from typing import Set, List, Tuple, Callable, Optional, Final
from urllib.parse import urlparse, ParseResult

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.md_util import (
    md_get_used_files,
    md_get_used_md2anki_tags,
    md_update_local_filepaths,
    md_update_code_parts,
    md_update_images,
    md_update_math_sections,
)


class TestMdGetUsedFiles(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[Set[Path | ParseResult]] = list()
        self.expected: List[Set[Path | ParseResult]] = list()

        test_data: List[Tuple[str, Set[Path | ParseResult]]] = [
            ("", set()),
            ("![](path1)", {Path("path1")}),
            ("hi\n![](path1)", {Path("path1")}),
            ("hi\n![](path1)\n![](path2)", {Path("path1"), Path("path2")}),
            ("![](path1) ![](path2)", {Path("path1"), Path("path2")}),
            (
                "![](path1) ![](path2) ![](https://www.google.com/image.png)",
                {
                    Path("path1"),
                    Path("path2"),
                    urlparse("https://www.google.com/image.png"),
                },
            ),
        ]

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(md_get_used_files(test_input))
            self.expected.append(test_expected)

    def test_used_files_set_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertSetEqual(
                    result, expected, f"Check if used files {result=}=={expected=}"
                )


class TestMdUpdateLocalFilepaths(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        new_directory: Final = Path("new_dir")
        absolute_path: Final = Path(
            "C:\\Users\\user\\Documents\\Md2Anki\\abs_graph.svg"
            if name == "nt"
            else "/mnt/c/Users/user/Documents/Md2Anki/abs_graph.svg"
        )

        test_data: List[Tuple[str, Callable[[Path], str]]] = [
            ("", lambda x: ""),
            ("![](path1)", lambda x: f"![]({x.joinpath('path1')})"),
            (
                "![](path1) ![](path2) ![](https://www.google.com/image.png)",
                lambda x: f"![]({x.joinpath('path1')}) ![]({x.joinpath('path2')}) ![](https://www.google.com/image.png)",
            ),
            (
                f"Question with matplotlib graph\n\n![]({absolute_path})\n",
                lambda x: f"Question with matplotlib graph\n\n![]({x.joinpath('abs_graph.svg')})\n",
            ),
        ]

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(md_update_local_filepaths(test_input, new_directory))
            self.expected.append(test_expected(new_directory))

    def test_updated_filepaths_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if updated filepaths {result=}=={expected=}",
                )


class TestMdUpdateCodeParts(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        test_data: List[Tuple[str, str]] = [
            ("", ""),
            ("`text`", "`ctextd`"),
            ("a `text`{.python}", "a `ctextd`{a.pythonb}"),
            (
                "Format inline code `print('inline')`{.python} is also `supported`{.txt}",
                "Format inline code `cprint('inline')d`{a.pythonb} is also `csupportedd`{a.txtb}",
            ),
            (
                "abc\n```python\nprint('hi')\n```",
                "abc\n```apythonb\ncprint('hi')\nd```",
            ),
            (
                "code block indented:\n\n" "    ```python\n    print('hi')\n    ```",
                "code block indented:\n\n"
                "    ```apythonb\nc    print('hi')\n    d    e\n```",
            ),
        ]

        def update_code_part(
            code: str,
            code_block: bool,
            language: Optional[str],
            code_block_indent: Optional[str],
        ):
            if language is not None:
                language = f"a{language}b"
            code = f"c{code}d"
            indent = f"{code_block_indent}e\n" if code_block_indent is not None else ""
            if code_block:
                return f"{code_block_indent if len(indent) > 0 else ''}```{language}\n{code}{indent}```"
            else:
                return f"`{code}`" + (
                    ("{" + language + "}") if language is not None else ""
                )

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(md_update_code_parts(test_input, update_code_part))
            self.expected.append(test_expected)

    def test_updated_code_parts_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if updated code parts {result=}=={expected=}",
                )


class TestMdUpdateImages(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        test_data: List[Tuple[str, str]] = [
            (
                "![alt text](source path){ width=100px, height=200px }",
                "![aalt textb](csource pathd){ width=e100pxf, height=g200pxh }",
            ),
            ("![alt text](source path){}", "![aalt textb](csource pathd)"),
            ("![alt text](source path)", "![aalt textb](csource pathd)"),
            (
                "![alt](./source.png){ height=20px }",
                "![aaltb](c./source.pngd){ height=g20pxh }",
            ),
            (
                "![alt text](source path) ![alt text2](source path2)",
                "![aalt textb](csource pathd) ![aalt text2b](csource path2d)",
            ),
        ]

        def update_image(
            file_path: str,
            file_description: str,
            width: Optional[str],
            height: Optional[str],
        ):
            style: List[str] = list()
            style_str = ""
            if width is not None:
                style.append(f"width=e{width}f")
            if height is not None:
                style.append(f"height=g{height}h")
            if len(style) > 0:
                style_str = "{ " + ", ".join(style) + " }"
            return f"![a{file_description}b](c{file_path}d){style_str}"

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(
                md_update_images(
                    test_input,
                    update_image,
                )
            )
            self.expected.append(test_expected)

    def test_updated_images_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if updated code parts {result=}=={expected=}",
                )


class TestMdGetUsedMd2ankiTags(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[Set[str]] = list()
        self.expected: List[Set[str]] = list()

        test_data: List[Tuple[str, Set[str]]] = [
            ("", set()),
            ("`{=:tag list string:=}`", {"tag_list_string"}),
            ("`{=:tag_list_string:=}`", {"tag_list_string"}),
            ("`{=:tag1,tag2,tag3:=}`", {"tag1", "tag2", "tag3"}),
        ]

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(md_get_used_md2anki_tags(test_input))
            self.expected.append(test_expected)

    def test_used_md2anki_tags_set_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertSetEqual(
                    result,
                    expected,
                    f"Check if used md2anki tags {result=}=={expected=}",
                )


class TestMdUpdateMathSections(unittest.TestCase):
    def setUp(self):
        self.md_content_list: List[str] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        test_data: List[Tuple[str, str]] = [
            ("", ""),
            ("abc", "abc"),
            ("$ab$", "$aabb$"),
            ("$$cd$$", "$$ccdd$$"),
        ]

        def update_math_section(math_section: str, block: bool):
            if block:
                return f"$$c{math_section}d$$"
            else:
                return f"$a{math_section}b$"

        for test_input, test_expected in test_data:
            self.md_content_list.append(test_input)
            self.results.append(
                md_update_math_sections(
                    test_input,
                    update_math_section,
                )
            )
            self.expected.append(test_expected)

    def test_updated_math_sections_same(self):
        for md_content, result, expected in zip(
            self.md_content_list, self.results, self.expected
        ):
            with self.subTest(md_content=md_content):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if updated math section {result=}=={expected=}",
                )
