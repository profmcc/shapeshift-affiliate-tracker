#!/usr/bin/env python3
"""
Debug script to investigate how affiliate fees are recorded in Relay transactions.
This will help us understand why we're not finding affiliate transactions despite
the user indicating there should be recent trades.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def debug_affiliate_fee_detection():
    """Debug affiliate fee detection in Relay transactions."""

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

    # Router addresses to check
    router_addresses = [
        "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
        "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
    ]

    # Known ShapeShift addresses (potential affiliate addresses)
    shapeshift_addresses = [
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Current affiliate address
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower(),  # Lowercase version
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".upper(),  # Uppercase version
    ]

    # Scan recent blocks for any transaction involving ShapeShift addresses
    print("\n🔍 Scanning for any transactions involving ShapeShift addresses...")

    # Check last 1000 blocks
    start_block = latest_block - 1000
    end_block = latest_block

    for block_num in range(start_block, end_block + 1, 100):  # Check every 100th block
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                # Check if any ShapeShift address is involved in this transaction
                shapeshift_involved = False
                for shapeshift_addr in shapeshift_addresses:
                    if (
                        shapeshift_addr.lower() in tx["to"].lower()
                        if tx["to"]
                        else False or shapeshift_addr.lower() in tx["from"].lower()
                    ):
                        shapeshift_involved = True
                        break

                if shapeshift_involved:
                    print(
                        f"\n🎯 Found transaction involving ShapeShift address: {tx_hash}"
                    )
                    print(f"   From: {tx['from']}")
                    print(f"   To: {tx['to']}")
                    print(f"   Block: {block_num}")

                    # Get transaction receipt
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        print(
                            f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}"
                        )

                        # Analyze all logs in this transaction
                        print(f"   📊 Found {len(receipt['logs'])} logs")

                        for i, log in enumerate(receipt["logs"]):
                            print(f"      Log {i}:")
                            print(f"         Address: {log['address']}")
                            print(
                                f"         Topics: {[topic.hex() for topic in log['topics']]}"
                            )
                            print(f"         Data: {log['data'].hex()}")

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

                                print(f"         ✅ ERC-20 Transfer:")
                                print(f"            From: {from_addr}")
                                print(f"            To: {to_addr}")

                                # Check if this involves a ShapeShift address
                                for shapeshift_addr in shapeshift_addresses:
                                    if (
                                        shapeshift_addr.lower() in from_addr.lower()
                                        or shapeshift_addr.lower() in to_addr.lower()
                                    ):
                                        print(f"         🎯 SHAPESHIFT INVOLVED!")
                                        print(
                                            f"            ShapeShift address: {shapeshift_addr}"
                                        )
                                        break

                    except Exception as e:
                        print(f"   ❌ Error getting receipt: {e}")

                # Also check if this transaction involves any router address
                router_involved = False
                for router_addr in router_addresses:
                    if router_addr.lower() in tx["to"].lower() if tx["to"] else False:
                        router_involved = True
                        break

                if router_involved:
                    print(f"\n🔧 Found transaction involving router: {tx_hash}")
                    print(f"   From: {tx['from']}")
                    print(f"   To: {tx['to']}")
                    print(f"   Block: {block_num}")

                    # Get transaction receipt for router transactions
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        print(
                            f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}"
                        )

                        # Look for any transfers to ShapeShift addresses
                        for i, log in enumerate(receipt["logs"]):
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

                                # Check if this transfer involves a ShapeShift address
                                for shapeshift_addr in shapeshift_addresses:
                                    if (
                                        shapeshift_addr.lower() in from_addr.lower()
                                        or shapeshift_addr.lower() in to_addr.lower()
                                    ):
                                        print(
                                            f"   🎯 Found transfer involving ShapeShift in router transaction!"
                                        )
                                        print(f"      From: {from_addr}")
                                        print(f"      To: {to_addr}")
                                        print(
                                            f"      ShapeShift address: {shapeshift_addr}"
                                        )
                                        break

                    except Exception as e:
                        print(f"   ❌ Error getting receipt: {e}")

        except Exception as e:
            print(f"❌ Error processing block {block_num}: {e}")
            continue

    print("\n🔍 Debug complete!")


if __name__ == "__main__":
    debug_affiliate_fee_detection()
