#!/bin/bash

cd "$(dirname "$0")"

if [ -f ".env" ]; then
    source .env
fi

if [ "$DATABASE_URL" = "" ]; then
    echo DATABASE_URL not set, aborting.
    exit 1
fi

# Check for pending migrations
# current_migration=$(alembic current | awk '{print $1}')
# latest_migration=$(alembic heads | awk '{print $1}')

# if [ "$current_migration" != "$latest_migration" ]; then
#     echo "Running migrations before starting app"
#     alembic upgrade head
# fi

WRAPPER=

if [ -f "newrelic.ini" ]; then
    export NEW_RELIC_CONFIG_FILE=$(pwd)/newrelic.ini
    WRAPPER="newrelic-admin run-program "
fi

$WRAPPER uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}
