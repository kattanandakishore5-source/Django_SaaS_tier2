#!/bin/sh
set -e

# Wait for PostgreSQL database if DB_HOST is set
if [ -n "$DB_HOST" ]; then
    echo "Waiting for PostgreSQL database at $DB_HOST:${DB_PORT:-5432}..."
    while ! pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER:-admin}" > /dev/null 2>&1; do
        sleep 1
    done
    echo "PostgreSQL database is ready!"
fi

# Run database migrations if we are running the web service
if [ "$1" = "gunicorn" ] || [ "$1" = "python" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear || true
fi

exec "$@"
