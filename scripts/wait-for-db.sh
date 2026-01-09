#!/usr/bin/env sh
# Wait for PostgreSQL to become available, then run the supplied command.
# Usage: ./scripts/wait-for-db.sh db python manage.py migrate

set -eu

HOST="$1"
shift || true

: "${POSTGRES_HOST:=db}"
PGUSER="${POSTGRES_USER:-ledger}"
PGDB="${POSTGRES_DB:-ledger_safe}"

echo "Waiting for Postgres on host '$HOST' (user=$PGUSER db=$PGDB)"

count=0
until pg_isready -h "$HOST" -U "$PGUSER" -d "$PGDB" >/dev/null 2>&1; do
  count=$((count + 1))
  if [ "$count" -ge 120 ]; then
    echo "Timed out waiting for Postgres after $count seconds." >&2
    exit 1
  fi
  echo "Postgres is unavailable - sleeping (attempt: $count)"
  sleep 1
done

echo "Postgres is up - executing: $*"
if [ "$#" -gt 0 ]; then
  exec "$@"
fi
#!/bin/sh
set -e

HOST="$1"
shift

DB_NAME="${POSTGRES_DB:-ledger_safe}"
DB_USER="${POSTGRES_USER:-ledger}"

until pg_isready -h "$HOST" -U "$DB_USER" -d "$DB_NAME"; do
  echo "Waiting for database $DB_NAME at $HOST..."
  sleep 2
done

echo "Database is ready. Starting application..."
exec "$@"
