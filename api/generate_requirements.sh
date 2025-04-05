#!/bin/bash

# Exit on error
set -e

echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Please install Python3 first."
    exit 1
fi

echo "Installing/upgrading pip..."
python3 -m ensurepip --upgrade || {
    echo "Failed to install pip. Please install pip manually."
    exit 1
}

echo "Installing pipenv..."
python3 -m pip install --user pipenv || {
    echo "Failed to install pipenv. Please check your Python installation."
    exit 1
}

echo "Generating requirements.txt from Pipfile..."
python3 -m pipenv requirements > requirements.txt || {
    echo "Failed to generate requirements.txt. Please check your Pipfile."
    exit 1
}

# Add watchdog to requirements
echo "watchdog[watchmedo]" >> requirements.txt

echo "requirements.txt has been generated successfully!"
echo "Contents of requirements.txt:"
cat requirements.txt