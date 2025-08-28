#!/usr/bin/env python3
"""
Test the Relay listener's logic directly on the specific transaction we found.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def test_specific_transaction():
    """Test the Relay listener's logic on a specific transaction."""

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

    # Test the specific transaction we found
    tx_hash = "0x82e227c1a0ad367e05de21fd49bc375a261a7dd6cfd6d7e0196365e70e884bb0"
    affiliate_address = "0x2905d7e4d048d29954f81b02171dd313f457a4a4"

    print(f"\n🔍 Testing Relay listener logic on transaction: {tx_hash}")

    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(
            f"📊 Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}"
        )
        print(f"📊 Block number: {receipt['blockNumber']}")

        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"📊 Transaction to: {tx['to']}")

        # Check if this transaction involves a router
        router_addresses = [
            "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
            "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
        ]

        router_involved = False
        for router_addr in router_addresses:
            if router_addr.lower() in tx["to"].lower() if tx["to"] else False:
                router_involved = True
                break

        print(f"📊 Router involved: {router_involved}")

        if not router_involved:
            print("❌ Transaction doesn't involve a router - listener would skip this")
            return

        # Test the affiliate fee detection logic
        print(f"\n🔍 Testing affiliate fee detection...")

        found_affiliate_fees = []

        for idx, log in enumerate(receipt["logs"]):
            if (
                log.get("topics")
                and len(log["topics"]) == 3
                and log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                to_address = "0x" + log["topics"][2].hex()[-40:]

                if to_address.lower() == affiliate_address.lower():
                    token_address = log["address"]

                    # Parse amount (simplified version of _safe_parse_amount)
                    amount = "0"
                    if len(log["data"]) >= 32:
                        try:
                            amount_int = int.from_bytes(log["data"][:32], "big")
                            amount = str(amount_int)
                        except:
                            pass

                    print(f"✅ Found affiliate fee transfer!")
                    print(f"   Token: {token_address}")
                    print(f"   Amount: {amount}")
                    print(f"   Log Index: {idx}")

                    found_affiliate_fees.append(
                        {"token": token_address, "amount": amount, "log_index": idx}
                    )

        print(f"\n📊 Results:")
        print(f"   Found {len(found_affiliate_fees)} affiliate fee transfers")

        if found_affiliate_fees:
            print("✅ The listener SHOULD detect this transaction!")
        else:
            print("❌ The listener would NOT detect this transaction")

        # Test trading pair extraction (simplified)
        print(f"\n🔍 Testing trading pair extraction...")

        # Look for transfers involving router addresses to identify trading pair
        router_transfers = []
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

                for router_addr in router_addresses:
                    if (
                        router_addr.lower() in from_addr.lower()
                        or router_addr.lower() in to_addr.lower()
                    ):
                        router_transfers.append(
                            {"from": from_addr, "to": to_addr, "token": log["address"]}
                        )
                        break

        print(f"   Found {len(router_transfers)} transfers involving router addresses")

        if router_transfers:
            print("✅ Trading pair extraction should work")
        else:
            print("❌ Trading pair extraction might fail")

    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")


if __name__ == "__main__":
    test_specific_transaction()
