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

# Create necessary directories
echo "Creating static and media directories..."
mkdir -p /app/staticfiles
mkdir -p /app/media
chmod -R 755 /app/staticfiles /app/media

# Wait for Redis
wait_for_redis

# Apply database migrations
echo "Applying database migrations..."
# Fake the problematic migration
python manage.py migrate blogs 0010_alter_blogpost_thumbnail
python manage.py migrate blogs 0011_client_embed_token_client_user_subscription --fake
# Run any remaining migrations
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Execute the command passed to docker
echo "Starting service..."
exec "$@"