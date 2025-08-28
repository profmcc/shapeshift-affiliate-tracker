#!/usr/bin/env python3
"""
Save the ShapeShift affiliate transaction from block 22,470,673
"""

import csv
import os
import time
import requests


def save_block_22470673_transaction():
    """Save the ShapeShift affiliate transaction from block 22,470,673"""
    target_block = 22470673

    print(f"🎯 Saving ShapeShift affiliate transaction from block {target_block}")
    print("🔍 Transaction with memo ending in ':ss:55'")
    print("=" * 60)

    # Get the transaction data using the offset we found
    print(f"📡 Fetching transaction data from offset 2000...")

    try:
        url = "https://midgard.ninerealms.com/v2/actions"
        params = {"offset": 2000, "limit": 1000, "type": "swap"}

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        actions = data.get("actions", [])

        if not actions:
            print(f"❌ No actions found")
            return

        print(f"📊 Retrieved {len(actions)} actions")

        # Find the ShapeShift affiliate transaction in our target block
        target_tx = None
        for action in actions:
            height = action.get("height", 0)
            memo = action.get("metadata", {}).get("swap", {}).get("memo", "")

            if str(height) == str(target_block) and memo and ":ss:" in memo.lower():
                target_tx = action
                break

        if not target_tx:
            print(
                f"❌ ShapeShift affiliate transaction not found in block {target_block}"
            )
            return

        print(f"✅ Found ShapeShift affiliate transaction!")
        print(f"   TX ID: {target_tx.get('txID', 'N/A')}")
        print(f"   Block: {target_tx.get('height', 'N/A')}")
        print(f"   Date: {target_tx.get('date', 'N/A')}")

        memo = target_tx.get("metadata", {}).get("swap", {}).get("memo", "")
        print(f"   Memo: {memo}")

        # Create transaction record
        transaction = {
            "tx_hash": target_tx.get("txID", ""),
            "chain": "thorchain",
            "block_number": target_block,
            "timestamp": target_tx.get("date", ""),
            "from_address": "",
            "to_address": "",
            "affiliate_address": "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju",
            "affiliate_fee_amount": "0",
            "affiliate_fee_token": "BTC",  # Based on memo pattern =:b: (Bitcoin)
            "affiliate_fee_usd": "0",
            "volume_amount": "0",
            "volume_token": "BTC",
            "volume_usd": "0",
            "gas_used": 0,
            "gas_price": 0,
            "pool": "BTC",
            "from_asset": "BTC",
            "to_asset": "BTC",
            "from_amount": "0",
            "to_amount": "0",
            "affiliate_fee_asset": "BTC",
            "affiliate_fee_amount_asset": "0",
            "created_at": int(time.time()),
        }

        # Extract actual data from action
        if "in" in target_tx and target_tx["in"]:
            in_data = target_tx["in"][0]
            transaction["from_address"] = in_data.get("address", "")
            if "coins" in in_data and in_data["coins"]:
                coin = in_data["coins"][0]
                transaction["from_asset"] = coin.get("asset", "")
                transaction["from_amount"] = coin.get("amount", "0")
                transaction["volume_amount"] = coin.get("amount", "0")
                transaction["volume_token"] = coin.get("asset", "")

        if "out" in target_tx and target_tx["out"]:
            out_data = target_tx["out"][0]
            transaction["to_address"] = out_data.get("address", "")
            if "coins" in out_data and out_data["coins"]:
                coin = out_data["coins"][0]
                transaction["to_asset"] = coin.get("asset", "")
                transaction["to_amount"] = coin.get("amount", "0")

        # Parse memo to get more details
        if memo:
            memo_parts = memo.split(":")
            if len(memo_parts) >= 4:
                # Format: =:b:bc1q5mvrqhv5s4yhw0ly5nj3g9v6gxr5w6xy9yegsk:0/10/0:ss:55
                if memo_parts[1] == "b":  # Bitcoin
                    transaction["from_asset"] = "BTC"
                    transaction["to_asset"] = "BTC"
                    transaction["pool"] = "BTC"
                    transaction["affiliate_fee_token"] = "BTC"
                    transaction["affiliate_fee_asset"] = "BTC"

        print(f"📝 Transaction details:")
        print(f"   TX: {transaction['tx_hash']}")
        print(f"   Block: {transaction['block_number']}")
        print(f"   From: {transaction['from_amount']} {transaction['from_asset']}")
        print(f"   To: {transaction['to_amount']} {transaction['to_asset']}")
        print(f"   Affiliate: {transaction['affiliate_address']}")
        print(f"   Pool: {transaction['pool']}")
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

        # Also save the other ShapeShift affiliate transaction we found
        print(f"\n🔍 Also saving the transaction from block 22,457,158...")

        # Find the other SS transaction
        other_ss_tx = None
        for action in actions:
            height = action.get("height", 0)
            memo = action.get("metadata", {}).get("swap", {}).get("memo", "")

            if str(height) == "22457158" and memo and ":ss:" in memo.lower():
                other_ss_tx = action
                break

        if other_ss_tx:
            print(f"✅ Found other ShapeShift affiliate transaction!")
            print(f"   Block: {other_ss_tx.get('height', 'N/A')}")
            print(
                f"   Memo: {other_ss_tx.get('metadata', {}).get('swap', {}).get('memo', '')}"
            )

            # Create transaction record for the other one
            other_transaction = {
                "tx_hash": other_ss_tx.get("txID", ""),
                "chain": "thorchain",
                "block_number": other_ss_tx.get("height", ""),
                "timestamp": other_ss_tx.get("date", ""),
                "from_address": "",
                "to_address": "",
                "affiliate_address": "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju",
                "affiliate_fee_amount": "0",
                "affiliate_fee_token": "RUNE",  # Based on memo pattern =:r: (RUNE)
                "affiliate_fee_usd": "0",
                "volume_amount": "0",
                "volume_token": "RUNE",
                "volume_usd": "0",
                "gas_used": 0,
                "gas_price": 0,
                "pool": "RUNE",
                "from_asset": "RUNE",
                "to_asset": "RUNE",
                "from_amount": "0",
                "to_amount": "0",
                "affiliate_fee_asset": "RUNE",
                "affiliate_fee_amount_asset": "0",
                "created_at": int(time.time()),
            }

            # Extract data
            if "in" in other_ss_tx and other_ss_tx["in"]:
                in_data = other_ss_tx["in"][0]
                other_transaction["from_address"] = in_data.get("address", "")
                if "coins" in in_data and in_data["coins"]:
                    coin = in_data["coins"][0]
                    other_transaction["from_asset"] = coin.get("asset", "")
                    other_transaction["from_amount"] = coin.get("amount", "0")
                    other_transaction["volume_amount"] = coin.get("amount", "0")
                    other_transaction["volume_token"] = coin.get("asset", "")

            if "out" in other_ss_tx and other_ss_tx["out"]:
                out_data = other_ss_tx["out"][0]
                other_transaction["to_address"] = out_data.get("address", "")
                if "coins" in out_data and out_data["coins"]:
                    coin = out_data["coins"][0]
                    other_transaction["to_asset"] = coin.get("asset", "")
                    other_transaction["to_amount"] = coin.get("amount", "0")

            # Save the other transaction
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=other_transaction.keys())
                writer.writerow(other_transaction)

            print(f"✅ Other transaction also saved!")

            # Final count
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                print(f"📊 CSV now has {len(rows)} rows (including header)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    save_block_22470673_transaction()
