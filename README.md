# Md2Anki

Convert your markdown notes to an anki deck

---

This is currently in development and many features are missing or errors can occur.

---

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

## ID2 (44f2549a-e812-4ebc-807b-95d46fd43578)

Question 2 more


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
To keep them (which enables updating cards later by reimporting the `.apkg` file) specify an output path:

```sh
python3 md2anki.py input.md -o-md output.md
```

## TODOs

- [ ] Export to zip (collect all files and put them into one `res` directory as backup)
