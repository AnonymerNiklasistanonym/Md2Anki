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
