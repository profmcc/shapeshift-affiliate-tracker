#!/usr/bin/env python3
"""
Debug Script for THORChain Listener - Small Batch Test
Tests the THORChainListener by fetching a small batch of recent transactions.
"""

import os
import sys
import sqlite3
import requests

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from listeners.thorchain_listener import THORChainListener


def test_thorchain_small_batch():
    """
    Initializes the THORChainListener, runs a small batch,
    and verifies that the data is correctly stored in the database.
    """
    print("🚀 Starting THORChain small batch test...")

    # Initialize the listener
    listener = THORChainListener()

    # Run the listener with a larger limit
    print("🔍 Fetching a larger batch of recent transactions...")
    listener.run_listener(limit=1000)

    # Verify the data was saved
    print("\n✅ Verifying data in the database...")
    conn = sqlite3.connect(listener.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM thorchain_transactions LIMIT 5")
    rows = cursor.fetchall()

    if not rows:
        print("❌ Verification failed: No data found in the database.")
    else:
        print(f"✅ Verification successful! Found {len(rows)} entries.")
        for row in rows:
            print(f"   - {row[0]}")  # Print only the tx_id

    conn.close()


if __name__ == "__main__":
    test_thorchain_small_batch()
