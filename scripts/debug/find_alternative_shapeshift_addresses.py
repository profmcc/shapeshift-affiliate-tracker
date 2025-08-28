#!/usr/bin/env python3
"""
Search for alternative ShapeShift addresses that might be used for affiliate fees.
This will help us identify the correct address to look for in transactions.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def find_alternative_shapeshift_addresses():
    """Search for alternative ShapeShift addresses."""

    # Initialize Web3 connection
    infura_key = os.getenv("INFURA_API_KEY")
    if not infura_key:
        print("❌ INFURA_API_KEY not found in environment variables")
        return

    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.infura.io/v3/{infura_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base chain")
        return

    print("✅ Connected to Base chain")

    # Get latest block
    latest_block = w3.eth.block_number
    print(f"📊 Latest block: {latest_block}")

    # Router addresses
    router_addresses = [
        "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
        "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
    ]

    # Current ShapeShift address
    current_shapeshift = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

    print(f"\n🔍 Searching for alternative ShapeShift addresses...")

    # Method 1: Look for addresses that appear frequently in router transactions
    print(f"\n📋 Method 1: Analyzing frequent addresses in router transactions")

    # Scan recent blocks for router transactions and collect all addresses
    start_block = latest_block - 100  # Look at last 100 blocks
    end_block = latest_block

    address_frequency = {}
    router_transactions = []

    for block_num in range(start_block, end_block + 1, 2):  # Check every 2nd block
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                # Check if this transaction involves a router
                router_involved = False
                for router_addr in router_addresses:
                    if router_addr.lower() in tx["to"].lower() if tx["to"] else False:
                        router_involved = True
                        break

                if router_involved:
                    router_transactions.append(tx_hash)

                    # Get transaction receipt to collect all addresses
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx_hash)

                        # Collect addresses from all ERC-20 transfers
                        for log in receipt["logs"]:
                            if (
                                log.get("topics")
                                and len(log["topics"]) == 3
                                and log["topics"][0].hex()
                                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                            ):
                                from_addr_raw = log["topics"][1].hex()
                                to_addr_raw = log["topics"][2].hex()

                                from_addr = "0x" + from_addr_raw[-40:]
                                to_addr = "0x" + to_addr_raw[-40:]

                                # Count address frequency
                                address_frequency[from_addr] = (
                                    address_frequency.get(from_addr, 0) + 1
                                )
                                address_frequency[to_addr] = (
                                    address_frequency.get(to_addr, 0) + 1
                                )

                    except Exception as e:
                        # Skip failed transactions
                        continue

        except Exception as e:
            print(f"❌ Error processing block {block_num}: {e}")
            continue

    print(f"\n📊 Found {len(router_transactions)} router transactions")
    print(f"📊 Collected {len(address_frequency)} unique addresses")

    # Show most frequent addresses
    sorted_addresses = sorted(
        address_frequency.items(), key=lambda x: x[1], reverse=True
    )
    print(f"\n🏆 Most frequent addresses in router transactions:")

    for i, (addr, count) in enumerate(sorted_addresses[:20]):
        print(f"   {i+1}. {addr}: {count} occurrences")

        # Check if this could be a ShapeShift address
        if count >= 3:  # Address appears in multiple transactions
            print(f"      ⚠️  Potential affiliate address (appears {count} times)")

    # Method 2: Look for addresses that might be ShapeShift-related
    print(f"\n📋 Method 2: Searching for ShapeShift-related addresses")

    # Common patterns for ShapeShift addresses
    shapeshift_patterns = [
        "shapeshift",
        "affiliate",
        "fee",
        "treasury",
        "dao",
        "gov",
        "9c9a",  # Part of current address
        "9036",  # Part of current address
        "630d",  # Part of current address
    ]

    potential_shapeshift_addresses = []

    for addr, count in sorted_addresses:
        addr_lower = addr.lower()

        # Check if address contains any ShapeShift-related patterns
        for pattern in shapeshift_patterns:
            if pattern in addr_lower:
                potential_shapeshift_addresses.append((addr, count, pattern))
                break

        # Also check if address appears frequently (potential affiliate address)
        if count >= 5:
            potential_shapeshift_addresses.append((addr, count, "frequent"))

    print(f"\n🎯 Potential ShapeShift addresses:")
    for addr, count, reason in potential_shapeshift_addresses:
        print(f"   {addr}: {count} occurrences (reason: {reason})")

    # Method 3: Compare with current address
    print(f"\n📋 Method 3: Comparing with current ShapeShift address")
    print(f"   Current address: {current_shapeshift}")
    print(
        f"   Current address frequency: {address_frequency.get(current_shapeshift, 0)}"
    )

    if current_shapeshift in address_frequency:
        print(f"   ✅ Current address found in recent transactions")
    else:
        print(f"   ❌ Current address NOT found in recent transactions")
        print(f"   🔍 This suggests we need a different address")

    print(f"\n🔍 Search complete!")
    print(f"📊 Summary:")
    print(f"   - Analyzed {len(router_transactions)} router transactions")
    print(f"   - Found {len(address_frequency)} unique addresses")
    print(
        f"   - Identified {len(potential_shapeshift_addresses)} potential ShapeShift addresses"
    )
    print(
        f"   - Current address frequency: {address_frequency.get(current_shapeshift, 0)}"
    )


if __name__ == "__main__":
    find_alternative_shapeshift_addresses()
