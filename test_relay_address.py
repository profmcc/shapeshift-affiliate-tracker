#!/usr/bin/env python3
"""
Test Relay Address - Verify the correct ShapeShift affiliate address
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_relay_address():
    """Test the correct Relay affiliate address"""

    print("🔍 Testing Relay Affiliate Address")
    print("=" * 50)

    # The correct ShapeShift affiliate address for Relay
    correct_address = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"

    print(f"✅ Correct Relay affiliate address: {correct_address}")
    print(
        f"   This is the address that should receive affiliate fees from Relay transactions"
    )

    # Check if this address appears in existing data
    print(f"\n📁 Checking existing data for this address...")

    csv_dir = "csv_data"
    relay_files = [
        "affiliate_relay_affiliate_fees.csv",
        "relay_transactions.csv",
        "relay_transactions_fast.csv",
    ]

    found_transactions = []

    for filename in relay_files:
        filepath = os.path.join(csv_dir, filename)
        if os.path.exists(filepath):
            try:
                import pandas as pd

                df = pd.read_csv(filepath)

                if len(df) > 0:
                    print(f"✅ {filename}: {len(df)} transactions")

                    # Check if any transactions involve the correct affiliate address
                    if "affiliate_address" in df.columns:
                        correct_address_mask = (
                            df["affiliate_address"].str.lower()
                            == correct_address.lower()
                        )
                        correct_count = correct_address_mask.sum()

                        if correct_count > 0:
                            print(
                                f"   🎯 Found {correct_count} transactions with correct affiliate address!"
                            )

                            # Show these transactions
                            correct_df = df[correct_address_mask]
                            for _, row in correct_df.iterrows():
                                found_transactions.append(
                                    {
                                        "file": filename,
                                        "tx_hash": row.get("tx_hash", "N/A"),
                                        "affiliate_address": row["affiliate_address"],
                                        "amount": row.get("amount", "N/A"),
                                        "chain": row.get("chain", "N/A"),
                                    }
                                )
                        else:
                            print(
                                f"   ❌ No transactions with correct affiliate address"
                            )

                            # Show what addresses are actually in the data
                            unique_addresses = df["affiliate_address"].unique()
                            print(f"   📋 Addresses found: {unique_addresses}")

                    elif "partner" in df.columns:
                        correct_address_mask = (
                            df["partner"].str.lower() == correct_address.lower()
                        )
                        correct_count = correct_address_mask.sum()

                        if correct_count > 0:
                            print(
                                f"   🎯 Found {correct_count} transactions with correct affiliate address!"
                            )
                        else:
                            print(
                                f"   ❌ No transactions with correct affiliate address"
                            )
                    else:
                        print(f"   ⚠️ No affiliate address column found")

            except Exception as e:
                print(f"❌ {filename}: Error reading - {e}")
        else:
            print(f"❌ {filename}: File not found")

    print(f"\n📊 Summary:")
    print(f"   Correct affiliate address: {correct_address}")
    print(f"   Transactions found with correct address: {len(found_transactions)}")

    if found_transactions:
        print(f"\n🔍 Transactions with Correct Affiliate Address:")
        for tx in found_transactions:
            print(
                f"   {tx['chain']}: {tx['tx_hash'][:10]}... - Amount: {tx['amount']} ({tx['file']})"
            )
    else:
        print(f"\n❌ No transactions found with the correct affiliate address")
        print(f"   This explains why we're not finding recent relay transactions!")
        print(
            f"   The existing data uses wrong addresses, so we need to scan for new ones"
        )


if __name__ == "__main__":
    test_relay_address()
