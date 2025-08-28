#!/usr/bin/env python3
"""
Debug Relay Transfer Parsing
Analyzes a specific Relay transaction to understand why transfer parsing is failing.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def debug_relay_transfer_parsing():
    """
    Debug the transfer parsing issue in Relay transactions.
    """
    print("🔍 Debugging Relay Transfer Parsing...")

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
        tx_hash = "0x5fa5e64509689c20591c7268a70f2f7e77864b633b06df499b7607986ec23167"
        print(f"🔍 Analyzing transaction: {tx_hash}")

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"📊 Transaction receipt found with {len(receipt['logs'])} logs")

        # Analyze each log in detail
        for i, log in enumerate(receipt["logs"]):
            print(f"\n📋 Log {i}:")
            print(f"   Address: {log['address']}")
            print(f"   Topics: {len(log['topics'])}")

            for j, topic in enumerate(log["topics"]):
                print(f"   Topic {j}: {topic.hex()}")

            print(f"   Data length: {len(log['data'])} bytes")
            print(f"   Data: {log['data'].hex()}")

            # Check if this looks like an ERC-20 transfer
            if len(log["topics"]) >= 3:
                topic0 = log["topics"][0].hex()
                print(f"   Topic 0: {topic0}")

                # ERC-20 Transfer event signature
                transfer_signature = (
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                )

                if topic0 == transfer_signature:
                    print(f"   ✅ This is an ERC-20 transfer!")

                    # Parse from and to addresses
                    from_addr = "0x" + log["topics"][1][-40:].hex()
                    to_addr = "0x" + log["topics"][2][-40:].hex()

                    print(f"   From: {from_addr}")
                    print(f"   To: {to_addr}")

                    # Parse amount
                    if len(log["data"]) >= 32:
                        try:
                            amount = int.from_bytes(log["data"][:32], "big")
                            print(f"   Amount: {amount}")
                        except Exception as e:
                            print(f"   ❌ Error parsing amount: {e}")
                    else:
                        print(f"   ❌ Data too short for amount parsing")
                else:
                    print(
                        f"   ❌ Not an ERC-20 transfer (expected {transfer_signature})"
                    )
            else:
                print(f"   ❌ Not enough topics for ERC-20 transfer")

        # Look for ShapeShift affiliate address
        affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"
        print(f"\n🔍 Looking for ShapeShift affiliate address: {affiliate_address}")

        found_affiliate = False
        for i, log in enumerate(receipt["logs"]):
            for j, topic in enumerate(log["topics"]):
                if affiliate_address.lower() in topic.hex().lower():
                    print(f"   ✅ Found affiliate address in log {i}, topic {j}")
                    found_affiliate = True

        if not found_affiliate:
            print(f"   ❌ No affiliate address found in any logs")

        # Check transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"\n📋 Transaction Details:")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {tx['value']}")
        print(f"   Input data length: {len(tx['input'])}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_relay_transfer_parsing()
