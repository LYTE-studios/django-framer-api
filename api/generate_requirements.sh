#!/bin/sh

# Exit on error
set -e

# Find Python3 path
if ! command -v python3 > /dev/null 2>&1; then
    echo "Python3 not found. Please install Python3 first."
    exit 1
fi

PYTHON_PATH=$(command -v python3)
echo "Using Python at: $PYTHON_PATH"

# Ensure pip is available
echo "Installing/upgrading pip..."
"$PYTHON_PATH" -m ensurepip --upgrade > /dev/null 2>&1 || true
"$PYTHON_PATH" -m pip install --upgrade pip > /dev/null 2>&1

echo "Installing pipenv..."
"$PYTHON_PATH" -m pip install --user pipenv > /dev/null 2>&1

# Add local bin to PATH
USER_BIN="$HOME/.local/bin"
PATH="$USER_BIN:$PATH"

echo "Generating requirements.txt from Pipfile..."
if [ -f "Pipfile" ]; then
    # Try using pipenv directly first
    if command -v pipenv > /dev/null 2>&1; then
        pipenv requirements > requirements.txt 2>/dev/null || {
            # If direct pipenv fails, try with python -m
            "$PYTHON_PATH" -m pipenv requirements > requirements.txt
        }
    else
        # If pipenv command not found, try with python -m
        "$PYTHON_PATH" -m pipenv requirements > requirements.txt
    fi
else
    echo "Pipfile not found in current directory!"
    exit 1
fi

# Add watchdog to requirements if not already present
if ! grep -q "watchdog\[watchmedo\]" requirements.txt; then
    echo "watchdog[watchmedo]" >> requirements.txt
fi

echo "requirements.txt has been generated successfully!"
echo "Contents of requirements.txt:"
cat requirements.txt