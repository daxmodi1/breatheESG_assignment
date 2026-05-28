#!/usr/bin/env bash
set -euxo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-breathe_esg.settings.prod}"

echo "Checking Django configuration..."
python manage.py check

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Seeding demo data..."
python manage.py seed_data

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn breathe_esg.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
