#!/usr/bin/env python3
"""
Show Combined Database
Queries all individual protocol databases and displays a combined table of all transactions.
"""

import os
import sqlite3
import pandas as pd


def show_combined_database():
    """
    Queries all individual protocol databases and displays a combined table of all transactions.
    """
    print("🚀 Querying all databases...")

    db_paths = {
        "relay": "databases/affiliate.db",
        "portals": "databases/portals_transactions.db",
        "thorchain": "databases/thorchain_transactions.db",
        "chainflip": "databases/chainflip_transactions.db",
        "cowswap": "databases/cowswap_transactions.db",
        "zerox": "databases/zerox_transactions.db",
    }

    all_trades = []

    for protocol, db_path in db_paths.items():
        if not os.path.exists(db_path):
            continue

        conn = sqlite3.connect(db_path)
        try:
            if protocol == "relay":
                df = pd.read_sql_query("SELECT * FROM relay_affiliate_fees", conn)
            elif protocol == "portals":
                df = pd.read_sql_query("SELECT * FROM portals_transactions", conn)
            elif protocol == "thorchain":
                df = pd.read_sql_query("SELECT * FROM thorchain_transactions", conn)
            elif protocol == "chainflip":
                df = pd.read_sql_query("SELECT * FROM chainflip_transactions", conn)
            elif protocol == "cowswap":
                df = pd.read_sql_query("SELECT * FROM cowswap_transactions", conn)
            elif protocol == "zerox":
                df = pd.read_sql_query("SELECT * FROM zerox_transactions", conn)

            df["protocol"] = protocol
            all_trades.append(df)
        except Exception as e:
            print(f"❌ Error reading from {protocol} database: {e}")
        finally:
            conn.close()

    if not all_trades:
        print("❌ No data found in any database.")
        return

    combined_df = pd.concat(all_trades, ignore_index=True)

    print("\n✅ Combined Database:")
    print(combined_df.to_string())


if __name__ == "__main__":
    show_combined_database()
