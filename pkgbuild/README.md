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

## WSL

To test this on a Windows PC you can install [Arch-Linux](https://github.com/yuk7/ArchWSL) and run the following commands:

```sh
# Update arch
sudo pacman -Sy archlinux-keyring && sudo pacman -Su
# Install basic packages to build other packages
sudo pacman -S binutils git vim
# Create non root user and assign a password to them (to run makepkg/yay command)
useradd pkgbuild_user
passwd pkgbuild_user
# Change to non root user
su newuser
# Or run a command as non root user
sudo -u newuser %command%
# Create home directory for user (that belongs to that user)
mkdir -p /home/pkgbuild_user
chown pkgbuild_user:pkgbuild_user /home/pkgbuild_user
usermod -d /home/pkgbuild_user pkgbuild_user
```

To get `sudo` access for this new user `pkgbuild_user` you need to edit the `/etc/sudoers` file:

```sh
sudo vim /etc/sudoers
# Also possible to use
sudo pacman -S vi
sudo visudo
```

You have 2 options:

1. Add a sudo user group and then add the user to that user group

   - Most likely there is already an entry that just needs to be uncommented otherwise add:
     ```text
     ## Uncomment to allow members of group sudo to execute any command
     %sudo ALL=(ALL:ALL) ALL
     ```

   - Now create the user group `sudo`:

     ```bash
     sudo groupadd sudo
     ```

   - And add the user to this group:

     ```bash
     sudo usermod -aG sudo pkgbuild_user
     ```

2. Add a custom entry for that user

   - For this just copy the line for the root user and paste it on a new line with the name of the user:

     ```text
     pkgbuild_user ALL=(ALL:ALL) ALL
     ```

### Bad characters

In case you get an error because of *bad* Windows characters use the program `dos2unix` to easily convert files:

```sh
sudo pacman -S dos2unix
dos2unix PKGBUILD
```

### `yay`

If some of the build/run-time dependencies are also packages that do not yet have an official package but an unofficial AUR (Arch User Repository) package these can easily be installed with `yay`.

To install `yay` follow the following steps:

```bash
# Clone the package file and install necessary dependencies
cd /opt
sudo git clone https://aur.archlinux.org/yay-git.git
sudo chown -R pkgbuild_user:pkgbuild_user ./yay-git
cd yay-git
sudo pacman -S --needed base-devel
# Build yay and install it afterwards
makepkg -si
# To update these unofficial packages run
sudo yay -Syu
```

## MAN page

**TODO**

To create a man page for the package use the following commands

```sh
# Install pandoc
pacman -S pandoc
# Convert Markdown file to man file
pandoc "man.md" -s -t man -o "man.1"
# And to view it use
man -l "man.1"
```
