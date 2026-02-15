# Sirküler Ekonomi – Deployment (SQLite)

Production uses **SQLite** stored on a Docker volume. There is no separate database server (no PostgreSQL or RDS).

## Prerequisites

- Server (e.g. EC2 Ubuntu) with Docker and Docker Compose
- Domain sirkulerekonomi.com and www.sirkulerekonomi.com pointing to the server
- Git repository clone on the server

## Initial server setup

1. Install Docker and Docker Compose (plugin or standalone).
2. Clone the repository and `cd` into it.
3. Ensure `deploy.sh` is executable: `chmod +x deploy.sh`.

## Deploy

```bash
./deploy.sh
```

This will:

- Pull latest code
- Build and start containers (web, nginx)
- Run migrations against the SQLite database (stored on the `sqlite_data` volume)
- Collect static files

## Data persistence

- The SQLite database file lives at `/app/sirkulerekonomi/data/db.sqlite3` inside the web container.
- This path is backed by the Docker volume **sqlite_data**, so data persists across container restarts and redeploys.

## Backup

Back up the SQLite database for disaster recovery:

- **Option 1 (volume backup):** Back up the Docker volume `sqlite_data` using your preferred method (e.g. `docker run` with the volume mounted and copy the file).
- **Option 2 (from container):** Copy the file out of the running web container:
  ```bash
  docker compose -f docker-compose.production.yaml exec web cat /app/sirkulerekonomi/data/db.sqlite3 > backup.sqlite3
  ```

Restore by placing `db.sqlite3` back into the volume or the data directory before starting the container.

## No database server

- No RDS or PostgreSQL setup is required.
- No database security groups or connection strings.
- All data is in the SQLite file on the `sqlite_data` volume.

## Troubleshooting

- View logs: `docker compose -f docker-compose.production.yaml logs -f web`
- Restart web: `docker compose -f docker-compose.production.yaml restart web`
- Shell into web container: `docker compose -f docker-compose.production.yaml exec web bash`
