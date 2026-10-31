"""
utils/db.py - PostgreSQL connection helper (replaces mysql-connector-python)
Uses psycopg2 with a connection-per-request pattern (same as the original).
"""

import os
import psycopg2
import psycopg2.extras   # for RealDictCursor (returns rows as dicts)

try:                      # load values from a local .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIG = {
    "host":     os.environ.get("PG_HOST",     "localhost"),
    "port":     int(os.environ.get("PG_PORT", 5432)),
    "user":     os.environ.get("PG_USER",     "postgres"),
    "password": os.environ.get("PG_PASSWORD", ""),
    "dbname":   os.environ.get("PG_DATABASE", "library_db"),
    "sslmode":  os.environ.get("PG_SSLMODE",  "require"),   # Supabase needs SSL; use "disable" for local Postgres
}


def get_conn():
    """Connect using DATABASE_URL (Supabase / Render style) if it is set,
    otherwise use the separate PG_* settings above."""
    url = os.environ.get("DATABASE_URL")
    if url:
        kwargs = {}
        if "sslmode" not in url:
            kwargs["sslmode"] = os.environ.get("PG_SSLMODE", "require")
        return psycopg2.connect(url, **kwargs)
    return psycopg2.connect(**DB_CONFIG)


def run_query(sql, params=None):
    """Run a SELECT and return rows as a list of dicts."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def run_write(sql, params=None):
    """
    Run an INSERT/UPDATE and commit it.
    Returns the first column of the first row when the statement has a
    RETURNING clause, otherwise None.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            new_id = cur.fetchone()[0] if cur.description else None
        conn.commit()
        return new_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
