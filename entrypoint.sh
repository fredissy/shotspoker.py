#!/bin/sh
set -eu

echo "Starting Shots poker"
echo "Version: ${APP_VERSION:-unknown}"

exec python app.py
