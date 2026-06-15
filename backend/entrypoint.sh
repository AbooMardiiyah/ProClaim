#!/bin/sh
if [ "$APP_MODE" = "worker" ]; then
    exec celery -A app.workers.celery_app worker -Q extraction -l info --concurrency 2
else
    exec sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
fi
