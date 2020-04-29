#!/usr/bin/env python3

import os.path
import random
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, TextIO
from uuid import uuid4

import genanki

VERSION_MAJOR: int = 0
VERSION_MINOR: int = 0
VERSION_PATCH: int = 1

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CSS_GENERAL_FILE_PATH = os.path.join(CURRENT_DIR, 'stylesheet.css')
HIGHLIGHTJS_HTML_FILE_PATH = os.path.join(CURRENT_DIR, 'highlightJs_renderer.html')
HIGHLIGHTJS_SCRIPT_FILE_PATH = os.path.join(CURRENT_DIR, 'highlightJs_renderer.js')
KATEXT_FILE_HTML_PATH = os.path.join(CURRENT_DIR, 'kaTex_renderer.html')
KATEXT_FILE_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'kaTex_renderer.js')


def cli_help():
    print("$ python3 md2anki.py MD_FILE [OPTIONS]\n\n" +
          "Create an anki deck from a markdown document.\n\n" +
          "Options:\n" +
          "\t-d\t\t\t\tActivate debugging output\n" +
          "\t-o-anki FILE_PATH\t\tCustom anki deck output file path\n" +
          "\t-o-md FILE_PATH\t\t\tCustom markdown output file path\n" +
          "\t-additional-res-dir DIR_PATH\tCustom resource directory\n\n" +
          "Also supported are:\n" +
          "\t--help\n" +
          "\t--version")


def cli_version():
    print(f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}")


def create_unique_id() -> str:
    return str(uuid4())


def create_unique_id_int(length: int = 32) -> int:
    return random.getrandbits(length)


@dataclass
class AnkiDeckNote:
    """
    Contains all information of an anki deck note
    """
    question: str = ""
    """Question multi line string"""
    answer: str = ""
    """Answer multi line string"""
    category: Optional[str] = None
    """Optional category for note"""
    guid: str = create_unique_id()
    """Unique id of anki deck note"""
    files: List[str] = field(default_factory=lambda: set())
    """List of files to package into the deck"""

    def genanki_create_note(self, anki_card_model: genanki.Model,
                            additional_file_dirs_to_escape: Optional[List[str]] = None,
                            escape_unicode=True, markdown_to_anki_html=True) -> genanki.Note:
        if additional_file_dirs_to_escape is None:
            additional_file_dirs_to_escape = []
        temp_question = self.question
        temp_answer = self.answer

        for file_dir_to_escape in additional_file_dirs_to_escape:
            temp_question = temp_question.replace(f'"{file_dir_to_escape}{os.path.sep}', '"')
            temp_answer = temp_answer.replace(f'"{file_dir_to_escape}{os.path.sep}', '"')

        # Fix source code blocks
        regex_code_block = re.compile(r'```(.*?)\n([\S\s\n]+?)```', flags=re.MULTILINE)
        regex_code_block_replace = r'<pre><code class="\1">\2</code></pre>'

        temp_question = re.sub(regex_code_block, regex_code_block_replace, temp_question)
        temp_answer = re.sub(regex_code_block, regex_code_block_replace, temp_answer)

        # Fix multiline TeX commands (otherwise broken on Website)
        regex_math_block = re.compile(r'\$\$([\S\s\n]+?)\$\$', flags=re.MULTILINE)
        temp_question = re.sub(regex_math_block, lambda x: ' '.join(x.group().splitlines()), temp_question)
        temp_answer = re.sub(regex_math_block, lambda x: ' '.join(x.group().splitlines()), temp_answer)

        # TODO Extract files that this card requests

        if markdown_to_anki_html:
            temp_question = temp_question.replace('\n', '<br>').replace('\r', '')
            temp_answer = temp_answer.replace('\n', '<br>').replace('\r', '')

        if escape_unicode:
            temp_question = temp_question.encode('utf-8', 'xmlcharrefreplace') \
                .decode('utf-8') \
                .replace("Ä", "&Auml;").replace("ä", "&auml;") \
                .replace("Ö", "&Ouml;").replace("ö", "&ouml;") \
                .replace("Ü", "&Uuml;").replace("ü", "&uuml;") \
                .replace("ß", "&szlig;")
            temp_answer = temp_answer.encode('utf-8', 'xmlcharrefreplace') \
                .decode('utf-8') \
                .replace("Ä", "&Auml;").replace("ä", "&auml;") \
                .replace("Ö", "&Ouml;").replace("ö", "&ouml;") \
                .replace("Ü", "&Uuml;").replace("ü", "&uuml;") \
                .replace("ß", "&szlig;")

        return genanki.Note(guid=self.guid, model=anki_card_model, fields=[temp_question, temp_answer])

    def md_create_string(self, heading_level=2) -> str:
        newline_count_question = len(self.question.splitlines())
        question_header: str = self.question.splitlines()[0].rstrip()
        question_body: str
        if newline_count_question <= 1:
            question_body = ""
        else:
            question_body = f"\n\n{''.join(self.question.splitlines(keepends=True)[1:])}\n\n---"

        return f"{'#' * heading_level} {question_header} ({self.guid}){question_body}\n\n{self.answer}"


