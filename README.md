[//]: <> (BEGIN: HEADER)

# md2anki

Convert Markdown formatted documents to anki decks

[//]: <> (END: HEADER)

[![PyPI version](https://badge.fury.io/py/md2anki.svg)](https://badge.fury.io/py/md2anki)

The decks were tested on:

- [Anki (Desktop client, 2.1.56)](https://apps.ankiweb.net/)
- [Anki web (Browser client, 02.2022)](https://ankiweb.net/)
- [AnkiDroid (Android client, 2.15.6)](https://play.google.com/store/apps/details?id=com.ichi2.anki)

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
# Linux
# > Ubuntu
# >> Evaluate code
sudo apt install clang inkscape latexmk nodejs texlive texlive-latex-extra #texlive-full
# >> PDF export
sudo apt install librsvg2-bin pandoc texlive-xetex
# > Arch/Manjaro
# Manjaro/Arch Linux
# >> Evaluate code
sudo pacman -S swi-prolog clang npm inkscape
# >> PDF export
sudo pacman -S pandoc-cli texlive-latex texlive-binextra texlive-xetex texlive-latexextra texlive-fontsextra texlive-luatex texlive-fontsrecommended
```

```ps1
# Windows (the choco package manager is just an example)
# > Evaluate code
choco install inkscape llvm miktex nodejs
# > PDF export
choco install miktex pandoc rsvg-convert
```

(On Windows `rsvg-convert` can sometimes throw errors in combination with `pandoc` but the latest build from [miyako](https://github.com/miyako/console-rsvg-convert/releases) does not throw them so try this one if you get errors)

```sh
# Linux + Windows
npm install -g ts-node
# > For matplotlib python graphs (used in some examples):
python -m pip install numpy matplotlib
```

### Examples

[//]: <> (BEGIN: EXAMPLES)

````markdown
# Example 'Basic' (3714486828)

## One line question (66b3661f-e22e-4986-a50d-569fdac454ad)

One line answer

## Multi line (24501c1a-f615-4355-a862-a00f64cc4725)

question thanks to a question answer separator (`---`)

---

Answer that has multiple lines.

**Basic** *Markdown* and <ins>HTML</ins> <del>formatting</del> is supported.

List:

- a
- b
  - c
  - d
    - e

New list:

1. abc
2. def
   - a
     1. maximum depth

## Question with multiple (parenthesis) (is) (possible) (b7b85393-b76d-43e6-965a-d86108bf5b09)

Answer

## Lines in answers with multiple `---` (f0e03cb6-2015-4f64-bcd3-51e24763705b)

First question answer seperator in the question.

---

Answer

---

Second part of answer with a line before it.
````

````markdown
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

### Subdeck: Subdeck Heading 3 with escaped :​: double colon (406641128)

All notes of the level 4 will be added to this subdeck.

`{=:subdeck_subdeck_tag:=}`

#### Question 3.1 (583813da-5786-4cb8-b39f-ae0337e1f13c)

Answer

### Question 2.2 (583223da-5786-4cb8-b39f-ae0337e1f13c)

Answer
````

[//]: <> (END: EXAMPLES)

[//]: <> (TODO: Update this later to be automatically generated [BEGIN])

To create *Fill in the blanks* Anki cards you need to change the anki model:

```sh
md2anki document.md -o-anki anki_deck.apkg -anki-model md2anki_type_cloze
```

If you select the **md2anki_type_cloze_extra** model the "extra" part below "---" will also be displayed only on the answer page while on the **md2anki_type_cloze** model it will just show it on the question and answer part:

```sh
md2anki document.md -o-anki anki_deck.apkg -anki-model md2anki_type_cloze_extra
```

[//]: <> (BEGIN: EXAMPLE_CLOZE)

````markdown
# Example 'Fill in the Blank' (3083273130)

## Basic fill in the blank (5afd1da8-f5af-4abd-8809-6e3e47d164eb)

This text is {{c1::boring::a custom hint}} and {{c1::a placeholder}}

---

This will create a card and be displayed as question:

- This text is [a custom hint] and [...]

which becomes the answer:

- This text is boring and a placeholder

## One line {{c1::cloze}} question (8d93bcdc-cbd9-4209-b7ae-0c9cafdb9d4e)

## Fill in the blank LaTeX math (c686c799-b625-4a76-88e2-fc1a7fd3e5c6)

- $1 + 1 =$ {{c1::$\Omega$::$\Sigma$}}
- $1 + 1 =$ {{c1::$\{ 1, \dots, \infty \}$::$\{ x, \dots, y \}$}}

## Fill in the blank source code (7c4ef35d-4eb1-4a86-955c-84fd7d1d506d)

- To write hello world in C++ you need {{c1::std:&#8203;:iostream::the C++ standard library...}}
- To write hello world in C++ you need {{c1:: `#include <std::iostream>`{.cpp} ::the C++ standard library...}}

```python
print("hello world") {{c1::source code comment}}
```

## Multiple fill the blanks (7e0c3a24-a542-4b53-84c2-0481caa86ab4)

{{c1::Mitochondria}} are the {{c2::powerhouses}} of the cell

---

This will create 2 cards and be displayed as question:

1. [...] are the powerhouses of the cell
2. Mitochondria are the [...] of the cell

which both become the answer:

- Mitochondria are the powerhouses of the cell
````

[//]: <> (END: EXAMPLE_CLOZE)

The anki models can be mixed together and even specified on the card:

```sh
# Global model md2anki_type_cloze
# - contains one md2anki_type_cloze (global override)
# - contains one md2anki_type_default (override on card)
# - contains one md2anki_type_cloze_extra (override on card)
md2anki document.md -o-anki anki_deck.apkg
```

[//]: <> (BEGIN: EXAMPLE_MULTIPLE_TYPES)

````markdown
# Example 'Multiple card types' (2303117446)

Global card type:

`{=<md2anki_type_cloze>=}`

## Card with global {{c1::card type}} (680d8091-21fb-40e0-9b9b-314b93baafcf)

Answer

## Card with custom card type `{=<md2anki_type_default>=}` (888ca2b8-9191-49fb-9681-bd5d818b5749)

Answer

## {{c1::Multi}} line card with custom card type (0834581b-ad90-47c1-b6ba-fc884e582d87)

`{=<md2anki_type_cloze_extra>=}`

---

Answer
````

[//]: <> (END: EXAMPLE_MULTIPLE_TYPES)

Checkout the [`examples`](examples) directory for more examples.

If you want to run them all use the following command in that directory:

```sh
python -m examples
```

## Usage

[//]: <> (BEGIN: USAGE)

````text
usage: md2anki [-h] [-v] [--lexers] [-d [{DEBUG,INFO,WARNING,ERROR,CRITICAL}]] [-e]
               [--evaluate-code-ignore-cache] [--evaluate-code-delete-cache] [-k]
               [-anki-model MODEL_ID] [-o-anki APKG_FILE] [-o-md MD_FILE]
               [-o-md-dir MD_DIR] [-o-backup-dir BACKUP_DIR] [-o-pdf PDF_FILE]
               [-evaluate-code-cache-dir CACHE_DIR] [-log-file LOG_FILE]
               [-file-dir [FILE_DIR ...]] [-md-heading-depth HEADING_DEPTH]
               [-custom-program language program]
               [-custom-program-args language program-args]
               MD_INPUT_FILE [MD_INPUT_FILE ...]

Create an anki deck file (.apkg) from one or more Markdown documents. If no custom
output path is given the file name of the document (+ .apkg) is used.

positional arguments:
  MD_INPUT_FILE         Markdown (.md) input file that contains anki deck notes

options:
  --evaluate-code-delete-cache
                        delete all cached files from previous code evaluations (default:
                        False)
  --evaluate-code-ignore-cache
                        ignore the cached files from previous code evaluations (default:
                        False)
  --lexers              print a list of all supported lexer languages and their aliases
  -anki-model MODEL_ID  custom anki card model (md2anki_type_default,
                        md2anki_type_answer, md2anki_type_cloze,
                        md2anki_type_cloze_extra) (default: md2anki_type_default)
  -custom-program language program
                        use custom program for code evaluation [i.e. "py" "python3.11"]
                        (default: [('py', 'python'), ('js', 'node'), ('ts', 'npx'),
                        ('pl', 'swipl'), ('latex', 'latexmk'), ('latex', 'inkscape'),
                        ('cpp', 'clang++'), ('cpp', 'main.exe'), ('c', 'clang'), ('c',
                        'main.exe'), ('pandoc_pdf', 'pandoc')])
  -custom-program-args language program-args
                        use custom program args for code evaluation [i.e. "py"
                        "[\"-c\",\"MD2ANKI_CODE\"]"] (default: [('py', '["-c",
                        "MD2ANKI_CODE"]'), ('js', '["-e", "MD2ANKI_CODE"]'), ('ts',
                        '["tsx", "MD2ANKI_CODE_FILE=code.ts"]'), ('pl', '["-O", "-s",
                        "MD2ANKI_CODE_FILE=code.pl", "-g", "true", "-t", "halt."]'),
                        ('latex', '["-shell-escape", "-pdf",
                        "MD2ANKI_CODE_FILE=code.tex"]'), ('latex', '["--export-
                        filename=code.svg", "code.pdf"]'), ('cpp', '["-Wall",
                        "-std=c++20", "MD2ANKI_CODE_FILE=main.cpp", "-o", "main.exe"]'),
                        ('cpp', '[]'), ('c', '["-std=c17", "MD2ANKI_CODE_FILE=main.c",
                        "-o", "main.exe"]'), ('c', '[]'), ('pandoc_pdf', '["--from",
                        "markdown", "--to", "pdf", "--table-of-contents", "-V",
                        "geometry:a4paper", "-V", "geometry:margin=2cm", "--pdf-
                        engine=xelatex", "--pdf-engine-opt=-shell-escape"]')])
  -d, --debug [{DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                        custom log level to the console (default: INFO)
  -e, --evaluate-code   evaluate markdown inline code/code blocks with the language
                        prefix '=' i.e. '`print(1+1)`{=python}' or '```{=python}
                        [newline] print(1+1) [newline] ```' (default: False)
  -evaluate-code-cache-dir CACHE_DIR
                        use a custom cache dir for code evaluations (default: None)
  -file-dir [FILE_DIR ...]
                        add directories that should be checked for referenced files
                        (like relative path images) (default: [])
  -h, --help            show this help message and exit
  -k, --keep-temp-files
                        keep temporary files (default: False)
  -log-file LOG_FILE    log all messages to a text file (.log) (default: None)
  -md-heading-depth HEADING_DEPTH
                        use a custom Markdown heading depth (>=1) (default: 1)
  -o-anki APKG_FILE     custom anki deck (.apkg) output file path [if not given: md
                        input file name + .apkg] (default: None)
  -o-backup-dir BACKUP_DIR
                        create a backup of the anki deck (i.e. merges input files and
                        copies external files) in a directory (default: None)
  -o-md MD_FILE         custom updated (and merged if multiple input files) Markdown
                        (.md) output file path for all input files (default: None)
  -o-md-dir MD_DIR      custom output directory for all updated Markdown (.md) input
                        files (default: None)
  -o-pdf PDF_FILE       create a PDF (.pdf) file of the anki deck (i.e. merges input
                        files and removes IDs) (default: None)
  -v, --version         show program's version number and exit
````

[//]: <> (END: USAGE)

### Linux (bash)

```sh
# Single source file
md2anki anki_deck.md -o-anki anki_deck.apkg
# Multiple source files
md2anki *.md -o-anki anki_deck.apkg
```

### Windows (powershell)

```pwsh
# Single source file
md2anki anki_deck.md -o-anki anki_deck.apkg
# Multiple source files
md2anki (Get-ChildItem -Filter *.md) -o-anki anki_deck.apkg
```

## Install

### PyPI

It can be installed using [`pip`](https://pypi.org/project/md2anki/):

```sh
# Install
pip install md2anki
# Uninstall
pip uninstall md2anki
```

### GitHub Releases

1. Download a wheel (`.whl`) file from [GitHub Releases](https://github.com/AnonymerNiklasistanonym/Md2Anki/releases)
2. Run:

   ```sh
   # Install
   pip install md2anki-$CURRENT_VERSION-py3-none-any.whl
   # Uninstall
   pip uninstall md2anki
   ```

### Pacman

```sh
cd pkgbuild
# Build package and then install it via pacman
makepkg -p PKGBUILD --syncdeps --rmdeps --clean
pacman -S python-md2anki-$CURRENT_VERSION-1-any.pkg.tar.zst
# Or build and install package
makepkg -p PKGBUILD --syncdeps --rmdeps --clean --install
# Remove package
pacman -R python-md2anki
```

### Build

Via the file [`pyproject.toml`](pyproject.toml) the package can be built:

```sh
# Some values in this config (e.g. version, dependencies) are auto generated using
python -m pip install tomlkit
python -m update_pyproject
```

The following commands create the package files in a new directory called `dist`:

- `md2anki-$CURRENT_VERSION-py3-none-any.whl`
- `md2anki-$CURRENT_VERSION.tar.gz`

```sh
python -m pip install --upgrade build
python -m build
```

#### Install package files

The wheel (`.whl`) file can be installed and uninstalled via `pip`:

```sh
# Install
python -m pip install "dist/md2anki-$CURRENT_VERSION-py3-none-any.whl"
# Uninstall
python -m pip uninstall md2anki
```

## Markdown Editors

A list of editors which support WYSIWYG editing of such Markdown documents (source code and math blocks):

- [Typora](https://typora.io/) (paid, free to use until version 0.9)
- [Visual Studio Code](https://code.visualstudio.com/) (open source)

## Development

### Dependencies

- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/): Edit HTML
- [`genanki`](https://pypi.org/project/genanki/): Write Anki decks
- [`Markdown`](https://pypi.org/project/Markdown/): Convert Markdown to HTML
- [`Pygments`](https://pypi.org/project/Pygments/): Convert source code to HTML with syntax highlighting/colors

```sh
python -m pip install --upgrade pip
# Runtime dependencies
python -m pip install --upgrade beautifulsoup4 genanki Markdown Pygments
# Save requirements
python -m pip freeze > "requirements.txt"
```

### Upload package to PyPI

1. [Create an PyPI account](https://pypi.org/account/login/)
2. Go to account settings, Scroll to API tokens, Create PyPI API token (with only the project scope if project already exists)

```sh
# Build
python -m pip install --upgrade pip build
python -m build
# Upload (only if a non existing version is found)
python -m pip install twine
python -m twine upload --skip-existing dist/*
# Use as username: "__token__"
# Use as password the created PyPI API token: "pypi-......"
```

### Type checks

Python files can be checked for type errors (to some extent) using the commands:

```sh
python -m pip install --upgrade mypy tomlkit types-beautifulsoup4 types-Markdown types-Pygments types-setuptools
python -m mypy src examples tests clean.py format.py main.py update_pkgbuild.py update_pyproject.py update_readme.py
```

### Tests

The tests can be run using the command (in the `tests` directory):

```sh
python -m unittest
```

### Format code

Python files can be formatted using the commands:

```sh
python -m pip install --upgrade black
# Add the option --check to only check if its already in the correct format
python -m black src examples tests clean.py format.py main.py update_pkgbuild.py update_pyproject.py update_readme.py
```

### Code editors

This project was written using the following code editors (IDEs):

- [PyCharm (Community)](https://www.jetbrains.com/pycharm/download/)
- [Visual Studio Code](https://code.visualstudio.com/)
