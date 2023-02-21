#!/usr/bin/env python3

# Internal packages
import unittest
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.cli import (
    convert_list_to_dict_merged,
    DEFAULT_CUSTOM_PROGRAMS,
    DEFAULT_CUSTOM_PROGRAM_ARGS,
    str_to_str,
    json_str_to_str_list,
)
from md2anki.info import md2anki_name
from md2anki.subprocess import subprocess_evaluate_code


class TestEvaluateCode(unittest.TestCase):
    def setUp(self):
        self.code: List[Tuple[str, str]] = list()
        self.results: List[Tuple[List[str], List[Path]]] = list()
        self.expected: List[Tuple[Optional[List[str]], List[Path]]] = list()

        test_data: List[Tuple[str, str, Tuple[Optional[List[str]], List[Path]]]] = [
            ("", "py", ([""], [])),
            (
                'print("Hello world!")',
                "py",
                (["Hello world!\n"], []),
            ),
            (
                "a = 42\n" 'print(f"The answer is {a}")',
                "py",
                (["The answer is 42\n"], []),
            ),
            ("", "js", ([""], [])),
            (
                'console.log("Hello world!")',
                "js",
                (["Hello world!\n"], []),
            ),
            (
                "const a = 42\n" "console.log(`The answer is ${a}`)",
                "js",
                (["The answer is 42\n"], []),
            ),
            (
                'let message: string = "Hello world!"\nconsole.log(message)',
                "ts",
                (["Hello world!\n"], []),
            ),
            (
                "#include<stdio.h>\n"
                "int main() {\n"
                '	printf("Hello world!\\n");\n'
                "	return 0;\n"
                "}",
                "c",
                (["", "Hello world!\n"], []),
            ),
            (
                "#include <iostream>\n"
                "int main() {\n"
                '	std::cout << "Hello world!" << std::endl;\n'
                "	return 0;\n"
                "}",
                "cpp",
                (["", "Hello world!\n"], []),
            ),
            (
                "import numpy as np\n"
                "import matplotlib.pyplot as plt\n"
                "\n"
                "def m_t_exp_wachstum(c, k, t):\n"
                "    return c * np.exp(k * t)\n"
                "\n"
                "def m_t_exp_wachstum_abl(c, k, t):\n"
                "    return k * m_t_exp_wachstum(c, k, t)\n"
                "\n"
                "x = np.linspace(0, 200)\n"
                "y_m_t = m_t_exp_wachstum(c=30, k=-0.04, t=x)\n"
                "y_m_t_abl = m_t_exp_wachstum_abl(c=30, k=-0.04, t=x)\n"
                "\n"
                "plt.plot(x, y_m_t, '-b', label='$M_{vereinfacht}(t)$')\n"
                "plt.xlabel('$t$ (in min)')\n"
                "plt.legend(loc='upper right')\n"
                "plt.savefig('graph_3.svg')\n",
                "py",
                ([""], [Path('graph_3.svg')]),
            ),
            (
                "\\documentclass[tikz,border=10pt]{standalone}\n"
                "\\usetikzlibrary{positioning}\n"
                "\\tikzset{\n"
                "    main\n"
                "    node/.style={circle,fill=none,draw,minimum size=1cm,inner sep=0pt}\n"
                "}\n"
                "\\begin{document}\n"
                "\\begin{tikzpicture}\n"
                "    \\node[main node] [                               ] (0)  {$A$};\n"
                "    \\node[main node] [right       = 2cm          of 0] (1)  {$B$};\n"
                "\n"
                "     \\path[draw,thick]\n"
                "     (0) edge node {} (1)\n"
                "     ;\n"
                "\\end{tikzpicture}\n"
                "\\end{document}\n",
                "latex",
                (None, [Path('code.svg')]),
            ),
        ]

        for test_input, test_program, test_expected in test_data:
            self.code.append((test_program, test_input))
            dir_dynamic_files = Path(
                tempfile.mkdtemp(prefix=f"{md2anki_name}_tmp_file_test_subprocess_")
            )
            self.results.append(
                subprocess_evaluate_code(
                    test_program,
                    test_input,
                    custom_program=convert_list_to_dict_merged(
                        DEFAULT_CUSTOM_PROGRAMS, str_to_str
                    ),
                    custom_program_args=convert_list_to_dict_merged(
                        DEFAULT_CUSTOM_PROGRAM_ARGS, json_str_to_str_list
                    ),
                    dir_dynamic_files=dir_dynamic_files,
                )
            )
            shutil.rmtree(dir_dynamic_files)
            self.expected.append((test_expected[0], [dir_dynamic_files.joinpath(x) for x in test_expected[1]]))

    def test_evaluated_code_output_matches(self):
        for (language, code), result, expected in zip(
            self.code, self.results, self.expected
        ):
            with self.subTest(language=language, code=code):
                if expected[0] is not None:
                    self.assertEqual(
                        result[0], expected[0], f"Check if output stdout {result[0]=}=={expected[0]=}"
                    )
                self.assertEqual(
                    result[1], expected[1], f"Check if output image files {result[1]=}=={expected[1]=}"
                )
