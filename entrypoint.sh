#!/bin/sh
set -eu

echo "Starting Shots Poker"
echo "Version: ${APP_VERSION:-unknown}"
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
	echo "Running Database Migrations..."
	flask db upgrade
else
	echo "Skipping Database Migrations"
fi

exec gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:5000 wsgi:app
