#!/usr/bin/env python3
"""
Process the specific ThorChain transaction with SS affiliate memo
"""

import os
import sys
import csv
import requests
import time
from datetime import datetime

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Set the correct config path
os.environ["CONFIG_PATH"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "shapeshift_config.yaml"
)

from csv_thorchain_listener import CSVThorChainListener


def process_specific_transaction():
    """Process the specific transaction we found"""
    target_tx = "82DAF9415587FD52CD2109976E86A63122CD654E965F076C33FC5A9DD641983C"
    target_block = 22456113

    print(f"🎯 Processing specific ThorChain transaction")
    print(f"   TX ID: {target_tx}")
    print(f"   Block: {target_block}")
    print("=" * 60)

    # Get the transaction data directly from API
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

        print(f"✅ Transaction data retrieved successfully")
        print(f"   Block Height: {action.get('height', 0)}")
        print(f"   Date: {action.get('date', '')}")

        # Check memo
        swap_meta = action.get("metadata", {}).get("swap", {})
        memo = swap_meta.get("memo", "")
        print(f"   Memo: {memo}")

        # Confirm this is a ShapeShift affiliate transaction
        if ":ss:" in memo.lower():
            print(f"🎯 CONFIRMED: ShapeShift affiliate transaction!")
        else:
            print(f"❌ No ':ss:' pattern found")
            return

        # Initialize the ThorChain listener
        print(f"\n🔄 Initializing ThorChain listener...")
        listener = CSVThorChainListener()

        # Convert the action to a transaction format
        print(f"📝 Converting action to transaction format...")

        try:
            # Use the listener's conversion method
            transaction = listener.convert_swap_to_transaction(action)

            if transaction:
                print(f"✅ Transaction converted successfully:")
                print(f"   TX Hash: {transaction.get('tx_hash', '')}")
                print(f"   Block: {transaction.get('block_number', 0)}")
                print(f"   From Asset: {transaction.get('from_asset', '')}")
                print(f"   To Asset: {transaction.get('to_asset', '')}")
                print(f"   Volume USD: {transaction.get('volume_usd', 0)}")
                print(
                    f"   Affiliate Address: {transaction.get('affiliate_address', '')}"
                )

                # Save to CSV
                print(f"\n💾 Saving transaction to CSV...")
                listener.save_transactions_to_csv([transaction])

                print(f"✅ Transaction saved successfully!")

                # Get updated stats
                stats = listener.get_csv_stats()
                print(f"\n📊 Updated CSV Statistics:")
                print(f"   Total transactions: {stats.get('total_transactions', 0)}")

            else:
                print(f"❌ Failed to convert transaction")

        except Exception as e:
            print(f"❌ Error processing transaction: {e}")

        # Try manual conversion regardless
        print(f"\n🔄 Attempting manual conversion...")

        manual_transaction = {
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
            "from_asset": "unknown",
            "to_asset": "THOR.TCY",
            "from_amount": "0",
            "to_amount": "0",
            "affiliate_fee_asset": "THOR.TCY",
            "affiliate_fee_amount_asset": "0",
            "created_at": int(time.time()),
        }

        # Extract more details from action
        if "in" in action and action["in"]:
            in_data = action["in"][0]
            manual_transaction["from_address"] = in_data.get("address", "")
            if "coins" in in_data and in_data["coins"]:
                coin = in_data["coins"][0]
                manual_transaction["from_asset"] = coin.get("asset", "")
                manual_transaction["from_amount"] = coin.get("amount", "0")

        if "out" in action and action["out"]:
            out_data = action["out"][0]
            manual_transaction["to_address"] = out_data.get("address", "")
            if "coins" in out_data and out_data["coins"]:
                coin = out_data["coins"][0]
                manual_transaction["to_asset"] = coin.get("asset", "")
                manual_transaction["to_amount"] = coin.get("amount", "0")

        print(f"📝 Manual transaction created:")
        print(
            f"   From: {manual_transaction['from_asset']} -> {manual_transaction['to_asset']}"
        )
        print(f"   Affiliate: {manual_transaction['affiliate_address']}")

        # Save manual transaction
        listener.save_transactions_to_csv([manual_transaction])
        print(f"✅ Manual transaction saved!")

    except Exception as e:
        print(f"❌ Error fetching transaction: {e}")


if __name__ == "__main__":
    process_specific_transaction()
