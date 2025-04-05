#!/bin/bash

# Exit on error
set -e

# Find Python3 path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Python3 not found. Please install Python3 first."
    exit 1
fi

echo "Using Python at: $PYTHON_PATH"

# Ensure pip is installed and get its version
echo "Installing/upgrading pip..."
$PYTHON_PATH -m ensurepip --upgrade
$PYTHON_PATH -m pip install --upgrade pip

echo "Installing pipenv..."
$PYTHON_PATH -m pip install --user pipenv

echo "Generating requirements.txt from Pipfile..."
export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"
$PYTHON_PATH -m pipenv requirements > requirements.txt || {
    echo "Failed to generate requirements.txt. Please check your Pipfile."
    exit 1
}

# Add watchdog to requirements
echo "watchdog[watchmedo]" >> requirements.txt

echo "requirements.txt has been generated successfully!"
echo "Contents of requirements.txt:"
cat requirements.txt