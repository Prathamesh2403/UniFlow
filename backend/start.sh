#!/usr/bin/env bash
set -e

# Start Celery background worker (single concurrency to stay within free-tier RAM)
celery -A core.celery_app worker --loglevel=info --concurrency=1 &

# Start FastAPI web server on Render's assigned $PORT
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