@dataclass
class AnkiModel:
    """
    Contains all information of an anki model (for anki notes of an anki deck)
    """
    name: str = ""
    """Model name"""
    description: str = ""
    """Model description"""
    css: str = ""
    """Style information (CSS code) for each anki note"""
    js: str = ""
    """Script information (JS code) for each anki note"""
    guid: int = create_unique_id_int()
    """Unique id of anki model"""
    template_card_question: str = '{{Question}}'
    """Card question text"""
    template_card_separator: str = '{{FrontSide}}<hr id="answer">'
    """Card separator text"""
    template_card_answer: str = '{{Answer}}'
    """Card answer text"""

    def genanki_create_model(self) -> genanki.Model:
        return genanki.Model(self.guid, self.description,
                             fields=[{'name': 'Question'}, {'name': 'Answer'}],
                             css=self.css,
                             templates=[{
                                 'name': self.name,
                                 'qfmt': self.js + self.template_card_question,
                                 'afmt': self.template_card_separator + self.template_card_answer,
                             }])


@dataclass
class AnkiDeck:
    """
    Contains all information of an anki deck
    """
    name: str = 'No name'
    """Name of the deck"""
    model: AnkiModel = AnkiModel()
    """Model of cards of anki deck"""
    guid: int = create_unique_id_int()
    """Unique id of anki deck"""
    notes: List[AnkiDeckNote] = field(default_factory=lambda: list())
    """List of anki notes"""
    additional_file_dirs: List[str] = field(default_factory=lambda: list())
    """List of additional file dirs that should be searched for missing files used in notes"""

    def genanki_create_deck(self, anki_card_model: genanki.Model,
                            additional_file_dirs_to_escape: Optional[List[str]] = None) -> genanki.Deck:
        temp_anki_deck = genanki.Deck(self.guid, self.name)
        for note in self.notes:
            temp_anki_deck.add_note(note.genanki_create_note(anki_card_model, additional_file_dirs_to_escape))
        return temp_anki_deck

    def genanki_write_deck_to_file(self, output_file_path: str):
        temp_genanki_anki_deck = self.genanki_create_deck(self.model.genanki_create_model(),
                                                          self.additional_file_dirs)
        temp_genanki_anki_deck_package = genanki.Package(temp_genanki_anki_deck)
        temp_genanki_anki_deck_package.media_files = []  # TODO Extract from notes
        temp_genanki_anki_deck_package.write_to_file(output_file_path)

    def md_write_deck_to_file(self, output_file_path: str):
        with open(output_file_path, 'w', encoding="utf-8") as file:
            file.write(f"# {self.name} ({self.guid})")
            for note in self.notes:
                file.write('\n\n')
                file.write(note.md_create_string())
            file.write('\n')


def create_katex_highlightjs_anki_deck_model() -> AnkiModel:
    # > Get CSS markup code
    with open(CSS_GENERAL_FILE_PATH, 'r') as cssFile:
        css_code = cssFile.read()
    # Get source code HTML/JS highlighting code
    with open(HIGHLIGHTJS_HTML_FILE_PATH, 'r') as highlightjsHtmlFile:
        highlightjs_template_code = highlightjsHtmlFile.read()
    with open(HIGHLIGHTJS_SCRIPT_FILE_PATH, 'r') as highlightjsScriptFile:
        highlightjs_template_code += f"<script>\n{highlightjsScriptFile.read()}</script>"
    # Get LaTeX math code HTML/JS render code
    with open(KATEXT_FILE_HTML_PATH, 'r') as kaTexHtmlFile:
        katex_template_code = kaTexHtmlFile.read()
    with open(KATEXT_FILE_SCRIPT_PATH, 'r') as kaTeXScriptFile:
        katex_template_code += f"<script>\n{kaTeXScriptFile.read()}</script>"

    return AnkiModel(guid=999999001,
                     name='Md2Anki card (KaTeX, HighlightJs)',
                     description='Card with KaTeX and HighlightJs support',
                     css=css_code,
                     js=highlightjs_template_code + katex_template_code)


class ParseSectionState(Enum):
    NONE = 'NONE',
    HEADER = 'HEADER',
    QUESTION_HEADER = 'QUESTION_HEADER',
    QUESTION_ANSWER_SEPERATOR = 'QUESTION_ANSWER_SEPERATOR',
    ANSWER = 'ANSWER',


