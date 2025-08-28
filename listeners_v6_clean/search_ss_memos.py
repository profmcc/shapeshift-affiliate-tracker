#!/usr/bin/env python3
"""
Simple script to search for ThorChain swaps with ':ss:' in memo
"""

import requests
import json


def search_ss_memos():
    """Search for swaps with :ss: in memo"""
    url = "https://midgard.ninerealms.com/v2/actions"
    params = {"limit": 1000, "type": "swap"}

    print("🔍 Searching for ThorChain swaps with ':ss:' in memo...")
    print(f"📡 Fetching from: {url}")

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        actions = data.get("actions", [])

        print(f"📊 Retrieved {len(actions)} swap actions")

        ss_swaps = []
        all_memos = []

        for action in actions:
            try:
                memo = action.get("metadata", {}).get("swap", {}).get("memo", "")
                if memo:
                    all_memos.append(memo)

                    # Check for :ss: pattern
                    if ":ss:" in memo.lower():
                        ss_swaps.append(
                            {
                                "tx_id": action.get("txID", ""),
                                "height": action.get("height", 0),
                                "memo": memo,
                            }
                        )
            except Exception as e:
                continue

        print(f"📊 Total swaps with memos: {len(all_memos)}")
        print(f"🎯 Swaps with ':ss:' pattern: {len(ss_swaps)}")

        if ss_swaps:
            print(f"\n✅ Found {len(ss_swaps)} ShapeShift affiliate swaps!")
            for i, swap in enumerate(ss_swaps[:10]):  # Show first 10
                print(f"   {i+1}. Block {swap['height']}: {swap['tx_id']}")
                print(f"      Memo: {swap['memo']}")
                print()
        else:
            print("\nℹ️  No swaps found with ':ss:' pattern")
            print("📋 Sample memos (first 10):")
            for i, memo in enumerate(all_memos[:10]):
                print(f"   {i+1}: {memo}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    search_ss_memos()
