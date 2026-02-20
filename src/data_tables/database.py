"""Database connection management and transaction helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from flask import current_app, g

from .config import config


def get_db() -> sqlite3.Connection:
    """Get database connection for current request context.

    Returns:
        SQLite connection with Row factory enabled.
    """
    if "db" not in g:
        g.db = sqlite3.connect(config.database_path)
        g.db.row_factory = sqlite3.Row
        # Enable foreign key enforcement (off by default in SQLite)
        g.db.execute("PRAGMA foreign_keys = ON")
        # Use WAL mode for better concurrency
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


def close_db(e: Optional[Exception] = None) -> None:
    """Close database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions.

    Automatically commits on success, rolls back on exception.

    Args:
        conn: SQLite database connection.

    Yields:
        The database connection within a transaction.

    Raises:
        Exception: Re-raises any exception after rollback.
    """
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    """Initialize database schema from schema.sql file."""
    conn = get_db()
    schema_path = Path(__file__).parent / "schema.sql"
    conn.executescript(schema_path.read_text())
    conn.commit()


def init_db_standalone(db_path: Optional[str] = None) -> None:
    """Initialize database schema without Flask context.

    Useful for testing and CLI initialization.

    Args:
        db_path: Optional path to database file. Uses config default if None.
    """
    path = db_path or config.database_path
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = Path(__file__).parent / "schema.sql"
    conn.executescript(schema_path.read_text())
    conn.commit()
    conn.close()

