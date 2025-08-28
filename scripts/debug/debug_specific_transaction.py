#!/usr/bin/env python3
"""
Debug script to analyze a specific successful router transaction in detail.
This will help us understand the transaction structure and how affiliate fees might be recorded.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def debug_specific_transaction():
    """Debug a specific successful router transaction."""

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

    # Analyze a specific successful transaction from the debug output
    tx_hash = "0x6d688cc41d208c4b7dd1bce9a174e65201fc6beecdb43ad0edcaba6d6ed69c96"

    print(f"\n🔍 Analyzing transaction: {tx_hash}")

    try:
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"📊 Transaction Details:")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {tx['value']} wei")
        print(f"   Gas: {tx['gas']}")
        print(f"   Gas Price: {tx['gasPrice']} wei")
        print(f"   Input Data: {tx['input']}")

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"\n📊 Receipt Details:")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Gas Used: {receipt['gasUsed']}")
        print(f"   Logs: {len(receipt['logs'])}")

        # Analyze all logs in detail
        print(f"\n📋 Detailed Log Analysis:")

        for i, log in enumerate(receipt["logs"]):
            print(f"\n   Log {i}:")
            print(f"      Address: {log['address']}")
            print(f"      Topics: {[topic.hex() for topic in log['topics']]}")
            print(f"      Data: {log['data'].hex()}")

            # Check if this is an ERC-20 transfer
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

                print(f"      ✅ ERC-20 Transfer:")
                print(f"         From: {from_addr}")
                print(f"         To: {to_addr}")

                # Parse amount from data
                if len(log["data"]) >= 32:
                    try:
                        amount = int.from_bytes(log["data"][:32], "big")
                        print(f"         Amount: {amount}")
                    except:
                        print(f"         Amount: Could not parse")

                # Check if this involves any known addresses
                known_addresses = [
                    "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # ShapeShift affiliate
                    "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",  # Router
                    "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",  # Router
                ]

                for known_addr in known_addresses:
                    if (
                        known_addr.lower() in from_addr.lower()
                        or known_addr.lower() in to_addr.lower()
                    ):
                        print(f"         🎯 Involves known address: {known_addr}")

            # Check for other event signatures that might indicate affiliate fees
            if log.get("topics") and len(log["topics"]) > 0:
                event_signature = log["topics"][0].hex()
                print(f"      Event Signature: {event_signature}")

                # Common event signatures that might be relevant
                known_signatures = {
                    "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "ERC-20 Transfer",
                    "8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "ERC-20 Approval",
                    "17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31": "ApprovalForAll",
                }

                if event_signature in known_signatures:
                    print(f"      📝 Known Event: {known_signatures[event_signature]}")
                else:
                    print(f"      ❓ Unknown Event Signature")

        # Look for any internal transactions or calls
        print(f"\n🔍 Checking for internal transactions...")

        # This would require a different approach - we'd need to trace the transaction
        # For now, let's just look at the input data more carefully

        if tx["input"] and tx["input"] != "0x":
            print(f"\n📝 Input Data Analysis:")
            print(f"   Raw Input: {tx['input']}")

            # Try to decode the input data
            if len(tx["input"]) >= 10:  # At least 4 bytes for function selector
                function_selector = tx["input"][:10]
                print(f"   Function Selector: {function_selector}")

                # Common function selectors for swap functions
                known_selectors = {
                    "0x38ed1739": "swapExactTokensForTokens",
                    "0x7ff36ab5": "swapExactETHForTokens",
                    "0x18cbafe5": "swapExactTokensForETH",
                    "0xfb3bdb41": "swap",
                    "0x5c11d795": "multicall",
                }

                if function_selector in known_selectors:
                    print(f"   📝 Known Function: {known_selectors[function_selector]}")
                else:
                    print(f"   ❓ Unknown Function Selector")

    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")


if __name__ == "__main__":
    debug_specific_transaction()
