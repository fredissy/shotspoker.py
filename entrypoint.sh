#!/bin/sh
set -eu

echo "Starting Shots Poker"
echo "Version: ${APP_VERSION:-unknown}"

exec gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:5000 wsgi:app
