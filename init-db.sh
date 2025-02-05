#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" &> /dev/null; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Clearing database..."
psql -h db -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS msk_db;"


echo "Creating database..."
psql -h db -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE msk_db;"

echo "Running SQL script..."
psql -h db -U "$POSTGRES_USER" -d msk_db -f /msk_db.sql

echo "Database setup complete."
