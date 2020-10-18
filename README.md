# Md2Anki

Convert your markdown notes to an anki deck.

This was tested on the anki Desktop client and the anki web client.

Supported features (and planned ones if not checked):

- [x] Pleasant creation of cards using a markdown editor and then exporting them to an anki deck
- [x] Works on the anki Desktop client
- [x] Works on the anki Web client
- [x] Automatically indexes cards so that they can be updated without loosing their learning progress (just import the updated anki deck)
- [x] LaTeX math (inline and blocks)
- [x] Images (local and URL)
- [ ] Code (code blocks and inline)
- [ ] Text formatting (bold, italics, underline, ...)
- [ ] Export `.zip` file that contains all local assets and the markdown file for easy sharing

## Usage

```text
$ python3 md2anki.py MD_FILE [OPTIONS]

Create an anki deck from a markdown document.

Options:
        -d                              Activate debugging output
        -o-anki FILE_PATH               Custom anki deck output file path
        -o-md FILE_PATH                 Custom markdown output file path
        -additional-res-dir DIR_PATH    Custom resource directory

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

For more examples checkout the [`examples`](examples) directory where you can also run [`create_example_apkgs.sh`](examples/create_example_apkgs.sh) to quickly create all corresponding anki decks and check them out in anki.
