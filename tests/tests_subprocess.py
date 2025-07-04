#!/usr/bin/env python3

# Internal packages
import unittest
import uuid
from random import choices
import sys
from pathlib import Path
import string
import tempfile

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

# Local modules
from md2anki.subprocess import (
    run_subprocess,
    ProgramNotFoundException,
    ProgramExitedWithWarningsException,
)


class TestRunSubprocess(unittest.TestCase):
    def test_run_successful_command(self):
        output = run_subprocess(sys.executable, args=["-c", "print('hello')"])
        self.assertEqual(output, "hello\n")
        output = run_subprocess(sys.executable, args=["-c", "import sys; sys.exit(0)"])
        self.assertEqual(output, "")

    @unittest.skipUnless(sys.platform.startswith("linux"), "Only runs on Linux")
    def test_run_successful_command_linux_only(self):
        output = run_subprocess("echo", args=["hello"])
        self.assertEqual(output, "hello\n")
        output = run_subprocess("true", args=[])
        self.assertEqual(output, "")

    def test_run_fail_command(self):
        with self.assertRaises(ProgramExitedWithWarningsException) as cm:
            run_subprocess(sys.executable, args=["-c", "import sys; sys.exit(1)"])
        self.assertIn("Subprocess exited with warnings", str(cm.exception))

    @unittest.skipUnless(sys.platform.startswith("linux"), "Only runs on Linux")
    def test_run_fail_command_linux_only(self):
        with self.assertRaises(ProgramExitedWithWarningsException) as cm:
            run_subprocess("false", args=["fail"])
        self.assertIn("Subprocess exited with warnings", str(cm.exception))

    def test_run_fail_command_not_found(self):
        with self.assertRaises(ProgramNotFoundException) as cm:
            run_subprocess(sys.executable + "sdsadsadsad")
        self.assertIn("could not be found", str(cm.exception))

    def test_additional_env(self):
        random_value = "".join(choices(string.ascii_letters + string.digits, k=10))
        output = run_subprocess(
            sys.executable,
            args=["-c", "import os; print(os.getenv('MY_RANDOM_VAR'))"],
            additional_env={"MY_RANDOM_VAR": random_value},
        )
        self.assertEqual(output.strip(), random_value)

    def test_cwd(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            filename = f"testfile_{uuid.uuid4().hex}.txt"
            run_subprocess(
                sys.executable,
                args=["-c", f"with open('{filename}', 'w') as f: f.write('hello')"],
                cwd=tmp_path,
            )
            created_file = tmp_path / filename
            self.assertTrue(created_file.exists(), f"{filename} was not created")
            self.assertEqual(created_file.read_text(), "hello")
