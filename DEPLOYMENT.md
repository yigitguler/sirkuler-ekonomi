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

### Regular automated backups

Use the `backup_sqlite` management command for consistent, app-safe backups (uses SQLite’s backup API). Backups are written to `data/backups/` inside the container (on the `sqlite_data` volume).

Run manually:

```bash
# Inside container (e.g. from host)
docker compose -f docker-compose.production.yaml exec web python sirkulerekonomi/manage.py backup_sqlite --keep 7
```

Or use the helper script (from the repo root):

```bash
./scripts/backup-sqlite.sh --keep 7
```

**Schedule with cron** (e.g. daily at 3:00, keep last 7 backups):

```bash
0 3 * * * cd /path/to/sirkulerekonomi && ./scripts/backup-sqlite.sh --keep 7
```

Install the cron job: `crontab -e` and add the line above (replace `/path/to/sirkulerekonomi` with the real path).

### One-off / manual backup

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

### Cloudflare 521 (Web server is down)

521 means Cloudflare cannot reach your **origin** server (the machine where Docker runs). Fix on the server/hosting side:

1. **Containers running**  
   On the server: `docker compose -f docker-compose.production.yaml ps`  
   Both `web` and `nginx` should be Up. If not: `docker compose -f docker-compose.production.yaml up -d`.

2. **Port 80 open**  
   Your nginx binds to port 80. Ensure the host firewall (e.g. `ufw`) and any cloud security group allow **inbound TCP 80** (and 443 if you add TLS on origin). Cloudflare connects to your origin’s public IP on port 80 (or 443 if SSL mode is Full).

3. **Cloudflare SSL/TLS mode**  
   Your origin nginx listens on **HTTP only** (port 80). In Cloudflare: **SSL/TLS** → **Overview** → set encryption mode to **Flexible** (Cloudflare HTTPS → origin HTTP). If you set Full or Full (strict), Cloudflare will try HTTPS to your origin and get a connection error (521) because the origin has no TLS.

4. **Origin server reachable**  
   From another machine: `curl -v http://YOUR_ORIGIN_IP` (use the server’s real IP, not the Cloudflare proxy IP). If this fails, the server or firewall is blocking access.

5. **DNS in Cloudflare**  
   For the A record of `sirkulerekonomi.com` (and `www` if used), the IP must be your **origin server’s IP**. Proxy status (orange cloud) is fine; the IP must point to the host running Docker.
