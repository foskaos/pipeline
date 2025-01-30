#!/bin/sh

echo "Waiting for PostgreSQL to be ready..."

# Wait until PostgreSQL is available
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "PostgreSQL is up. Running migrations..."
python manage.py migrate

echo "Starting Django development server..."
exec "$@"
