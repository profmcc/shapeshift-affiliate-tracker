#!/usr/bin/env python3
"""
Directly save the ThorChain transaction to CSV
"""

import csv
import os
import time
import requests


def save_transaction_direct():
    """Save the transaction directly to CSV"""
    target_tx = "82DAF9415587FD52CD2109976E86A63122CD654E965F076C33FC5A9DD641983C"
    target_block = 22456113

    print(f"🎯 Saving ThorChain transaction directly to CSV")
    print(f"   TX ID: {target_tx}")
    print(f"   Block: {target_block}")
    print("=" * 60)

    # Get the transaction data
    print(f"📡 Fetching transaction data...")

    try:
        url = f"https://midgard.ninerealms.com/v2/actions?txid={target_tx}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()
        actions = data.get("actions", [])

        if not actions:
            print(f"❌ No transaction data found")
            return

        action = actions[0]

        print(f"✅ Transaction data retrieved")

        # Create transaction record
        transaction = {
            "tx_hash": target_tx,
            "chain": "thorchain",
            "block_number": target_block,
            "timestamp": action.get("date", ""),
            "from_address": "",
            "to_address": "",
            "affiliate_address": "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju",
            "affiliate_fee_amount": "0",
            "affiliate_fee_token": "THOR.TCY",
            "affiliate_fee_usd": "0",
            "volume_amount": "0",
            "volume_token": "THOR.TCY",
            "volume_usd": "0",
            "gas_used": 0,
            "gas_price": 0,
            "pool": "THOR.TCY",
            "from_asset": "THOR.RUNE",
            "to_asset": "THOR.TCY",
            "from_amount": "0",
            "to_amount": "0",
            "affiliate_fee_asset": "THOR.TCY",
            "affiliate_fee_amount_asset": "0",
            "created_at": int(time.time()),
        }

        # Extract actual data from action
        if "in" in action and action["in"]:
            in_data = action["in"][0]
            transaction["from_address"] = in_data.get("address", "")
            if "coins" in in_data and in_data["coins"]:
                coin = in_data["coins"][0]
                transaction["from_asset"] = coin.get("asset", "")
                transaction["from_amount"] = coin.get("amount", "0")
                transaction["volume_amount"] = coin.get("amount", "0")
                transaction["volume_token"] = coin.get("asset", "")

        if "out" in action and action["out"]:
            out_data = action["out"][0]
            transaction["to_address"] = out_data.get("address", "")
            if "coins" in out_data and out_data["coins"]:
                coin = out_data["coins"][0]
                transaction["to_asset"] = coin.get("asset", "")
                transaction["to_amount"] = coin.get("amount", "0")

        # Get memo
        memo = action.get("metadata", {}).get("swap", {}).get("memo", "")

        print(f"📝 Transaction details:")
        print(f"   TX: {transaction['tx_hash']}")
        print(f"   Block: {transaction['block_number']}")
        print(f"   From: {transaction['from_amount']} {transaction['from_asset']}")
        print(f"   To: {transaction['to_amount']} {transaction['to_asset']}")
        print(f"   Affiliate: {transaction['affiliate_address']}")
        print(f"   Memo: {memo}")

        # Save to CSV
        csv_dir = "../csv_data/transactions"
        os.makedirs(csv_dir, exist_ok=True)
        csv_file = os.path.join(csv_dir, "thorchain_transactions.csv")

        # Check if file exists
        file_exists = os.path.exists(csv_file)

        print(f"💾 Saving to: {csv_file}")
        print(f"   File exists: {file_exists}")

        # Write to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=transaction.keys())

            # Write header if file is new
            if not file_exists or os.path.getsize(csv_file) == 0:
                writer.writeheader()
                print(f"   📝 Header written")

            # Write transaction
            writer.writerow(transaction)
            print(f"   📝 Transaction written")

        print(f"✅ Transaction saved successfully!")

        # Verify the save
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            print(f"📊 CSV now has {len(rows)} rows (including header)")

            if len(rows) > 1:
                print(f"📋 Last row preview: {rows[-1][:5]}...")  # Show first 5 fields

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    save_transaction_direct()
