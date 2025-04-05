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

# First, migrate auth and contenttypes
echo "Migrating auth and contenttypes..."
python manage.py migrate auth
python manage.py migrate contenttypes

# Then migrate the blogs app migrations one by one
echo "Migrating blogs app..."
for i in $(seq 1 10); do
    num=$(printf "%04d" $i)
    echo "Applying blogs migration $num..."
    python manage.py migrate blogs $num --fake-initial
done

# Apply the new split migrations
echo "Applying new migrations..."
python manage.py migrate blogs 0011_client_embed_token_client_user --fake-initial
python manage.py migrate blogs 0012_subscription --fake-initial

# Finally, migrate any remaining apps
echo "Applying remaining migrations..."
python manage.py migrate --fake blogs
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