def parse_header(md_file_line: str, debug_this=False) -> Optional[AnkiDeck]:
    regex_header = re.compile(r'^# (.+?)\s+\((\d+)\)\s+$')
    regex_header_without_id = re.compile(r'^# (.+?)\s+$')

    regex_header_match = regex_header.match(md_file_line)
    regex_header_without_id_match = regex_header_without_id.match(md_file_line)

    if regex_header_match is not None:
        temp_anki_deck = AnkiDeck(name=regex_header_match.group(1), guid=int(regex_header_match.group(2)))
        if debug_this:
            print(f"> Found header (name={temp_anki_deck.name},guid={temp_anki_deck.guid})")
        return temp_anki_deck
    elif regex_header_without_id_match is not None:
        temp_anki_deck = AnkiDeck(name=regex_header_without_id_match.group(1), guid=create_unique_id_int())
        if debug_this:
            print(f"> Found header without id (name={temp_anki_deck.name})")
        return temp_anki_deck


def parse_question_header(md_file_line: str, debug_this=False) -> Optional[AnkiDeckNote]:
    regex_question_header = re.compile(r'^## (.+?)\s+\((.+?)\)\s+$')
    regex_question_header_without_id = re.compile(r'^## (.+?)\s+$')

    regex_question_header_match = regex_question_header.match(md_file_line)
    regex_question_header_without_id_match = regex_question_header_without_id.match(md_file_line)

    if regex_question_header_match is not None:
        temp_anki_note = AnkiDeckNote(question=regex_question_header_match.group(1),
                                      guid=regex_question_header_match.group(2))
        if debug_this:
            print(f"> Found question header (question={temp_anki_note.question},id={temp_anki_note.guid})")
        return temp_anki_note
    elif regex_question_header_without_id_match is not None:
        temp_anki_note = AnkiDeckNote(question=regex_question_header_without_id_match.group(1),
                                      guid=create_unique_id())
        if debug_this:
            print(f"> Found question header without id (question={temp_anki_note.question})")
        return temp_anki_note


def parse_md_file_to_anki_deck(text_file: TextIO, debug=False) -> AnkiDeck:
    empty_lines: int = 0
    parse_state: ParseSectionState = ParseSectionState.NONE

    temp_anki_deck: AnkiDeck = AnkiDeck()
    temp_anki_note: AnkiDeckNote = AnkiDeckNote()

    for line in text_file:

        # Strip line from newlines
        line_stripped = line.strip()

        if debug:
            print(f"line='{line_stripped}' state={parse_state.name} empty_lines={empty_lines}")

        # Skip empty lines
        if len(line_stripped) == 0:
            empty_lines += 1
            if debug:
                print(f"> Found empty line")
            continue

        # Parse states
        if parse_state == ParseSectionState.NONE:
            temp_optional_anki_deck = parse_header(line, debug_this=debug)
            if temp_optional_anki_deck is not None:
                temp_anki_deck = temp_optional_anki_deck
                parse_state = ParseSectionState.HEADER
                empty_lines = 0
            else:
                print(f"WARNING: Header was not found: '{line_stripped}'")
        elif parse_state == ParseSectionState.HEADER:
            # Header was read -> expect question header
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_note = temp_optional_anki_note
                parse_state = ParseSectionState.QUESTION_HEADER
                empty_lines = 0
            else:
                print(f"WARNING: Question header was not found: '{line_stripped}'")
        elif parse_state == ParseSectionState.QUESTION_HEADER:
            # Question header was read -> expect question block or answer block
            # (if separator is found move content from answer to question)
            if line_stripped == "---":
                temp_anki_note.question += f"\n{temp_anki_note.answer}"
                temp_anki_note.answer = ""
                parse_state = ParseSectionState.QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(f"> Found question answer separator (question={temp_anki_note.question})")
            else:
                if len(temp_anki_note.answer.rstrip()) != 0:
                    temp_anki_note.answer += '\n' * (empty_lines + 1)
                temp_anki_note.answer += line.rstrip()
                parse_state = ParseSectionState.ANSWER
                empty_lines = 0
                if debug:
                    print(f"> Found new answer line (answer={temp_anki_note.answer})")
        elif parse_state == ParseSectionState.ANSWER:
            # Question answer was read -> expect more answer lines or answer/question/separator or next question header
            if line_stripped == "---":
                temp_anki_note.question += f"\n{temp_anki_note.answer}"
                temp_anki_note.answer = ""
                parse_state = ParseSectionState.QUESTION_ANSWER_SEPERATOR
                empty_lines = 0
                if debug:
                    print(f"> Found question answer separator (question={temp_anki_note.question})")
            else:
                temp_optional_anki_note = parse_question_header(line, debug_this=debug)
                if temp_optional_anki_note is not None:
                    temp_anki_deck.notes.append(temp_anki_note)
                    if debug:
                        print(f"> new note was appended to deck (notes={temp_anki_deck.notes})")
                    temp_anki_note = temp_optional_anki_note
                    parse_state = ParseSectionState.QUESTION_HEADER
                    empty_lines = 0
                else:
                    if len(temp_anki_note.answer.rstrip()) != 0:
                        temp_anki_note.answer += '\n' * (empty_lines + 1)
                    temp_anki_note.answer += line.rstrip()
                    parse_state = ParseSectionState.ANSWER
                    empty_lines = 0
                    if debug:
                        print(f"> Found new answer line (answer={temp_anki_note.answer})")
        elif parse_state == ParseSectionState.QUESTION_ANSWER_SEPERATOR:
            # Question answer separator was read -> expect answer block or new question block
            temp_optional_anki_note = parse_question_header(line, debug_this=debug)
            if temp_optional_anki_note is not None:
                temp_anki_deck.notes.append(temp_anki_note)
                if debug:
                    print(f"> new note was appended to deck (notes={temp_anki_deck.notes})")
                temp_anki_note = temp_optional_anki_note
                parse_state = ParseSectionState.QUESTION_HEADER
                empty_lines = 0
            else:
                if len(temp_anki_note.answer.rstrip()) != 0:
                    temp_anki_note.answer += '\n' * (empty_lines + 1)
                temp_anki_note.answer += line.rstrip()
                parse_state = ParseSectionState.ANSWER
                empty_lines = 0
                if debug:
                    print(f"> Found answer line (answer={temp_anki_note.answer})")

    if parse_state == ParseSectionState.ANSWER:
        temp_anki_deck.notes.append(temp_anki_note)
        if debug:
            print(f"> new note was appended to deck (notes={temp_anki_deck.notes})")

    return temp_anki_deck


