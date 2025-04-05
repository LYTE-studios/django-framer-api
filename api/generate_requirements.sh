#!/bin/sh

# Exit on error and print commands
set -e
set -x

echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Directory contents:"
ls -la

# Find Python3 path
if ! command -v python3 > /dev/null 2>&1; then
    echo "Python3 not found. Please install Python3 first."
    exit 1
fi

PYTHON_PATH=$(command -v python3)
echo "Using Python at: $PYTHON_PATH"

# Create requirements.txt with basic dependencies
echo "Creating requirements.txt..."
cat > requirements.txt << EOL
django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-storages==1.14.2
celery==5.3.6
redis==5.0.1
gunicorn==21.2.0
python-dotenv==1.0.0
openai==1.8.0
requests==2.31.0
boto3==1.34.14
stripe==7.10.0
watchdog[watchmedo]==3.0.0
EOL

# Check if requirements.txt was created
if [ ! -f "requirements.txt" ]; then
    echo "Error: Failed to create requirements.txt"
    exit 1
fi

# Make sure the file is readable
chmod 644 requirements.txt

echo "requirements.txt has been generated successfully!"
echo "Contents of requirements.txt:"
cat requirements.txt

# Final verification
if [ -f "requirements.txt" ] && [ -s "requirements.txt" ]; then
    echo "requirements.txt is ready for use"
    echo "File permissions:"
    ls -l requirements.txt
else
    echo "Error: requirements.txt verification failed"
    exit 1
fi