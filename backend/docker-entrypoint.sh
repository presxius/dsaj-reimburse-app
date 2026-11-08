#!/bin/sh
set -e

flask --app wsgi db upgrade

if [ "$SEED_DEMO" = "1" ]; then
  flask --app wsgi seed
fi

exec "$@"
