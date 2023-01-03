# Md2Anki

Convert Markdown notes to an anki deck.

This was tested on the anki Desktop client, the anki web client and AnkiDroid.

**TODO**:

- [ ] Offline support for
  - [ ] LaTeX math
  - [ ] source code syntax highlighting
- [ ] Actually merge decks
  - [ ] Merge anki decks with same id
  - [ ] Merge markdown sections with same id
- [ ] Update logs/debug logs

## Features

- Create an anki deck `.apkg` file
- The name of the deck and its notes will be updated on your next deck import (this works via automatic IDs, **deletions can not be tracked!**)
- Very simple basic structure that supports additionally anki note tags and anki subdecks:

  ```markdown
  # Anki deck name (AUTOMATIC_DECK_ID)

  Optional deck description

  `{=:optional_tag_for_cards_in_deck,another_optional_tag_for_cards_in_deck:=}`

  ## Anki note question (AUTOMATIC_NOTE_ID)

  Anki note answer

  ## Long anki note question (AUTOMATIC_NOTE_ID)

  More question content

  ---

  Answer

  ## Subdeck: Anki subdeck name (AUTOMATIC_DECK_ID)

  ## Anki note question of subdeck (AUTOMATIC_NOTE_ID)

  Anki note answer
  ```

- Supported question/answer content:
  - LaTeX math (inline and blocks)
  - Images (local files and URLs, vector and raster format)
  - Code (inline and blocks)
  - All basic Markdown features (i.e. tables, bold, italics, lines)
- Merge notes from multiple markdown input files into a single deck output file
- Export document and all used local assets to a custom directory that can easily be shared or used as backup

## Usage

```text
usage: md2anki [-h] [-v] [-d] [-anki-model MODEL_ID] [-o-anki APKG_FILE]
               [-o-md MD_FILE] [-o-md-dir MD_DIR] [-o-backup-dir BACKUP_DIR]
               [-file-dir [FILE_DIR ...]] [-md-heading-depth HEADING_DEPTH]
               MD_INPUT_FILE [MD_INPUT_FILE ...]

Create an anki deck file (.apkg) from one or more Markdown documents. If no
custom output path is given the file name of the document (+ .apkg) is used.

positional arguments:
  MD_INPUT_FILE         Markdown (.md) input file that contains anki deck
                        notes

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d, --debug           enable debug output
  -anki-model MODEL_ID  custom anki card model (md2anki_online, type_answer)
  -o-anki APKG_FILE     custom anki deck (.apkg) output file path
  -o-md MD_FILE         custom updated and merged Markdown (.md) output file
                        path for all input files
  -o-md-dir MD_DIR      custom output directory for all updated Markdown (.md)
                        input files
  -o-backup-dir BACKUP_DIR
                        create a backup of the anki deck (i.e. merges input
                        files and copies external files)
  -file-dir [FILE_DIR ...]
                        file directories that contain referenced files (like
                        images)
  -md-heading-depth HEADING_DEPTH
                        use a custom Markdown heading depth (>1, default: 1)
```

## Setup

Via the file [`setup.py`](setup.py) the package can be built and installed.

### Build

The following commands create the package files in a new directory called `dist`:

- `md2anki-$CURRENT_VERSION-py3-none-any.whl`
- `md2anki-$CURRENT_VERSION.tar.gz`

```sh
python -m pip install --upgrade build
python -m build
```

### Install

The wheel (`.whl`) file can be installed and uninstalled via `pip`:

```sh
# Install package
pip install dist/md2anki-$CURRENT_VERSION-py3-none-any.whl
# Uninstall package
pip uninstall md2anki
```

## Markdown Editors

A list of editors which support WYSIWYG editing of such Markdown documents (source code and math blocks):

- [Typora](https://typora.io/) (paid, free to use until version 0.9)
- [Visual Studio Code](https://code.visualstudio.com/) (open source)

## Examples

Checkout the [`examples`](examples) directory for examples.

## Dependencies

- [`Markdown`](https://pypi.org/project/Markdown/)
- [`genanki`](https://pypi.org/project/genanki/)
