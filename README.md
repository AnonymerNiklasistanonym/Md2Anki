[//]: <> (BEGIN: HEADER)

# md2anki

Convert Markdown formatted documents to anki decks

[//]: <> (END: HEADER)

This was tested on the anki Desktop client, the anki web client and AnkiDroid.

**TODO**:

- [ ] Fix inline code generation without css rule for ALL `<p>` tags
- [ ] Add tests for anki note generation
- [ ] Enable inline code execution to additionally generate:
  - [ ] Graphs
    - [ ] LaTeX `tikzpicture`

## Features

- Create an anki deck `.apkg` file
- The name of the deck and its notes will be updated on your next deck import (this works via automatic IDs, **deletions can not be tracked!**)
- Very simple basic structure that supports additionally anki note tags and anki subdecks:

- Supported question/answer content:
  - LaTeX math (inline and blocks)
  - Images (local files and URLs, vector and raster format)
  - Code (inline and blocks)
  - All basic Markdown features (i.e. tables, bold, italics, lines)
- Merge notes from multiple markdown input files into a single deck output file
- Export document and all used local assets to a custom directory that can easily be shared or used as backup

To evaluate code and export to pdf the following additional software needs to be installed:

```sh
# Linux (the apt package manager is just an example)
# > Evaluate code
sudo apt install clang nodejs
# > PDF export
sudo apt install librsvg2-bin pandoc texlive-xetex
```

```ps1
# Windows (the choco package manager is just an example)
# > Evaluate code
choco install llvm nodejs
# > PDF export
choco install miktex pandoc rsvg-convert
```

```sh
# Both
npm install -g ts-node
# > For matplotlib python graphs (used in some examples):
python -m pip install numpy matplotlib
```

### Examples

Checkout the [`examples`](examples) directory for more examples.

[//]: <> (BEGIN: EXAMPLES)

```markdown
# Example 'Basic' (3714486828)

## One line question (66b3661f-e22e-4986-a50d-569fdac454ad)

One line answer

## Multi line (24501c1a-f615-4355-a862-a00f64cc4725)

question thanks to a question answer separator (`---`)

---

Answer that has multiple lines.

**Basic** *Markdown* and <ins>HTML</ins> <del>formatting</del> is supported.

## Question with multiple (parenthesis) (is) (possible) (b7b85393-b76d-43e6-965a-d86108bf5b09)

Answer

## Lines in answers with multiple `---` (f0e03cb6-2015-4f64-bcd3-51e24763705b)

First question answer seperator in the question.

---

Answer

---

Second part of answer with a line before it.
```

```markdown
# Example 'Subdeck' (750441971)

Example document to show how subdecks work.

`{=:global_tag:=}`

## Question 1 (f51d6aa5-1e39-4ad7-94fb-042f7084eff5)

Answer

## Subdeck: Subdeck Heading 1 (406542328)

All notes of the level 3 will be added to this subdeck.

`{=:subdeck_tag_1:=}`

### Question 1.1 (583813da-5766-4cb8-b39f-ae0337e1f13c)

Answer

## Question 1.2 (f51d6aa5-1e39-4ad8-94fb-047f7094eff5)

Answer

## Subdeck: Subdeck Heading 2 (406541128)

`{=:subdeck_tag_2:=}`

### Question 2.1 (583813da-5766-4cb8-b39f-ae0337e1f13c)

Answer

### Subdeck: Subdeck Heading 3 (406641128)

All notes of the level 4 will be added to this subdeck.

`{=:subdeck_subdeck_tag:=}`

#### Question 3.1 (583813da-5786-4cb8-b39f-ae0337e1f13c)

Answer

### Question 2.2 (583223da-5786-4cb8-b39f-ae0337e1f13c)

Answer
```

[//]: <> (END: EXAMPLES)

## Usage

[//]: <> (BEGIN: USAGE)

```text
usage: md2anki [-h] [-v] [-d] [-anki-model MODEL_ID] [-o-anki APKG_FILE]
               [-o-md MD_FILE] [-o-md-dir MD_DIR] [-o-backup-dir BACKUP_DIR]
               [-o-pdf PDF_FILE] [-file-dir [FILE_DIR ...]]
               [-md-heading-depth HEADING_DEPTH]
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
  -anki-model MODEL_ID  custom anki card model (md2anki_default,
                        md2anki_type_answer) [default: md2anki_default]
  -o-anki APKG_FILE     custom anki deck (.apkg) output file path
  -o-md MD_FILE         custom updated (and merged if multiple input files)
                        Markdown (.md) output file path for all input files
  -o-md-dir MD_DIR      custom output directory for all updated Markdown (.md)
                        input files
  -o-backup-dir BACKUP_DIR
                        create a backup of the anki deck (i.e. merges input
                        files and copies external files) in a directory
  -o-pdf PDF_FILE       create a PDF (.pdf) file of the anki deck (i.e. merges
                        input files and removes IDs)
  -file-dir [FILE_DIR ...]
                        add directories that should be checked for referenced
                        files (like relative path images)
  -md-heading-depth HEADING_DEPTH
                        use a custom Markdown heading depth (>=1) [default: 1]
```

[//]: <> (END: USAGE)

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

## Dependencies

- [`genanki`](https://pypi.org/project/genanki/)
- [`Markdown`](https://pypi.org/project/Markdown/)
- [`Pygments`](https://pypi.org/project/Pygments/)
