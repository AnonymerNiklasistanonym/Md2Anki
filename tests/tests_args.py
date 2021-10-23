import sys
import io
from contextlib import redirect_stdout

sys.path.append("../src/md2anki/")
import md2anki


def test_version():
    assert md2anki.parse_cli_args(["--version"]).show_version == True
    f = io.StringIO()
    with redirect_stdout(f):
        error_code = md2anki.main_method(md2anki.Md2AnkiArgs(show_version=True))
    output = f.getvalue()
    assert error_code == 0
    assert len(output) > 0


def test_help():
    assert md2anki.parse_cli_args(["--help"]).show_help == True
    f = io.StringIO()
    with redirect_stdout(f):
        error_code = md2anki.main_method(md2anki.Md2AnkiArgs(show_help=True))
    output = f.getvalue()
    assert error_code == 0
    assert len(output) > 0


if __name__ == "__main__":
    test_version()
    test_help()
    print("Everything passed [args]")
