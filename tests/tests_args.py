import sys
import io
from contextlib import redirect_stdout

sys.path.append("../")
import md2anki

def test_version():
    f = io.StringIO()
    with redirect_stdout(f):
        error_code = md2anki.main(["", "--version"])
    output = f.getvalue()
    assert error_code == 0
    assert len(output) > 0

def test_help():
    f = io.StringIO()
    with redirect_stdout(f):
        error_code = md2anki.main(["", "--help"])
    output = f.getvalue()
    assert error_code == 0
    assert len(output) > 0

if __name__ == "__main__":
    test_version()
    test_help()
    print("Everything passed [args]")
