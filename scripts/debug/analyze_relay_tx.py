#!/usr/bin/env python3
"""
Analyze Relay Transaction
Analyzes a specific Relay transaction to understand the structure and find affiliate fees.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def analyze_relay_transaction():
    """
    Analyze a specific Relay transaction in detail.
    """
    print("🔍 Analyzing Relay transaction...")

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

        # Get a recent Relay transaction
        latest_block = w3.eth.block_number
        print(f"📊 Latest block: {latest_block}")

        # Look for Relay router logs in recent blocks
        router_address = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

        filter_params = {
            "fromBlock": latest_block - 50,
            "toBlock": latest_block,
            "address": router_address,
        }

        logs = w3.eth.get_logs(filter_params)
        print(f"📊 Found {len(logs)} Relay router logs")

        if not logs:
            print("❌ No Relay router logs found")
            return

        # Analyze the first transaction
        tx_hash = logs[0]["transactionHash"].hex()
        print(f"\n🔍 Analyzing transaction: {tx_hash}")

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"📊 Transaction has {len(receipt['logs'])} logs")

        # Check for affiliate address
        affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"
        affiliate_clean = affiliate_address.lower()

        print(f"\n🔍 Looking for affiliate address: {affiliate_address}")

        affiliate_found = False
        for i, log in enumerate(receipt["logs"]):
            print(f"\n📋 Log {i}:")
            print(f"   Address: {log['address']}")
            print(f"   Topics: {[topic.hex() for topic in log['topics']]}")
            print(f"   Data: {log['data'].hex()}")

            # Check if affiliate address appears in topics or data
            for topic in log["topics"]:
                if affiliate_clean in topic.hex().lower():
                    print(f"   ✅ Found affiliate address in topic!")
                    affiliate_found = True

            if affiliate_clean in log["data"].hex().lower():
                print(f"   ✅ Found affiliate address in data!")
                affiliate_found = True

        if not affiliate_found:
            print(f"\n❌ Affiliate address {affiliate_address} not found in transaction")

            # Let's check what addresses are actually in the transaction
            print(f"\n📋 All addresses in transaction:")
            addresses = set()
            for log in receipt["logs"]:
                addresses.add(log["address"])

            for addr in sorted(addresses):
                print(f"   {addr}")

        # Check for ERC-20 transfers
        print(f"\n🔍 Looking for ERC-20 transfers...")
        transfer_topic = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        transfers = []
        for log in receipt["logs"]:
            if log["topics"] and log["topics"][0].hex() == transfer_topic:
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()

                # Decode amount
                amount = 0
                if len(log["data"]) >= 32:
                    try:
                        amount = int.from_bytes(log["data"][:32], "big")
                    except:
                        pass

                transfer = {
                    "token": log["address"],
                    "from": from_addr,
                    "to": to_addr,
                    "amount": amount,
                }
                transfers.append(transfer)

                print(f"   Transfer: {from_addr} -> {to_addr} ({amount} tokens)")
                print(f"   Token: {log['address']}")

        print(f"\n📊 Found {len(transfers)} ERC-20 transfers")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_relay_transaction()
