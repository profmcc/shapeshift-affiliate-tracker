#!/usr/bin/env python3
"""
Search for specific ThorChain transaction with SS memo
"""

import requests
import json


def search_specific_tx():
    """Search for the specific transaction with ss memo"""
    target_block = 22470673

    print(f"🎯 Searching for ShapeShift affiliate transactions in block {target_block}")
    print("🔍 Looking for transactions with ':ss:' in memo pattern")

    # Try different API endpoints to find transactions in this block
    endpoints_to_try = [
        f"https://midgard.ninerealms.com/v2/actions",
        f"https://thornode.ninerealms.com/thorchain/block/{target_block}",
    ]

    for endpoint in endpoints_to_try:
        print(f"\n📡 Trying endpoint: {endpoint}")

        try:
            if "thornode" in endpoint:
                # ThorNode block API
                response = requests.get(endpoint, timeout=60)
            else:
                # Search through recent actions to find our block
                params = {"limit": 5000, "type": "swap"}
                response = requests.get(endpoint, params=params, timeout=60)

            if response.status_code != 200:
                print(f"❌ Status code: {response.status_code}")
                continue

            data = response.json()

            if "thornode" in endpoint:
                # Handle ThorNode response format
                print(f"📊 ThorNode response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"📋 Response keys: {list(data.keys())}")
                    # Look for transactions in the block
                    if "transactions" in data:
                        txs = data["transactions"]
                        print(
                            f"📊 Found {len(txs)} transactions in block {target_block}"
                        )

                        # Look for any with :ss: pattern
                        ss_txs = []
                        for tx in txs:
                            if "memo" in tx and ":ss:" in tx["memo"].lower():
                                ss_txs.append(tx)

                        if ss_txs:
                            print(
                                f"🎯 Found {len(ss_txs)} ShapeShift affiliate transactions!"
                            )
                            for tx in ss_txs:
                                print(f"   TX: {tx.get('id', 'N/A')}")
                                print(f"   Memo: {tx.get('memo', 'N/A')}")
                        else:
                            print(
                                f"ℹ️  No ShapeShift affiliate transactions found in block {target_block}"
                            )
                continue

            # Handle Midgard response
            actions = data.get("actions", []) if isinstance(data, dict) else []

            print(f"📊 Retrieved {len(actions)} actions")

            # Search for actions in our target block
            target_block_actions = []
            ss_transactions = []

            for action in actions:
                height = action.get("height", 0)
                memo = action.get("metadata", {}).get("swap", {}).get("memo", "")

                # Check if this action is in our target block
                if str(height) == str(target_block):
                    target_block_actions.append(action)

                # Also collect any transactions with :ss: pattern
                if memo and ":ss:" in memo.lower():
                    ss_transactions.append(
                        {
                            "tx_id": action.get("txID", ""),
                            "height": height,
                            "memo": memo,
                            "date": action.get("date", ""),
                        }
                    )

            if target_block_actions:
                print(
                    f"✅ Found {len(target_block_actions)} actions in block {target_block}"
                )

                # Check for ShapeShift affiliate transactions in this block
                block_ss_txs = []
                for action in target_block_actions:
                    memo = action.get("metadata", {}).get("swap", {}).get("memo", "")
                    if memo and ":ss:" in memo.lower():
                        block_ss_txs.append(action)

                if block_ss_txs:
                    print(
                        f"🎯 Found {len(block_ss_txs)} ShapeShift affiliate transactions in block {target_block}!"
                    )
                    for action in block_ss_txs:
                        print(f"   TX ID: {action.get('txID', '')}")
                        print(
                            f"   Memo: {action.get('metadata', {}).get('swap', {}).get('memo', '')}"
                        )
                        print()
                else:
                    print(
                        f"ℹ️  No ShapeShift affiliate transactions found in block {target_block}"
                    )

                    # Show sample transactions from this block
                    print(f"📋 Sample transactions from block {target_block}:")
                    for i, action in enumerate(target_block_actions[:3]):
                        memo = (
                            action.get("metadata", {}).get("swap", {}).get("memo", "")
                        )
                        print(f"   {i+1}. TX: {action.get('txID', '')}")
                        print(
                            f"      Memo: {memo[:100]}{'...' if len(memo) > 100 else ''}"
                        )
                        print()
            else:
                print(f"ℹ️  No actions found in block {target_block}")

                # Check if our target block is in the range of retrieved data
                if actions:
                    heights = [
                        int(a.get("height", 0)) for a in actions if a.get("height")
                    ]
                    if heights:
                        heights.sort()
                        print(
                            f"📊 Retrieved block range: {min(heights)} to {max(heights)}"
                        )

                        # Check if our target block is in this range
                        if target_block >= min(heights) and target_block <= max(
                            heights
                        ):
                            print(
                                f"🎯 Target block {target_block} is in this range but no actions found"
                            )
                        else:
                            print(f"ℹ️  Target block {target_block} not in this range")
                            print(
                                f"💡 Block {target_block} might be from a different time period"
                            )

            # Show any :ss: transactions found in the data
            if ss_transactions:
                print(
                    f"🎯 Found {len(ss_transactions)} total transactions with ':ss:' pattern!"
                )
                print(f"📋 First 5 ShapeShift affiliate transactions:")
                for i, tx in enumerate(ss_transactions[:5]):
                    print(f"   {i+1}. Block {tx['height']}: {tx['tx_id']}")
                    print(f"      Memo: {tx['memo']}")
                    print()

        except Exception as e:
            print(f"❌ Error with {endpoint}: {e}")

    print(f"\n💡 Summary for block {target_block}:")
    print(f"💡 If no transactions found, the block might be:")
    print(f"   - From an earlier time period")
    print(f"   - Not contain any swap actions")
    print(f"   - Require different API parameters")

    return None


if __name__ == "__main__":
    search_specific_tx()
