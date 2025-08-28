#!/usr/bin/env python3
"""
Search ThorChain data using offset parameters to find specific block
"""

import requests
import json
import time


def search_with_offset():
    """Search using offset parameters to find specific block"""
    target_block = 22470673

    print(f"🎯 Searching for block {target_block} using offset parameters")
    print("🔍 This approach searches through historical data")
    print("=" * 60)

    # Try different offset ranges to find our target block
    # Start with recent data and work backwards
    base_offsets = [0, 1000, 2000, 5000, 10000, 20000, 50000]

    all_actions = []
    ss_transactions = []
    target_block_found = False

    for base_offset in base_offsets:
        print(f"\n📡 Searching with base offset {base_offset}...")

        try:
            url = "https://midgard.ninerealms.com/v2/actions"
            params = {"offset": base_offset, "limit": 1000, "type": "swap"}

            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"❌ Status code: {response.status_code} for offset {base_offset}")
                continue

            data = response.json()
            actions = data.get("actions", [])

            if not actions:
                print(f"ℹ️  No actions found at offset {base_offset}")
                continue

            print(f"📊 Retrieved {len(actions)} actions at offset {base_offset}")

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
                    print(f"   Offset: {base_offset}")

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
                            "offset": base_offset,
                        }
                    )

            # Add to our collection
            all_actions.extend(actions)

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error with offset {base_offset}: {e}")
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

                # Calculate how far we are from the target
                if target_block < min(heights):
                    blocks_behind = min(heights) - target_block
                    print(
                        f"   💡 Target block is {blocks_behind:,} blocks behind our range"
                    )
                else:
                    blocks_ahead = target_block - max(heights)
                    print(
                        f"   💡 Target block is {blocks_ahead:,} blocks ahead of our range"
                    )

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
            print(f"     Offset: {tx['offset']}")
            print()

        if len(sorted_ss_txs) > 10:
            print(f"... and {len(sorted_ss_txs) - 10} more")

    if not target_block_found:
        print(f"\n💡 Block {target_block} not found in the searched ranges.")
        print(f"💡 This suggests the block is from an even earlier time period.")
        print(f"💡 Consider:")
        print(f"   - Using much larger offset values")
        print(f"   - Checking if the block number is correct")
        print(f"   - Using alternative data sources")

    return target_block_found, list(unique_ss_txs)


if __name__ == "__main__":
    search_with_offset()
