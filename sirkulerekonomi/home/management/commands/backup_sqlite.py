"""
Back up the SQLite database using the SQLite backup API (consistent snapshot while app may be running).
Usage: python manage.py backup_sqlite [--keep N]
"""
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create a timestamped backup of the SQLite database (safe to run while app is running)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            default=0,
            type=int,
            help="Keep only the last N backups in the backup dir; 0 = keep all.",
        )
        parser.add_argument(
            "--out",
            default=None,
            help="Write backup to this path instead of the default backup dir.",
        )

    def handle(self, *args, **options):
        db_settings = connection.settings_dict
        if db_settings["ENGINE"] != "django.db.backends.sqlite3":
            self.stderr.write(self.style.ERROR("This command only supports SQLite."))
            return

        db_path = Path(db_settings["NAME"])
        if not db_path.exists():
            self.stderr.write(self.style.ERROR("Database file not found: %s" % db_path))
            return

        backup_dir = getattr(settings, "SQLITE_BACKUP_DIR", None)
        if backup_dir is None:
            backup_dir = db_path.parent / "backups"
        else:
            backup_dir = Path(backup_dir)

        if options["out"]:
            out_path = Path(options["out"])
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            backup_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_path = backup_dir / ("db_%s.sqlite3" % stamp)

        self.stdout.write("Backing up %s -> %s" % (db_path, out_path))

        conn = sqlite3.connect(str(db_path))
        try:
            dest = sqlite3.connect(str(out_path))
            try:
                conn.backup(dest)
            finally:
                dest.close()
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS("Backup written: %s" % out_path))

        keep = options["keep"]
        if keep > 0 and not options["out"]:
            backups = sorted(backup_dir.glob("db_*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[keep:]:
                old.unlink()
                self.stdout.write("Removed old backup: %s" % old.name)