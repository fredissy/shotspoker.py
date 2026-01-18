#!/bin/sh
set -eu

echo "Starting Shots Poker"
echo "Running Database Migrations..."
flask db upgrade

exec gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:5000 wsgi:app
