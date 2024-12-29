#!/bin/bash
set -e

if [ -z "$CELERY_MODE" ]; then
    echo "Starting Gunicorn..."
fi

if [ "$ENTRYPOINT" == "web" ]; then
    echo "Applying database migrations..."
    python manage.py migrate

    exec gunicorn posts_app.wsgi:application --bind 0.0.0.0:8000 --workers 4 --log-level info
fi

if [ "$ENTRYPOINT" == "celery_worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A posts_app worker --loglevel=info
fi

if [ "$ENTRYPOINT" == "celery_beat" ]; then
    echo "Starting Celery beat..."
    exec celery -A posts_app beat --loglevel=info
fi
