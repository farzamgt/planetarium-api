#!/bin/sh

echo "Waiting for database..."
python manage.py wait_for_db

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
