#!/usr/bin/env pwsh

# Make script stop when an error happens
$ErrorActionPreference = "Stop"

# Run python clean script
$CALL_DIR = $PWD
Set-Location -Path $PSScriptRoot
python -m clean
Set-Location -Path $CALL_DIR

# Remove python virtual environments
$VenvDirs = Get-ChildItem -Path $PSScriptRoot -Directory -Filter "venv_*"
foreach ($VenvDir in $VenvDirs) {
    Write-Output "Remove directory '$($VenvDir.FullName)'"
    Remove-Item -Recurse -Force $VenvDir
}


