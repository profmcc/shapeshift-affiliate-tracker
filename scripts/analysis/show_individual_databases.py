#!/usr/bin/env python3
"""
Show Individual Databases
Queries all individual protocol databases and displays the contents of each one separately.
"""

import os
import sqlite3
import pandas as pd


def show_individual_databases():
    """
    Queries all individual protocol databases and displays their contents.
    """
    print("🚀 Querying all individual databases...")

    db_paths = {
        "Relay": ("databases/affiliate.db", "relay_affiliate_fees"),
        "Portals": ("databases/portals_transactions.db", "portals_transactions"),
        "THORChain": ("databases/thorchain_transactions.db", "thorchain_transactions"),
        "Chainflip": ("databases/chainflip_transactions.db", "chainflip_transactions"),
        "CowSwap": ("databases/cowswap_transactions.db", "cowswap_transactions"),
        "0x Protocol": ("databases/zerox_transactions.db", "zerox_transactions"),
    }

    found_data = False
    for protocol, (db_path, table_name) in db_paths.items():
        print(f"\n{'='*30}")
        print(f" DATABASE: {protocol} ({db_path})")
        print(f"{'='*30}")

        if not os.path.exists(db_path):
            print("Database file not found.")
            continue

        conn = sqlite3.connect(db_path)
        try:
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone() is None:
                print(f"Table '{table_name}' not found.")
                continue

            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            if df.empty:
                print("No data found.")
            else:
                print(df.to_string())
                found_data = True
        except Exception as e:
            print(f"❌ Error reading from database: {e}")
        finally:
            conn.close()

    if not found_data:
        print("\n❌ No data was found in any of the databases.")


if __name__ == "__main__":
    show_individual_databases()
