import os
import sys
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
from app.core.config import settings


def create_test_db() -> int:
    """Create test database if it doesn't exist."""

    # Parse TEST_DATABASE_URL to extract connection details
    # Format: postgresql://user:pass@host:port/DBNAME
    test_db_url = settings.TEST_DATABASE_URL
    parsed = urlparse(test_db_url)

    user = parsed.username or os.environ.get("POSTGRES_USER", "postgres")
    password = parsed.password or os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = parsed.hostname or "db"
    port = parsed.port or 5432
    test_db = parsed.path.lstrip("/") if parsed.path else "IAMS_DB_Test"
    admin_db = "postgres"

    try:
        conn = psycopg2.connect(dbname=admin_db, user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if test DB exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (test_db,))

        if not cur.fetchone():
            print(f"Creating test database: {test_db}")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
            print(f"Test database '{test_db}' created successfully")
        else:
            print(f"Test database '{test_db}' already exists")

        cur.close()
        conn.close()
        return 0

    except Exception as exc:
        print(f"Error creating test database: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(create_test_db())
