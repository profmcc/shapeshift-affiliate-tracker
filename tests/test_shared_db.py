import os
import tempfile
import sqlite3
from shared.db import db_connection, init_table

def test_db_connection_and_init_table():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    schema_sql = '''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT
        )
    '''
    init_table(db_path, schema_sql)
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO test_table (value) VALUES (?)', ('foo',))
        cursor.execute('SELECT value FROM test_table WHERE id=1')
        result = cursor.fetchone()
    os.remove(db_path)
    assert result[0] == 'foo' 