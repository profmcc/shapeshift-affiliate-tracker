#!/usr/bin/env python3
"""
Clear All Databases
Deletes all SQLite database files in the 'databases' directory.
"""

import os
import glob


def clear_databases():
    """Deletes all .db files in the databases/ directory."""
    db_path = "databases"
    if not os.path.exists(db_path):
        print(f"Directory '{db_path}' not found.")
        return

    db_files = glob.glob(os.path.join(db_path, "*.db"))

    if not db_files:
        print("No database files found to clear.")
        return

    print("Clearing the following database files:")
    for f in db_files:
        print(f" - {f}")
        try:
            os.remove(f)
        except Exception as e:
            print(f"   Error removing file: {e}")

    print("\n✅ All databases cleared.")


if __name__ == "__main__":
    clear_databases()
