# PKGBUILD

To create a Linux `pacman` compatible package of `md2anki` the following steps are necessary.

## `pacman` basics

To create a `pacman` package a `PKGBUILD` file needs to exist and the command `makepkg` needs to be available:

```sh
# - build a package declared in the PKGBUILD file
# - clean the package sources after a successful build
# - automatically install dependencies necessary to build the package
# - automatically remove dependencies that were installed to build the package
makepkg -p PKGBUILD --clean --syncdeps --rmdeps
```

- You can add `--install` to install the built package right after building it
- Otherwise you can install the package using `pacman -U /folder/package.tar.zst`
