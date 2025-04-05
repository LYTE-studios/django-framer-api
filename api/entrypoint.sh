#!/bin/sh

# Exit on error
set -e

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is up!"
}

# Install netcat for service checking
apt-get update && apt-get install -y netcat-openbsd

# Ensure gunicorn is installed
if ! command -v gunicorn > /dev/null 2>&1; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Wait for Redis
wait_for_redis

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Execute the command passed to docker
echo "Starting service..."
echo "Running command: $@"

# Check if command exists
if [ -z "$1" ]; then
    echo "Error: No command provided"
    exit 1
fi

# Run the command
echo "Executing command..."
exec "$@"