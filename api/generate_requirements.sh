#!/bin/bash

# Exit on error
set -e

echo "Generating requirements.txt from Pipfile..."

# Install pipenv if not installed
pip install --upgrade pip
pip install pipenv

# Generate requirements.txt
pipenv requirements > requirements.txt

echo "requirements.txt has been generated successfully!"