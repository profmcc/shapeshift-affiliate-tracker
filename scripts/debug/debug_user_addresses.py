#!/usr/bin/env python3
"""
Debug User Addresses
Debug why user addresses are being filtered out in Relay transactions.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def debug_user_addresses():
    """
    Debug why user addresses are being filtered out.
    """
    print("🔍 Debugging User Addresses...")

    try:
        # Connect to Base chain
        w3 = Web3(
            Web3.HTTPProvider(
                "https://base-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"
            )
        )
        if not w3.is_connected():
            print("❌ Failed to connect to Base chain")
            return

        print("✅ Connected to Base chain")

        # Use one of the transaction hashes from the previous analysis
        tx_hash = "0xecd80f3367bb3c4d2a7e713c79c523f51fe1845627933f52ff572b6f2dfbf295"
        print(f"🔍 Analyzing transaction: {tx_hash}")

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"📊 Transaction receipt found with {len(receipt['logs'])} logs")

        # Router addresses to exclude
        router_addresses = [
            "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
            "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
        ]

        # Analyze each log for user addresses
        all_addresses = []
        for i, log in enumerate(receipt["logs"]):
            if (
                log.get("topics")
                and len(log["topics"]) == 3
                and log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                from_addr = "0x" + log["topics"][1][-40:].hex()
                to_addr = "0x" + log["topics"][2][-40:].hex()

                print(f"\n📋 Transfer {i}:")
                print(f"   From: {from_addr}")
                print(f"   To: {to_addr}")
                print(f"   Token: {log['address']}")

                # Check why addresses are being filtered
                is_router = from_addr.lower() in [r.lower() for r in router_addresses]
                is_zero = from_addr == "0x0000000000000000000000000000000000000000"
                starts_with_zero = from_addr.startswith("0x000000000000000000000000")

                print(f"   Is router: {is_router}")
                print(f"   Is zero: {is_zero}")
                print(f"   Starts with zero: {starts_with_zero}")

                if not (is_router or is_zero or starts_with_zero):
                    print(f"   ✅ Would be included as user")
                    all_addresses.append(from_addr)
                else:
                    print(f"   ❌ Filtered out")

                # Also check to address
                is_router_to = to_addr.lower() in [r.lower() for r in router_addresses]
                is_zero_to = to_addr == "0x0000000000000000000000000000000000000000"
                starts_with_zero_to = to_addr.startswith("0x000000000000000000000000")

                if not (is_router_to or is_zero_to or starts_with_zero_to):
                    print(f"   ✅ To address would be included as user")
                    all_addresses.append(to_addr)
                else:
                    print(f"   ❌ To address filtered out")

        print(f"\n📊 SUMMARY:")
        print(f"   Total addresses found: {len(all_addresses)}")
        print(f"   Unique addresses: {len(set(all_addresses))}")

        if all_addresses:
            print(f"   Addresses: {list(set(all_addresses))}")
        else:
            print(f"   ❌ No user addresses found - all filtered out")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_user_addresses()
