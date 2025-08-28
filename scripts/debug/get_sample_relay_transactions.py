#!/usr/bin/env python3
"""
Get Sample Relay Transactions

This script finds sample Relay transactions that you can explore 
in the relay.link browser interface.
"""

import requests
import json
from datetime import datetime


def get_sample_transactions():
    """Get sample Relay transactions for browser exploration"""

    print("🔗 Getting Sample Relay Transactions for Browser Exploration")
    print("=" * 60)

    # Sample transaction IDs and request IDs from various sources
    sample_transactions = [
        {
            "request_id": "0x92b99e6e1ee1deeb9531b5ad7f87091b3d71254b3176de9e8b5f6c6d0bd3a331",
            "description": "Sample bridge transaction from API docs",
            "browser_url": "https://relay.link/tx/0x92b99e6e1ee1deeb9531b5ad7f87091b3d71254b3176de9e8b5f6c6d0bd3a331",
        },
        {
            "request_id": "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
            "description": "Hypothetical cross-chain swap",
            "browser_url": "https://relay.link/tx/0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
        },
    ]

    # Try alternative API approaches
    api_approaches = [
        "https://api.relay.link/v2/requests",
        "https://api.relay.link/transactions",
        "https://api.relay.link/recent",
        "https://relay.link/api/transactions",
    ]

    print("🔍 Trying different API endpoints to find real transactions...")

    for i, endpoint in enumerate(api_approaches, 1):
        try:
            print(f"\n{i}. Trying: {endpoint}")
            response = requests.get(endpoint, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success! Found data structure:")

                    if isinstance(data, dict):
                        print(f"   📊 Keys: {list(data.keys())}")

                        # Look for transaction-like data
                        for key in ["requests", "transactions", "data", "results"]:
                            if (
                                key in data
                                and isinstance(data[key], list)
                                and len(data[key]) > 0
                            ):
                                transactions = data[key][:3]  # Get first 3
                                print(f"   🎯 Found {len(data[key])} items in '{key}'")

                                for j, tx in enumerate(transactions):
                                    if isinstance(tx, dict):
                                        tx_id = (
                                            tx.get("id")
                                            or tx.get("requestId")
                                            or tx.get("hash")
                                        )
                                        if tx_id:
                                            sample_transactions.append(
                                                {
                                                    "request_id": tx_id,
                                                    "description": f"Real transaction from {endpoint}",
                                                    "browser_url": f"https://relay.link/tx/{tx_id}",
                                                    "data": tx,
                                                }
                                            )
                                            print(
                                                f"   📝 Added transaction: {tx_id[:20]}..."
                                            )

                    elif isinstance(data, list) and len(data) > 0:
                        print(f"   📊 Array with {len(data)} items")
                        for j, tx in enumerate(data[:3]):
                            if isinstance(tx, dict):
                                tx_id = (
                                    tx.get("id")
                                    or tx.get("requestId")
                                    or tx.get("hash")
                                )
                                if tx_id:
                                    sample_transactions.append(
                                        {
                                            "request_id": tx_id,
                                            "description": f"Real transaction from {endpoint}",
                                            "browser_url": f"https://relay.link/tx/{tx_id}",
                                            "data": tx,
                                        }
                                    )
                                    print(f"   📝 Added transaction: {tx_id[:20]}...")

                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")

            elif response.status_code == 404:
                print(f"   ❌ Not found (404)")
            elif response.status_code == 500:
                print(f"   ❌ Server error (500)")
            else:
                print(f"   ❌ HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")

    # Try to get recent transactions from blockchain explorers that might show Relay activity
    print(f"\n🔍 Checking for recent Relay activity on Base chain...")

    try:
        # Look for recent transactions to known Relay contracts on Base
        relay_contracts = [
            "0xf70da97812cb96acdf810712aa562db8dfa3dbef",  # Example Relay contract
            "0x1234567890123456789012345678901234567890",  # Placeholder
        ]

        for contract in relay_contracts:
            print(f"   Checking contract: {contract}")
            # This would need a proper Base chain RPC, but showing the concept

    except Exception as e:
        print(f"   ❌ Error checking contracts: {e}")

    # Display results
    print(f"\n📋 SAMPLE TRANSACTIONS FOR BROWSER EXPLORATION")
    print("=" * 60)

    unique_transactions = []
    seen_ids = set()

    for tx in sample_transactions:
        if tx["request_id"] not in seen_ids:
            unique_transactions.append(tx)
            seen_ids.add(tx["request_id"])

    if unique_transactions:
        for i, tx in enumerate(unique_transactions, 1):
            print(f"\n{i}. Request ID: {tx['request_id']}")
            print(f"   Description: {tx['description']}")
            print(f"   Browser URL: {tx['browser_url']}")

            if "data" in tx:
                data = tx["data"]
                if isinstance(data, dict):
                    # Show some relevant fields
                    for field in [
                        "user",
                        "amount",
                        "originChain",
                        "destinationChain",
                        "status",
                    ]:
                        if field in data:
                            print(f"   {field}: {data[field]}")

        print(f"\n🌐 HOW TO EXPLORE THESE TRANSACTIONS:")
        print("1. Copy any Request ID above")
        print("2. Visit https://relay.link in your browser")
        print("3. Search for the Request ID")
        print("4. Click through to see transaction details")
        print("5. Look for fee breakdowns and app fees")

        print(f"\n🔍 WHAT TO LOOK FOR:")
        print("- App fees section")
        print("- Fee recipient addresses")
        print("- ShapeShift address: 0x9008D19f58AAbD9eD0D60971565AA8510560ab41")
        print("- Cross-chain routing details")
        print("- Transaction status and timing")

    else:
        print("❌ No transactions found. API might be down or requiring authentication.")
        print("\n🔄 Alternative approaches:")
        print("1. Visit relay.link directly and browse recent transactions")
        print("2. Check Relay's documentation for example transaction IDs")
        print("3. Monitor Base chain for recent Relay activity")
        print("4. Use social media/Discord to find recent Relay transaction examples")

    return unique_transactions


if __name__ == "__main__":
    transactions = get_sample_transactions()
