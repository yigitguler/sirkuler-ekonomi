#!/bin/bash
# Run SQLite backup inside the web container. Backups are stored in data/backups on the sqlite_data volume.
# Usage: ./scripts/backup-sqlite.sh [--keep N]
# Schedule with cron, e.g. daily at 3am: 0 3 * * * /path/to/repo/scripts/backup-sqlite.sh --keep 7

set -e
cd "$(dirname "$0")/.."

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Neither 'docker-compose' nor 'docker compose' is available"
    exit 1
fi

$COMPOSE_CMD -f docker-compose.production.yaml exec -T web python sirkulerekonomi/manage.py backup_sqlite "$@"
