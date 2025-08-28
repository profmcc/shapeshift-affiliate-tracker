import csv
import json
import os
import sqlite3
from typing import Dict

_DB_PATH = os.path.expanduser("~/.token_cache.sqlite")

# --- DB Schema ---
_SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    decimals INTEGER,
    price REAL,
    updated_at INTEGER
);
"""


def bootstrap_from_csv(csv_path: str) -> None:
    """Populate the token cache from a CSV file."""
    with sqlite3.connect(_DB_PATH) as conn, open(csv_path, newline="") as f:
        conn.execute(_SCHEMA)
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                'INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) VALUES (?, ?, ?, ?, ?, strftime("%s","now"))',
                (
                    row["address"],
                    row["symbol"],
                    row["name"],
                    int(row["decimals"]),
                    None,
                ),
            )
        conn.commit()


def bootstrap_from_json(json_path: str) -> None:
    """Populate the token cache from a JSON file (supports Uniswap token list format)."""
    with sqlite3.connect(_DB_PATH) as conn, open(json_path) as f:
        conn.execute(_SCHEMA)
        data = json.load(f)
        # Support Uniswap-style lists with a 'tokens' array
        tokens = data["tokens"] if "tokens" in data else data
        for row in tokens:
            conn.execute(
                'INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) VALUES (?, ?, ?, ?, ?, strftime("%s","now"))',
                (
                    row["address"],
                    row["symbol"],
                    row["name"],
                    int(row["decimals"]),
                    None,
                ),
            )
        conn.commit()


if __name__ == "__main__":
    # Example usage: python bootstrap_tokens.py tokens.csv
    import sys

    if len(sys.argv) != 2:
        print("Usage: python bootstrap_tokens.py <tokens.csv|tokens.json>")
        exit(1)
    path = sys.argv[1]
    if path.endswith(".csv"):
        bootstrap_from_csv(path)
    elif path.endswith(".json"):
        bootstrap_from_json(path)
    else:
        print("File must be .csv or .json")
        exit(1)
