from tests_anki_deck import test_regex_image_file, test_get_used_files
from tests_cli import test_cli_args

if __name__ == "__main__":
    test_cli_args()
    test_regex_image_file()
    test_get_used_files()
