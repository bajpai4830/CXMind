#!/bin/bash
# Run database migrations
alembic upgrade head

# Start the web server
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
