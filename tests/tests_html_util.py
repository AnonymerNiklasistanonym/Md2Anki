#!/usr/bin/env python3

# Internal packages
import unittest
import sys
from pathlib import Path
from typing import List, Tuple

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.html_util import fix_inline_code_p_tags


class TestFixInlineCodePTags(unittest.TestCase):
    def setUp(self):
        self.html_content_list: List[str] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        test_data: List[Tuple[str, str]] = [
            ("", ""),
            ("<p>Test</p>", "<p>Test</p>"),
            (
                '<div class="highlight_inline">Code</div>',
                '<div class="highlight_inline">Code</div>',
            ),
            (
                '<p>Test</p><div class="highlight_inline">Code</div><p>Test 2</p>',
                '<p class="highlight_inline_next">Test</p><div class="highlight_inline">Code</div><p>Test 2</p>',
            ),
        ]

        for test_input, test_expected in test_data:
            self.html_content_list.append(test_input)
            self.results.append(fix_inline_code_p_tags(test_input))
            self.expected.append(test_expected)

    def test_updated_html_same(self):
        for html_content, result, expected in zip(
            self.html_content_list, self.results, self.expected
        ):
            with self.subTest(html_content=html_content):
                self.assertEqual(
                    result,
                    expected,
                    f"Check if updated html {result=}=={expected=}",
                )
