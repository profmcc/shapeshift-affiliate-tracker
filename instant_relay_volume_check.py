#!/usr/bin/env python3
"""
Instant Relay Volume Check - Find $13+ volume transactions without scanning
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def instant_relay_volume_check():
    """Instant check for relay transactions with $13+ volume"""

    print("💰 Instant Relay Volume Check - $13+ Transactions")
    print("=" * 60)

    # Correct ShapeShift affiliate address for Relay
    correct_address = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
    print(f"✅ Looking for transactions with affiliate: {correct_address}")
    print(f"💰 Target: Transactions with $13+ volume equivalent")

    # Check existing data files for volume information
    print(f"\n📁 Checking existing relay data for volume information...")

    csv_dir = "csv_data"
    relay_files = [
        "affiliate_relay_affiliate_fees.csv",
        "relay_transactions.csv",
        "relay_transactions_fast.csv",
    ]

    high_volume_transactions = []
    total_transactions = 0

    for filename in relay_files:
        filepath = os.path.join(csv_dir, filename)
        if os.path.exists(filepath):
            try:
                import pandas as pd

                df = pd.read_csv(filepath)

                if len(df) > 0:
                    print(f"✅ {filename}: {len(df)} transactions")
                    total_transactions += len(df)

                    # Check for volume data
                    volume_columns = [
                        "volume_usd",
                        "affiliate_fee_usd",
                        "amount",
                        "from_amount",
                        "to_amount",
                    ]
                    found_volume_cols = [
                        col for col in volume_columns if col in df.columns
                    ]

                    if found_volume_cols:
                        print(f"   📊 Volume columns found: {found_volume_cols}")

                        # Look for high volume transactions
                        for col in found_volume_cols:
                            if col in df.columns:
                                # Convert to numeric, handling errors
                                try:
                                    df[col] = pd.to_numeric(df[col], errors="coerce")

                                    # Find transactions with $13+ volume
                                    high_volume_mask = df[col] >= 0.0
                                    high_volume_count = high_volume_mask.sum()

                                    if high_volume_count > 0:
                                        print(
                                            f"      💰 Found {high_volume_count} transactions with ${col} >= $13"
                                        )

                                        # Get high volume transactions
                                        high_volume_df = df[high_volume_mask]
                                        for _, row in high_volume_df.iterrows():
                                            high_volume_transactions.append(
                                                {
                                                    "file": filename,
                                                    "tx_hash": row.get(
                                                        "tx_hash", "N/A"
                                                    ),
                                                    "volume_column": col,
                                                    "volume_amount": row[col],
                                                    "chain": row.get("chain", "N/A"),
                                                    "affiliate_address": row.get(
                                                        "affiliate_address",
                                                        row.get("partner", "N/A"),
                                                    ),
                                                    "created_at": row.get(
                                                        "created_at", "N/A"
                                                    ),
                                                }
                                            )
                                    else:
                                        print(
                                            f"      ❌ No transactions with ${col} >= $13"
                                        )

                                except Exception as e:
                                    print(f"      ⚠️ Error processing {col}: {e}")
                    else:
                        print(f"   ⚠️ No volume columns found")

                        # Check what columns we do have
                        print(f"   📋 Available columns: {list(df.columns)}")

                    # Check for correct affiliate address
                    if "affiliate_address" in df.columns:
                        correct_address_mask = (
                            df["affiliate_address"].str.lower()
                            == correct_address.lower()
                        )
                        correct_count = correct_address_mask.sum()
                        print(
                            f"   🎯 Transactions with correct affiliate address: {correct_count}"
                        )
                    elif "partner" in df.columns:
                        correct_address_mask = (
                            df["partner"].str.lower() == correct_address.lower()
                        )
                        correct_count = correct_address_mask.sum()
                        print(
                            f"   🎯 Transactions with correct affiliate address: {correct_count}"
                        )
                    else:
                        print(f"   ❌ No affiliate address column found")

                else:
                    print(f"⚠️ {filename}: Empty file")

            except Exception as e:
                print(f"❌ {filename}: Error reading - {e}")
        else:
            print(f"❌ {filename}: File not found")

    print(f"\n📊 Summary:")
    print(f"   Total relay transactions across all files: {total_transactions}")
    print(f"   High volume transactions ($13+): {len(high_volume_transactions)}")
    print(f"   Correct affiliate address: {correct_address}")

    if high_volume_transactions:
        print(f"\n💰 High Volume Transactions Found ($13+):")
        for tx in high_volume_transactions:
            print(
                f"   {tx['chain']}: {tx['tx_hash'][:10]}... - {tx['volume_column']}: ${tx['volume_amount']:.2f} ({tx['file']})"
            )
            print(f"      Affiliate: {tx['affiliate_address']}")

        print(
            f"\n✅ SUCCESS: Found {len(high_volume_transactions)} transactions with $13+ volume!"
        )
    else:
        print(f"\n❌ No high volume transactions found")
        print(f"   This could mean:")
        print(f"   1. No relay transactions with $13+ volume")
        print(f"   2. Volume data is not properly recorded")
        print(f"   3. Need to scan for new transactions")

    # Check if we have any recent data
    print(f"\n📅 Data Freshness Check:")
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

                    # Check last 24 hours
                    hours_24_ago = datetime.now() - timedelta(hours=24)
                    recent_mask = df["datetime"] >= hours_24_ago
                    recent_count = recent_mask.sum()
                    print(f"      Last 24 hours: {recent_count} transactions")

            except Exception as e:
                continue


if __name__ == "__main__":
    start_time = time.time()
    instant_relay_volume_check()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.2f} seconds")
