# Md2Anki

Convert your markdown notes to an anki deck.

This was tested on the anki Desktop client and the anki web client.

Supported features (and planned ones if not checked):

- [x] Pleasant creation of cards using a markdown editor and then exporting them to an anki deck
- [x] Works on the anki Desktop client
- [x] Works on the anki Web client
- [x] Works on the anki Android client
  - [ ] Fix problem with syntax highlighting of code blocks
- [x] Automatically indexes cards so that they can be updated without loosing their learning progress (just import the updated anki deck)
- [x] LaTeX math (inline and blocks)
- [x] Images (local and URL, vector and raster)
- [x] Code (code blocks and inline)
  - [x] Syntax highlighting for code blocks
- [x] Tables
- [x] Text formatting (bold, italics)
- [x] Export document and local assets to a custom directory that can easily be shared or used as backup
- [x] Split the Anki deck markdown document into multiple pages that can then merged together into one anki deck
- [x] Insert tags for each card to allow for better custom studies/references/etc.

## Usage

```text
$ python3 md2anki.py MD_FILE [MD_FILE...] [OPTIONS]

Create an anki deck file (.apkg) from one or more markdown
documents. If no custom output path is given the file name
of the document (+ .apkg) is used.

Options:
        -d                      Activate debugging output
        -o-anki FILE_PATH       Custom anki deck output
                                file path
        -o-md FILE_PATH         Custom markdown output
                                file path (multiple files
                                will be merged into one)
        -o-md-dir DIR_PATH      Custom markdown output
                                directory path
        -o-backup-dir DIR_PATH  Backup the input and its
                                local assets with a build
                                script
        -file-dir DIR_PATH      Additional file directory
                                which can be supplied
                                multiple times

Also supported are:
        --help
        --version
```

For convenience the scripts `run.sh` (Linux) and `run.ps1` (Windows and Linux) can be called to automatically create a local Python 3 virtual environment so that the dependencies do not pollute the whole system.

## Editor

A list of editors which support WYSIWYG editing of such markdown documents (source code and math blocks):

- [Typora](https://typora.io/) (free to use)
- [Visual Studio Code](https://code.visualstudio.com/) (open source - some problems with math blocks...)

## Example

```sh
python3 md2anki.py input.md
```

`input.md`:

```markdown
# Test deck (1475745167)

## Question 1 (4e19216b-521a-4202-be03-5c4cf5368b9f)

Answer1

$100$

## Question 2 (44f2549a-e812-4ebc-807b-95d46fd43578)

more text of question 2

$$
a = 10 * \begin{cases}
1 & \text{yes} \\
0 & \text{else}
\end{cases}
$$

---

Answer2
```

The IDs are automatically generated if not manually specified.
To not update the markdown file but create a new one specify a custom output path:

```sh
python3 md2anki.py input.md -o-md output.md
```

For more examples checkout the [`examples`](examples) directory where you can also run [`run_examples.sh`](examples/run_examples.sh) to quickly create all corresponding anki decks and check them out in anki.

## Install Python package

Via the file [`setup.py`](setup.py) the package can be built and installed.

```sh
python3 -m pip install --upgrade build
python3 -m build
# Which then creates a new directory called `dist` with the following files in there:
#- md2anki-$CURRENT_VERSION-py3-none-any.whl
#- md2anki-$CURRENT_VERSION.tar.gz
```

The wheel file can be installed via:

```sh
# Create a virtual environment for testing otherwise skip this section
python3 -m venv venv_testing_package_installation
source venv_testing_package_installation/bin/activate
# Install it
pip install dist/md2anki-$CURRENT_VERSION-py3-none-any.whl
```

It can also be uninstalled via:

```sh
# Uninstall it
pip uninstall md2anki
```
