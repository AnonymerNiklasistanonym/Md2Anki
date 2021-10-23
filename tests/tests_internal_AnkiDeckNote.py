import sys
import re

sys.path.append("../src/md2anki/")
import md2anki


def test_regex_image_file():
    def check_regex_image_file(
        string="",
        expected_alt_texts=[],
        expected_source_paths=[],
        expected_widths=[],
        expected_heights=[],
    ):
        """Check if the recognized image file infos are as expected"""
        matches = re.findall(md2anki.REGEX_MD_IMAGE_FILE, string)
        assert len(matches) == len(
            expected_alt_texts
        ), f"{len(matches)=}{len(expected_alt_texts)=}"
        assert len(matches) == len(
            expected_source_paths
        ), f"{len(matches)=}{len(expected_source_paths)=}"
        assert len(matches) == len(
            expected_widths
        ), f"{len(matches)=}{len(expected_widths)=}"
        assert len(matches) == len(
            expected_heights
        ), f"{len(matches)=}{len(expected_heights)=}"
        for (
            match,
            expected_alt_text,
            expected_source_path,
            expected_width,
            expected_height,
        ) in zip(
            matches,
            expected_alt_texts,
            expected_source_paths,
            expected_widths,
            expected_heights,
        ):
            assert match[0] == expected_alt_text, f"{match[0]=}{expected_alt_text=}"
            assert (
                match[1] == expected_source_path
            ), f"{match[1]=}{expected_source_path=}"
            assert match[2] == expected_width, f"{match[2]=}{expected_width=}"
            assert match[3] == expected_height, f"{match[3]=}{expected_height=}"

    check_regex_image_file()
    check_regex_image_file(
        "![alt text](source path){ width=100px, height=200px }",
        expected_alt_texts=["alt text"],
        expected_source_paths=["source path"],
        expected_widths=["100px"],
        expected_heights=["200px"],
    )
    check_regex_image_file(
        "![alt text](source path){}",
        expected_alt_texts=["alt text"],
        expected_source_paths=["source path"],
        expected_widths=[""],
        expected_heights=[""],
    )
    check_regex_image_file(
        "![alt text](source path)",
        expected_alt_texts=["alt text"],
        expected_source_paths=["source path"],
        expected_widths=[""],
        expected_heights=[""],
    )
    check_regex_image_file(
        "![alt](./source.png){ height=20px }",
        expected_alt_texts=["alt"],
        expected_source_paths=["./source.png"],
        expected_widths=[""],
        expected_heights=["20px"],
    )
    check_regex_image_file(
        "![alt text](source path) ![alt text2](source path2)",
        expected_alt_texts=["alt text", "alt text2"],
        expected_source_paths=["source path", "source path2"],
        expected_widths=["", ""],
        expected_heights=["", ""],
    )


def test_regex_tag():
    def check_regex_tag(
        string="",
        expected_tag_list_strings=[],
    ):
        """Check if the recognized tag infos are as expected"""
        matches = re.findall(md2anki.REGEX_MD_TAG, string)
        assert len(matches) == len(
            expected_tag_list_strings
        ), f"{len(matches)=}{len(expected_tag_list_strings)=}"
        for match, expected_tag_list_string in zip(matches, expected_tag_list_strings):
            assert (
                match[0] == expected_tag_list_string
            ), f"{match[0]=}{expected_tag_list_string=}"

    check_regex_tag()
    check_regex_tag(
        "`{=:tag list string:=}`",
        expected_tag_list_strings=["tag string list"],
    )


def test_get_used_files():
    def check_used_files(
        expected_used_files=set(),
        question_string="",
        answer_string="",
    ):
        """Check if the recognized used files are the expected ones"""
        note = md2anki.AnkiDeckNote(
            question=question_string,
            answer=answer_string,
        )
        note_used_files = note.get_used_files()
        assert (
            len(note_used_files.difference(expected_used_files)) == 0
        ), f"{note_used_files=}{expected_used_files=}{note_used_files.difference(expected_used_files)=}"

    check_used_files()
    check_used_files(
        question_string="abc",
    )
    check_used_files(
        expected_used_files=set(["path1"]),
        question_string="![](path1)",
    )
    check_used_files(
        expected_used_files=set(["path1"]),
        question_string="hi\n![](path1)",
    )
    check_used_files(
        expected_used_files=set(["path1", "path2"]),
        question_string="hi\n![](path1)\n![](path2)",
    )
    # Check if answer strings are also searched
    check_used_files(
        expected_used_files=set(["path1", "path2"]),
        answer_string="![](path1) ![](path2)",
    )
    # Check if URLs are ignored
    check_used_files(
        expected_used_files=set(["path1", "path2"]),
        question_string="![](path1) ![](path2) ![https://www.google.com/image.png]",
    )


if __name__ == "__main__":
    test_regex_image_file()
    test_get_used_files()
    print("Everything passed [internal AnkiDeckNote]")
