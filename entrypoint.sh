#!/bin/sh

echo "Waiting for PostgreSQL to be ready..."

# Wait until PostgreSQL is available
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "PostgreSQL is up. Running migrations..."

python manage.py migrate


# Ensure the cron service is running
echo "Setting up cron job..."



echo "0 * * * * cd /app && /usr/local/bin/python manage.py run_pipeline >> /var/log/pipeline.log 2>&1" | crontab -

# Start the cron daemon
echo "Starting cron..."
crond -b -l 2

# Verify cron job is installed
echo "Current crontab:"
crontab -l

echo "Starting Python container..."
exec "$@"



