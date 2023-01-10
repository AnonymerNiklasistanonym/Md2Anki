#!/usr/bin/env pwsh

$CALL_DIR = $PWD

# Make script stop when an error happens
$ErrorActionPreference = "Stop"

# Go to script directory even when run from another one
Set-Location -Path $PSScriptRoot

python -m clean
$files = Get-ChildItem -Recurse -Directory -Include 'venv_*'
foreach ($file in $files) {
    Write-Output "Remove directory '$($file.FullName)'"
    Remove-Item -Recurse -Force $file.FullName
}

# Go back to original directory
Set-Location -Path $CALL_DIR
