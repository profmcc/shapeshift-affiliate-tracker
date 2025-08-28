#!/usr/bin/env python3
"""
Test the Relay listener's detection logic to see why it's not finding affiliate transactions.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def test_relay_listener_detection():
    """Test the Relay listener's detection logic."""

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
    affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

    print(f"\n🔍 Testing Relay listener detection logic on transaction: {tx_hash}")

    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(
            f"📊 Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}"
        )
        print(f"📊 Block number: {receipt['blockNumber']}")
        print(f"📊 Number of logs: {len(receipt['logs'])}")

        # Test the listener's detection logic
        print(f"\n🔍 Testing affiliate fee detection...")

        found_affiliate_fees = []

        for idx, log in enumerate(receipt["logs"]):
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

                print(f"   Transfer {idx}:")
                print(f"      From: {from_addr}")
                print(f"      To: {to_addr}")
                print(f"      Token: {log['address']}")

                # Parse amount
                amount = 0
                if len(log["data"]) >= 32:
                    try:
                        amount = int.from_bytes(log["data"][:32], "big")
                        print(f"      Amount: {amount}")
                    except:
                        print(f"      Amount: Could not parse")

                # Check if this is a transfer TO the affiliate address
                if to_addr.lower() == affiliate_address.lower():
                    print(f"      ✅ AFFILIATE FEE DETECTED!")
                    found_affiliate_fees.append(
                        {
                            "from": from_addr,
                            "to": to_addr,
                            "token": log["address"],
                            "amount": amount,
                            "log_index": idx,
                        }
                    )

                # Check if this is a transfer FROM the affiliate address
                elif from_addr.lower() == affiliate_address.lower():
                    print(f"      🔄 AFFILIATE SENDING TOKENS")

        print(f"\n📊 Detection Results:")
        print(f"   Found {len(found_affiliate_fees)} affiliate fee transfers")

        for i, fee in enumerate(found_affiliate_fees):
            print(f"   Fee {i+1}:")
            print(f"      From: {fee['from']}")
            print(f"      To: {fee['to']}")
            print(f"      Token: {fee['token']}")
            print(f"      Amount: {fee['amount']}")
            print(f"      Log Index: {fee['log_index']}")

        # Test the listener's trading pair extraction
        print(f"\n🔍 Testing trading pair extraction...")

        # This would require the full listener logic, but let's check if we can identify the trading pair
        router_addresses = [
            "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
            "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
        ]

        # Look for transfers involving router addresses
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

        for i, transfer in enumerate(router_transfers):
            print(f"   Router Transfer {i+1}:")
            print(f"      From: {transfer['from']}")
            print(f"      To: {transfer['to']}")
            print(f"      Token: {transfer['token']}")

    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")


if __name__ == "__main__":
    test_relay_listener_detection()
