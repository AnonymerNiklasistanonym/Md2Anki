# Example 'Code' (3947389752)

## Question with inline code `camelCaseVar()` (c1277119-fe3b-4843-a41e-ecf12fbd79fb)

Answer with `inline` code

Format inline code `print('inline')`{.py} is also `supported`{.text}

## Question with code block: (605ec2c5-e905-4019-a309-39bbb401c589)

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Title</title>
  <meta name="description" content="description">
  <meta name="author" content="Author">
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <script src="js/script.js"></script>
</body>
</html>
```

---

Answer with code block:

```cpp
#include <iostream>
using namespace std;

int main() {
	cout << "Hello World!" << endl; // prints Hello World!
	return 0;
}
```

```asm
; ----------------------------------------------------------------------------------------
; Writes "Hello, World" to the console using only system calls. Runs on 64-bit Linux only.
; To assemble and run:
;
;     nasm -felf64 hello.asm && ld hello.o && ./a.out
; ----------------------------------------------------------------------------------------

          global    _start

          section   .text
_start:   mov       rax, 1                  ; system call for write
          mov       rdi, 1                  ; file handle 1 is stdout
          mov       rsi, message            ; address of string to output
          mov       rdx, 13                 ; number of bytes
          syscall                           ; invoke operating system to do the write
          mov       rax, 60                 ; system call for exit
          xor       rdi, rdi                ; exit code 0
          syscall                           ; invoke operating system to exit

          section   .data
message:  db        'Hello, World', 10      ; note the newline at the end
```

## Question (c1277119-fe3b-4843-a41e-ecf12fbd85fb)

Answer with code from external file:

```cpp

[//]: # (MD2ANKI_INSERT_FILE=res/hello_world.cpp)

```
