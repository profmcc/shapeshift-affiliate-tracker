#!/usr/bin/env python3
"""
Instant Relay Check - No blockchain scanning, just quick data lookup
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def instant_relay_check():
    """Instant check without blockchain scanning"""

    print("🔍 Instant Relay Check - No Blockchain Scanning")
    print("=" * 60)

    # Check existing data files
    print("📁 Checking existing relay data files...")

    csv_dir = "csv_data"
    relay_files = [
        "affiliate_relay_affiliate_fees.csv",
        "relay_transactions.csv",
        "relay_transactions_fast.csv",
    ]

    total_transactions = 0
    recent_transactions = []

    for filename in relay_files:
        filepath = os.path.join(csv_dir, filename)
        if os.path.exists(filepath):
            try:
                import pandas as pd

                df = pd.read_csv(filepath)

                if len(df) > 0:
                    print(f"✅ {filename}: {len(df)} transactions")

                    # Check for recent transactions (last 24 hours)
                    if "created_at" in df.columns:
                        current_time = time.time()
                        hours_24_ago = current_time - (24 * 3600)

                        # Filter for recent transactions
                        recent_mask = df["created_at"] >= hours_24_ago
                        recent_count = recent_mask.sum()

                        if recent_count > 0:
                            print(f"   📅 {recent_count} transactions in last 24 hours")

                            # Get recent transaction details
                            recent_df = df[recent_mask]
                            for _, row in recent_df.iterrows():
                                tx_time = datetime.fromtimestamp(row["created_at"])
                                recent_transactions.append(
                                    {
                                        "file": filename,
                                        "tx_hash": row.get("tx_hash", "N/A"),
                                        "created_at": tx_time,
                                        "chain": row.get("chain", "N/A"),
                                    }
                                )
                        else:
                            print(f"   ⏰ No transactions in last 24 hours")

                    total_transactions += len(df)
                else:
                    print(f"⚠️ {filename}: Empty file")

            except Exception as e:
                print(f"❌ {filename}: Error reading - {e}")
        else:
            print(f"❌ {filename}: File not found")

    print(f"\n📊 Summary:")
    print(f"   Total relay transactions across all files: {total_transactions}")
    print(f"   Recent transactions (24h): {len(recent_transactions)}")

    if recent_transactions:
        print(f"\n🔍 Recent Relay Transactions (Last 24 Hours):")
        for tx in recent_transactions:
            print(
                f"   {tx['chain']}: {tx['tx_hash'][:10]}... - {tx['created_at']} ({tx['file']})"
            )
    else:
        print(f"\n❌ No recent relay transactions found in existing data")
        print(f"   This suggests either:")
        print(f"   1. No relay activity in the last 24 hours")
        print(f"   2. The data hasn't been updated recently")
        print(f"   3. Relay transactions are infrequent")

    # Check if we have any historical data with timestamps
    print(f"\n📅 Historical Data Analysis:")

    for filename in relay_files:
        filepath = os.path.join(csv_dir, filename)
        if os.path.exists(filepath):
            try:
                import pandas as pd

                df = pd.read_csv(filepath)

                if len(df) > 0 and "created_at" in df.columns:
                    # Convert timestamps to datetime
                    df["datetime"] = pd.to_datetime(df["created_at"], unit="s")

                    # Get date range
                    earliest = df["datetime"].min()
                    latest = df["datetime"].max()

                    print(f"   {filename}:")
                    print(f"      Date range: {earliest} to {latest}")
                    print(f"      Total transactions: {len(df)}")

                    # Check last 7 days
                    week_ago = datetime.now() - timedelta(days=7)
                    week_mask = df["datetime"] >= week_ago
                    week_count = week_mask.sum()
                    print(f"      Last 7 days: {week_count} transactions")

            except Exception as e:
                continue


if __name__ == "__main__":
    start_time = time.time()
    instant_relay_check()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.2f} seconds")