# Main method (This will not be executed when file is imported)
if __name__ == '__main__':

    debug_flag_found = False

    nextAnkiOutFilePath: bool = False
    nextMdOutFilePath: bool = False
    nextRmResPrefix: bool = False

    argsToRemove: List[str] = [sys.argv[0]]

    # Simple (activate) options
    for x in sys.argv:
        if x == "--help" or x == "-help" or x == "-h":
            cli_help()
            exit(0)
        if x == "--version" or x == "-version" or x == "-v":
            cli_version()
            exit(0)

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    if len(sys.argv) < 1:
        print("No input file was specified!")
        sys.exit(1)

    md_input_file_path = sys.argv[0]
    md_output_file_path = sys.argv[0]
    argsToRemove.append(sys.argv[0])
    anki_output_file_path = f"{os.path.basename(md_input_file_path)}.apkg"

    if not os.path.isfile(md_input_file_path):
        print(f"Input file was not found: '{md_input_file_path}'")
        sys.exit(1)

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    additional_res_dirs: List[str] = []

    for x in sys.argv:
        if x == "-d":
            argsToRemove.append(x)
            debug_flag_found = True
            print("> Debugging was turned on")
        elif nextAnkiOutFilePath:
            nextAnkiOutFilePath = False
            anki_output_file_path = x
            argsToRemove.append(x)
        elif nextMdOutFilePath:
            nextMdOutFilePath = False
            md_output_file_path = x
            argsToRemove.append(x)
        elif nextRmResPrefix:
            nextRmResPrefix = False
            additional_res_dirs.append(x)
            argsToRemove.append(x)
        elif x == "-o-anki":
            nextAnkiOutFilePath = True
            argsToRemove.append(x)
        elif x == "-o-md":
            nextMdOutFilePath = True
            argsToRemove.append(x)
        elif x == "-additional-res-dir":
            nextRmResPrefix = True
            argsToRemove.append(x)
        else:
            print(f"Unknown option found: '{x}'")
            sys.exit(1)

    anki_deck: AnkiDeck
    with open(md_input_file_path, "r", encoding="utf-8") as md_file:
        anki_deck = parse_md_file_to_anki_deck(md_file, debug=debug_flag_found)

    anki_deck.additional_file_dirs = additional_res_dirs
    anki_deck.model = create_katex_highlightjs_anki_deck_model()

    if debug_flag_found:
        print(anki_deck)

    anki_deck.genanki_write_deck_to_file(anki_output_file_path)

    if md_output_file_path is not None:
        anki_deck.md_write_deck_to_file(md_output_file_path)
