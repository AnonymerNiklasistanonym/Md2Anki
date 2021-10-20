#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Make script stop when an error happens
set -e

# Go to script directory even when run from another one
cd "$SCRIPT_DIR"

# Use run script from root to create all demos for all found markdown files
find . -maxdepth 1 -type f -name "*_example.md" | while read md_filename
do
	../run.sh "examples/$md_filename" \
	          -o-anki "examples/$(basename "$md_filename" .md).apkg" \
	          -file-dir "examples" \
	          -o-backup-dir "examples/backup_$(basename "$md_filename" .md)" \
	          "$@"
done

../run.sh "examples/multi_page_example_part_01.md" \
          "examples/multi_page_example_part_02.md" \
          "examples/multi_page_example_part_03.md" \
          -o-anki "examples/multi_page_example.apkg" \
          -o-md "examples/multi_page_example.md" \
          -o-md-dir "examples" \
          -file-dir "examples" \
          -o-backup-dir "examples/backup_multi_page_example" \
          "$@"

# Use run script from root to create all demo backups for all found markdown files
find . -maxdepth 1 -type d -name "backup_*" | while read backup_dir
do
	../run.sh "examples/$backup_dir/document.md" \
	          -o-anki "examples/$(basename "$backup_dir").apkg" \
	          -file-dir "examples/$backup_dir" \
	          "$@"
done
