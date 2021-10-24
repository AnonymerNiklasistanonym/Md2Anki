#!/usr/bin/env pwsh

# Make script stop when an error happens
$ErrorActionPreference = "Stop"

$PYTHON_VENV_DIR = "venv_Md2Anki_pwsh"
$PYTHON_VENV_REQUIREMENTS_FILE = "requirements.txt"

$ACTIVATE_SCRIPT_PATH_WINDOWS = Join-Path $PSScriptRoot -ChildPath $PYTHON_VENV_DIR | Join-Path -ChildPath "Scripts" | Join-Path -ChildPath "Activate.ps1"
$ACTIVATE_SCRIPT_PATH_LINUX = Join-Path $PSScriptRoot -ChildPath $PYTHON_VENV_DIR | Join-Path -ChildPath "bin" | Join-Path -ChildPath "Activate.ps1"

# Enable usage on multiple operating systems even though the activation paths are different
if ($IsWindows) {
  $ACTIVATE_SCRIPT_PATH = $ACTIVATE_SCRIPT_PATH_WINDOWS
} else {
  $ACTIVATE_SCRIPT_PATH = $ACTIVATE_SCRIPT_PATH_LINUX
}

# Go to script directory even when run from another one
$CALL_DIR = $pwd
Set-Location -Path $PSScriptRoot

# (Create and) Enter virtual environment
if (-not (Test-Path -LiteralPath $PYTHON_VENV_DIR)) {
  python -m venv $PYTHON_VENV_DIR
  if (-not (Test-Path -LiteralPath $ACTIVATE_SCRIPT_PATH)) {
    Write-Output "Activation script file not found: '$ACTIVATE_SCRIPT_PATH'"
    exit 1
  }
  Invoke-Expression $ACTIVATE_SCRIPT_PATH
  python -m pip install --upgrade pip
  if (-not (Test-Path -LiteralPath $PYTHON_VENV_REQUIREMENTS_FILE)) {
    Write-Output "Requirements file not found: '$PYTHON_VENV_REQUIREMENTS_FILE'"
    exit 1
  } else {
    pip install -r $PYTHON_VENV_REQUIREMENTS_FILE
  }
} else {
  if (-not (Test-Path -LiteralPath $ACTIVATE_SCRIPT_PATH)) {
    Write-Output "Activation script file not found: '$ACTIVATE_SCRIPT_PATH'"
    exit 1
  }
  Invoke-Expression $ACTIVATE_SCRIPT_PATH
}

# Go back to the call directory
Set-Location -Path $CALL_DIR

# Run
try {
  $PYTHON_FILE_PATH = Join-Path $PSScriptRoot -ChildPath "src" | Join-Path -ChildPath "md2anki" | Join-Path -ChildPath "md2anki.py"
  python "$PYTHON_FILE_PATH" $args
}
catch {
  return $LASTEXITCODE
}
finally {
  deactivate
}
