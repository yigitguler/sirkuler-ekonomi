# Sirküler Ekonomi

## Development (SQLite)

### Prerequisites

- Docker
- Docker Compose (or Docker with built-in compose)

### Quick start

1. **First time:** Build images:
   ```bash
   ./run_development --build
   ```
   In the opened shell:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # optional
   ```

2. **Start development:** Run `./run_development` to bring up containers and open a shell in the web container. The dev server is **not** started automatically.

3. **Start the server manually** (in the shell you got from step 2, or in a new terminal):
   ```bash
   docker compose exec web python manage.py runserver 0.0.0.0:8000
   ```

4. Open http://localhost:8000 (nginx proxies to the web container).

### Options

- `--build`: Rebuild images before starting
- `--down`: Stop and remove containers
- `-h` / `--help`: Show help

### Database

The project uses **SQLite**. The database file is at `sirkulerekonomi/data/db.sqlite3` (create the `data` directory if needed). No separate database container is used.
