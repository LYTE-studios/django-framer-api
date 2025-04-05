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

# Extract dependencies from Pipfile
echo "Extracting dependencies from Pipfile..."
{
    echo "django"
    echo "djangorestframework"
    echo "django-cors-headers"
    echo "django-storages"
    echo "celery"
    echo "redis"
    echo "gunicorn"
    echo "python-dotenv"
    echo "openai"
    echo "requests"
    echo "boto3"
    echo "stripe"
    echo "watchdog[watchmedo]"
} > requirements.txt

# Verify requirements.txt was created and is not empty
if [ ! -f "requirements.txt" ] || [ ! -s "requirements.txt" ]; then
    echo "Error: requirements.txt was not generated or is empty"
    exit 1
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