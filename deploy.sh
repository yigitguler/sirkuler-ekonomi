#!/bin/bash
set -e

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Neither 'docker-compose' nor 'docker compose' is available"
    exit 1
fi

echo "Starting deployment..."

# Pull latest code
echo "Pulling latest code from GitHub..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
git pull --ff-only origin "$CURRENT_BRANCH"

# Stop existing containers
echo "Stopping containers..."
$COMPOSE_CMD -f docker-compose.production.yaml down

# Build and start containers
echo "Building and starting containers..."
$COMPOSE_CMD -f docker-compose.production.yaml up -d --build

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
$COMPOSE_CMD -f docker-compose.production.yaml exec -T web python sirkulerekonomi/manage.py migrate --noinput

# Collect static files (clear first to ensure manifest is regenerated)
echo "Collecting static files..."
$COMPOSE_CMD -f docker-compose.production.yaml exec -T web python sirkulerekonomi/manage.py collectstatic --noinput --clear

echo "Deployment complete!"
$COMPOSE_CMD -f docker-compose.production.yaml ps
