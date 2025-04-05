#!/bin/sh

# Exit on error
set -e

# Wait for database if needed (uncomment and modify if using a database)
# until nc -z $DB_HOST $DB_PORT; do
#     echo "Waiting for database..."
#     sleep 1
# done

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute the command passed to docker
exec "$@"