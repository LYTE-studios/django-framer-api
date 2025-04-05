#!/bin/sh

# Exit on error
set -e

# Ensure we're in the correct directory (should contain Pipfile)
if [ ! -f "Pipfile" ]; then
    echo "Error: Pipfile not found in current directory"
    echo "Please run this script from the directory containing Pipfile"
    exit 1
fi

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

# Try different methods to generate requirements.txt
generate_requirements() {
    # Try using pipenv directly
    if command -v pipenv > /dev/null 2>&1; then
        pipenv requirements > requirements.txt 2>/dev/null && return 0
    fi
    
    # Try with python -m
    "$PYTHON_PATH" -m pipenv requirements > requirements.txt 2>/dev/null && return 0
    
    # If both methods fail
    return 1
}

if ! generate_requirements; then
    echo "Error: Failed to generate requirements.txt"
    exit 1
fi

# Verify requirements.txt was created and is not empty
if [ ! -f "requirements.txt" ] || [ ! -s "requirements.txt" ]; then
    echo "Error: requirements.txt was not generated or is empty"
    exit 1
fi

# Add watchdog to requirements if not already present
if ! grep -q "watchdog\[watchmedo\]" requirements.txt; then
    echo "watchdog[watchmedo]" >> requirements.txt
fi

echo "requirements.txt has been generated successfully!"
echo "Contents of requirements.txt:"
cat requirements.txt

# Verify the file exists and has content before exiting
if [ -f "requirements.txt" ] && [ -s "requirements.txt" ]; then
    echo "requirements.txt is ready for use"
else
    echo "Error: requirements.txt verification failed"
    exit 1
fi