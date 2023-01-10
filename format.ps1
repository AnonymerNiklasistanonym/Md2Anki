#!/usr/bin/env pwsh

# Make script stop when an error happens
$ErrorActionPreference = "Stop"

python -m black src setup.py main.py clean.py update_readme.py tests examples
