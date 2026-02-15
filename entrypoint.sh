#!/bin/sh
set -e

# Ensure Python can import the inner project package (sirkulerekonomi/sirkulerekonomi)
export PYTHONPATH="/app/sirkulerekonomi:${PYTHONPATH}"

# Development mode: run Django dev server (auto-reload), skip gunicorn
if [ "$DEV_SERVER" = "1" ]; then
  cd /app/sirkulerekonomi || exit 1
  echo "Running makemigrations (dev only)..."
  python manage.py makemigrations || true
  echo "Running database migrations..."
  python manage.py migrate --noinput
  echo "Starting Django development server..."
  exec python manage.py runserver 0.0.0.0:8000
fi

cd /app/sirkulerekonomi || exit 1
echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting gunicorn..."
exec gunicorn sirkulerekonomi.wsgi:application --bind 0.0.0.0:8000 --workers 3
