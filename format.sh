#!/usr/bin/env bash

# Make script stop when an error happens
set -e

black src setup.py main.py tests examples
