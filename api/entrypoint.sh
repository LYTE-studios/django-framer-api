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
python manage.py migrate auth
python manage.py migrate contenttypes

# Then migrate the blogs app migrations in order
echo "Migrating blogs app..."
for i in $(seq 1 11); do
    migration_number=$(printf "%04d" $i)
    echo "Applying migration blogs.$migration_number..."
    python manage.py migrate blogs $migration_number --fake-initial
done

# Finally, migrate any remaining apps
echo "Applying remaining migrations..."
python manage.py migrate --fake blogs

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Execute the command passed to docker
echo "Starting service..."
exec "$@"