import sys
import unittest
from os.path import dirname, join
from typing import Set, List, Tuple

# Append the module path for md2anki
sys.path.append(join(dirname(__file__), "..", "src"))

from md2anki.subprocess import evaluate_code, SubprocessPrograms


class TestEvaluateCode(unittest.TestCase):
    def setUp(self):
        self.code: List[Tuple[SubprocessPrograms, str]] = list()
        self.results: List[str] = list()
        self.expected: List[str] = list()

        test_data: List[Tuple[str, SubprocessPrograms, str]] = [
            ("", SubprocessPrograms.PYTHON, ""),
            ('print("Hello world!")', SubprocessPrograms.PYTHON, "Hello world!\n"),
            (
                "a = 42\n" 'print(f"The answer is {a}")',
                SubprocessPrograms.PYTHON,
                "The answer is 42\n",
            ),
            ("", SubprocessPrograms.JAVASCRIPT, ""),
            (
                'console.log("Hello world!")',
                SubprocessPrograms.JAVASCRIPT,
                "Hello world!\n",
            ),
            (
                "const a = 42\n" "console.log(`The answer is ${a}`)",
                SubprocessPrograms.JAVASCRIPT,
                "The answer is 42\n",
            ),
            (
                'let message: string = "Hello world!"\nconsole.log(message)',
                SubprocessPrograms.TYPESCRIPT,
                "Hello world!\n",
            ),
            (
                "#include<stdio.h>\n"
                "int main() {\n"
                '	printf("Hello world!\\n");\n'
                "	return 0;\n"
                "}",
                SubprocessPrograms.C,
                "Hello world!\n",
            ),
            (
                "#include <iostream>\n"
                "int main() {\n"
                '	std::cout << "Hello world!" << std::endl;\n'
                "	return 0;\n"
                "}",
                SubprocessPrograms.CPP,
                "Hello world!\n",
            ),
        ]

        for test_input, test_program, test_expected in test_data:
            self.code.append((test_program, test_input))
            self.results.append(evaluate_code(test_program, test_input))
            self.expected.append(test_expected)

    def test_evaluated_code_output_matches(self):
        for (language, code), result, expected in zip(
            self.code, self.results, self.expected
        ):
            with self.subTest(language=language, code=code):
                self.assertEqual(
                    result, expected, f"Check if output {result=}=={expected=}"
                )
