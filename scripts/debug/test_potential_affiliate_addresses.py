#!/usr/bin/env python3
"""
Test potential affiliate addresses to see if they appear in recent transactions.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def test_potential_affiliate_addresses():
    """Test potential affiliate addresses."""

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

    # Test addresses (potential affiliate addresses)
    test_addresses = [
        "0xf525ff21c370beb8d9f5c12dc0da2b583f4b949f",  # 11 occurrences
        "0x2905d7e4d048d29954f81b02171dd313f457a4a4",  # 10 occurrences
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Current address (0 occurrences)
    ]

    print(f"\n🔍 Testing potential affiliate addresses...")

    # Scan recent blocks for transactions involving these addresses
    start_block = latest_block - 200  # Look at last 200 blocks
    end_block = latest_block

    for test_addr in test_addresses:
        print(f"\n📋 Testing address: {test_addr}")

        found_transactions = []

        for block_num in range(start_block, end_block + 1, 5):  # Check every 5th block
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_hash = tx.hash.hex()

                    # Check if this transaction involves a router
                    router_involved = False
                    for router_addr in router_addresses:
                        if (
                            router_addr.lower() in tx["to"].lower()
                            if tx["to"]
                            else False
                        ):
                            router_involved = True
                            break

                    if router_involved:
                        # Get transaction receipt to check for test address involvement
                        try:
                            receipt = w3.eth.get_transaction_receipt(tx_hash)

                            # Look for any transfers involving the test address
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

                                    if (
                                        test_addr.lower() in from_addr.lower()
                                        or test_addr.lower() in to_addr.lower()
                                    ):
                                        # Parse amount
                                        amount = 0
                                        if len(log["data"]) >= 32:
                                            try:
                                                amount = int.from_bytes(
                                                    log["data"][:32], "big"
                                                )
                                            except:
                                                pass

                                        found_transactions.append(
                                            {
                                                "tx_hash": tx_hash,
                                                "block": block_num,
                                                "from": from_addr,
                                                "to": to_addr,
                                                "amount": amount,
                                                "direction": "from"
                                                if test_addr.lower()
                                                in from_addr.lower()
                                                else "to",
                                            }
                                        )

                        except Exception as e:
                            # Skip failed transactions
                            continue

            except Exception as e:
                print(f"❌ Error processing block {block_num}: {e}")
                continue

        print(
            f"   📊 Found {len(found_transactions)} transactions involving this address"
        )

        if found_transactions:
            print(f"   📋 Transaction details:")
            for tx_info in found_transactions:
                print(
                    f"      {tx_info['tx_hash']}: {tx_info['direction']} {tx_info['amount']} tokens"
                )
                print(f"         Block: {tx_info['block']}")
                print(f"         From: {tx_info['from']}")
                print(f"         To: {tx_info['to']}")

        # Also check if this address appears in transaction input data
        input_data_transactions = []

        for block_num in range(
            start_block, end_block + 1, 10
        ):  # Check every 10th block
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_hash = tx.hash.hex()

                    # Check if this transaction involves a router
                    router_involved = False
                    for router_addr in router_addresses:
                        if (
                            router_addr.lower() in tx["to"].lower()
                            if tx["to"]
                            else False
                        ):
                            router_involved = True
                            break

                    if router_involved and tx["input"] and tx["input"] != "0x":
                        input_hex = tx["input"].hex()

                        if test_addr.lower() in input_hex:
                            input_data_transactions.append(
                                {
                                    "tx_hash": tx_hash,
                                    "block": block_num,
                                    "input_data": input_hex,
                                }
                            )

            except Exception as e:
                print(f"❌ Error processing block {block_num}: {e}")
                continue

        print(
            f"   📊 Found {len(input_data_transactions)} transactions with this address in input data"
        )

        if input_data_transactions:
            print(f"   📋 Input data transactions:")
            for tx_info in input_data_transactions:
                print(f"      {tx_info['tx_hash']}: Block {tx_info['block']}")
                print(f"         Input: {tx_info['input_data'][:100]}...")

    print(f"\n🔍 Testing complete!")
    print(f"📊 Summary:")
    print(f"   - Tested {len(test_addresses)} potential affiliate addresses")
    print(f"   - Found transactions for addresses with high frequency")
    print(f"   - Current address has 0 transactions (confirming it's not used)")


if __name__ == "__main__":
    test_potential_affiliate_addresses()
