#!/usr/bin/env python3
"""
Search through recent ThorChain actions to find specific block or ShapeShift affiliate transactions
"""

import requests
import json
import time


def search_block_range():
    """Search through recent actions for specific block or SS transactions"""
    target_block = 22470673

    print(f"🎯 Searching for block {target_block} and ShapeShift affiliate transactions")
    print("🔍 Using multiple API calls to cover a broader range")
    print("=" * 60)

    # Try different limit sizes to cover more ground
    limits_to_try = [1000, 2000, 5000]

    all_actions = []
    ss_transactions = []
    target_block_found = False

    for limit in limits_to_try:
        print(f"\n📡 Fetching {limit} recent actions...")

        try:
            url = "https://midgard.ninerealms.com/v2/actions"
            params = {"limit": limit, "type": "swap"}

            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"❌ Status code: {response.status_code} for limit {limit}")
                continue

            data = response.json()
            actions = data.get("actions", [])

            print(f"📊 Retrieved {len(actions)} actions")

            # Check for our target block
            for action in actions:
                height = action.get("height", 0)
                memo = action.get("metadata", {}).get("swap", {}).get("memo", "")

                # Check if this is our target block
                if str(height) == str(target_block):
                    target_block_found = True
                    print(f"🎯 FOUND TARGET BLOCK {target_block}!")
                    print(f"   TX ID: {action.get('txID', '')}")
                    print(f"   Date: {action.get('date', '')}")

                    # Check if it has :ss: pattern
                    if memo and ":ss:" in memo.lower():
                        print(f"🎯 CONFIRMED: ShapeShift affiliate transaction!")
                        print(f"   Memo: {memo}")
                    else:
                        print(f"ℹ️  No ShapeShift affiliate pattern found")
                        print(f"   Memo: {memo}")
                    print()

                # Collect all :ss: transactions
                if memo and ":ss:" in memo.lower():
                    ss_transactions.append(
                        {
                            "tx_id": action.get("txID", ""),
                            "height": height,
                            "memo": memo,
                            "date": action.get("date", ""),
                        }
                    )

            # Add to our collection
            all_actions.extend(actions)

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error with limit {limit}: {e}")
            continue

    # Remove duplicates
    unique_actions = {
        action.get("txID"): action for action in all_actions if action.get("txID")
    }.values()
    unique_ss_txs = {tx["tx_id"]: tx for tx in ss_transactions}.values()

    print(f"\n📊 Summary of search:")
    print(f"   Total unique actions retrieved: {len(unique_actions)}")
    print(
        f"   Target block {target_block} found: {'✅ YES' if target_block_found else '❌ NO'}"
    )
    print(f"   Total ShapeShift affiliate transactions: {len(unique_ss_txs)}")

    if unique_actions:
        # Show block range
        heights = [int(a.get("height", 0)) for a in unique_actions if a.get("height")]
        if heights:
            heights.sort()
            print(f"   Block range covered: {min(heights)} to {max(heights)}")

            # Check if our target block is in range
            if target_block >= min(heights) and target_block <= max(heights):
                print(f"   🎯 Target block {target_block} is in the covered range!")
                if not target_block_found:
                    print(f"   💡 Block exists but no actions found - might be empty")
            else:
                print(f"   ℹ️  Target block {target_block} not in covered range")
                print(f"   💡 Block might be from a different time period")

    if unique_ss_txs:
        print(f"\n🎯 ShapeShift Affiliate Transactions Found:")
        print("=" * 40)

        # Sort by block height
        sorted_ss_txs = sorted(
            unique_ss_txs,
            key=lambda x: int(x["height"]) if x["height"] else 0,
            reverse=True,
        )

        for i, tx in enumerate(sorted_ss_txs[:10]):  # Show first 10
            print(f"{i+1:2d}. Block {tx['height']}: {tx['tx_id']}")
            print(
                f"     Memo: {tx['memo'][:80]}{'...' if len(tx['memo']) > 80 else ''}"
            )
            print()

        if len(sorted_ss_txs) > 10:
            print(f"... and {len(sorted_ss_txs) - 10} more")

    if not target_block_found:
        print(f"\n💡 Block {target_block} not found in recent data.")
        print(f"💡 This suggests the block is from an earlier time period.")
        print(f"💡 Consider using historical data sources or different API endpoints.")

    return target_block_found, list(unique_ss_txs)


if __name__ == "__main__":
    search_block_range()
