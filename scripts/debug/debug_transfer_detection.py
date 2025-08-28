#!/usr/bin/env python3
"""
Debug Transfer Detection
Debug why the transfer detection is still failing in Relay transactions.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def debug_transfer_detection():
    """
    Debug why transfer detection is failing.
    """
    print("🔍 Debugging Transfer Detection...")

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
        tx_hash = "0x8e8b596d6f575710b4fe91d89ddb22d4337c16ee85ee1a12821b5fb5f4a24c6f"
        print(f"🔍 Analyzing transaction: {tx_hash}")

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"📊 Transaction receipt found with {len(receipt['logs'])} logs")

        # Expected ERC-20 transfer signature
        expected_signature = (
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )
        print(f"🔍 Expected signature: {expected_signature}")

        # Analyze each log for transfer detection
        transfer_count = 0
        for i, log in enumerate(receipt["logs"]):
            print(f"\n📋 Log {i}:")
            print(f"   Address: {log['address']}")
            print(f"   Topics: {len(log['topics'])}")

            if len(log["topics"]) >= 3:
                topic0 = log["topics"][0].hex()
                print(f"   Topic 0: {topic0}")
                print(f"   Expected: {expected_signature}")
                print(f"   Match: {topic0 == expected_signature}")

                if topic0 == expected_signature:
                    print(f"   ✅ This is an ERC-20 transfer!")
                    transfer_count += 1

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
                    print(f"   ❌ Not an ERC-20 transfer")
            else:
                print(f"   ❌ Not enough topics for ERC-20 transfer")

        print(f"\n📊 SUMMARY:")
        print(f"   Total logs: {len(receipt['logs'])}")
        print(f"   Transfer logs found: {transfer_count}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_transfer_detection()
