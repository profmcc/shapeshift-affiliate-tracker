"""
shared.db

Helpers for SQLite database connection and schema management.

Example usage:
    from shared.db import connect_db, ensure_schema
    conn = connect_db('mydb.sqlite')
    ensure_schema(conn, 'CREATE TABLE IF NOT EXISTS ...')
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Any

def ensure_db_dir(db_path):
    """
    Ensure the directory for the database exists.
    Args:
        db_path (str): Path to the SQLite database file.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

@contextmanager
def db_connection(db_path):
    """
    Context manager for SQLite DB connection.
    Args:
        db_path (str): Path to the SQLite database file.
    Yields:
        sqlite3.Connection: SQLite connection object.
    """
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_table(db_path, schema_sql):
    """
    Initialize a table using the provided schema SQL.
    Args:
        db_path (str): Path to the SQLite database file.
        schema_sql (str): SQL statement to create the table.
    """
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(schema_sql) 

def connect_db(db_path: str) -> sqlite3.Connection:
    """
    Connect to a SQLite database at the given path.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Database connection object.

    Raises:
        sqlite3.Error: If connection fails.

    Example:
        >>> from shared.db import connect_db
        >>> conn = connect_db('mydb.sqlite')
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to connect to database: {e}")

def ensure_schema(conn: sqlite3.Connection, schema_sql: str) -> None:
    """
    Ensure the database schema exists by executing the provided SQL.

    Args:
        conn (sqlite3.Connection): Database connection.
        schema_sql (str): SQL string to create tables if not exist.

    Raises:
        sqlite3.Error: If schema creation fails.

    Example:
        >>> schema = 'CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, data TEXT);'
        >>> ensure_schema(conn, schema)
    """
    try:
        with conn:
            conn.executescript(schema_sql)
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to ensure schema: {e}") 