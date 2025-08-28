#!/usr/bin/env python3
"""
Investigate unknown event signatures from the Relay router.
These might contain affiliate fee information in a different format.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def investigate_router_events():
    """Investigate unknown event signatures from the Relay router."""

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

    # Router address
    router_address = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    # Unknown event signatures we found
    unknown_signatures = [
        "93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324",  # From router
        "add7095becdaa725f0f33243630938c861b0bba83dfd217d4055701aa768ec2e",  # From token
        "e1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c",  # From WETH
    ]

    print(f"\n🔍 Investigating unknown event signatures from router: {router_address}")

    # Get latest block
    latest_block = w3.eth.block_number
    print(f"📊 Latest block: {latest_block}")

    # Scan recent blocks for these specific event signatures
    start_block = latest_block - 1000
    end_block = latest_block

    for block_num in range(start_block, end_block + 1, 50):  # Check every 50th block
        try:
            # Get logs for the router address with these specific event signatures
            for signature in unknown_signatures:
                logs = w3.eth.get_logs(
                    {
                        "fromBlock": block_num,
                        "toBlock": block_num,
                        "address": router_address,
                        "topics": [signature],
                    }
                )

                for log in logs:
                    tx_hash = log["transactionHash"].hex()
                    print(
                        f"\n🎯 Found event with signature {signature} in transaction: {tx_hash}"
                    )
                    print(f"   Block: {log['blockNumber']}")
                    print(f"   Topics: {[topic.hex() for topic in log['topics']]}")
                    print(f"   Data: {log['data'].hex()}")

                    # Try to decode the data based on the signature
                    if (
                        signature
                        == "93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324"
                    ):
                        print(f"   📝 This appears to be a swap event from the router")
                        # Try to parse the data as addresses and amounts
                        data = log["data"]
                        if len(data) >= 32:
                            try:
                                # First 32 bytes might be an address or amount
                                first_bytes = data[:32]
                                print(f"   First 32 bytes: {first_bytes.hex()}")

                                # Look for any addresses in the data
                                for i in range(0, len(data) - 31, 32):
                                    chunk = data[i : i + 32]
                                    if chunk.startswith(b"\x00" * 12):  # Padded address
                                        addr = "0x" + chunk[-20:].hex()
                                        print(
                                            f"   Potential address at offset {i}: {addr}"
                                        )

                            except Exception as e:
                                print(f"   ❌ Error parsing data: {e}")

                    elif (
                        signature
                        == "add7095becdaa725f0f33243630938c861b0bba83dfd217d4055701aa768ec2e"
                    ):
                        print(f"   📝 This appears to be an event from a token contract")

                    elif (
                        signature
                        == "e1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
                    ):
                        print(
                            f"   📝 This appears to be a WETH deposit/withdrawal event"
                        )

                    # Check if this transaction involves any known addresses
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        print(
                            f"   Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}"
                        )

                        # Look for any transfers to ShapeShift addresses in this transaction
                        shapeshift_addresses = [
                            "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
                            "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower(),
                        ]

                        for receipt_log in receipt["logs"]:
                            if (
                                receipt_log.get("topics")
                                and len(receipt_log["topics"]) == 3
                                and receipt_log["topics"][0].hex()
                                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                            ):
                                from_addr_raw = receipt_log["topics"][1].hex()
                                to_addr_raw = receipt_log["topics"][2].hex()

                                from_addr = "0x" + from_addr_raw[-40:]
                                to_addr = "0x" + to_addr_raw[-40:]

                                for shapeshift_addr in shapeshift_addresses:
                                    if (
                                        shapeshift_addr.lower() in from_addr.lower()
                                        or shapeshift_addr.lower() in to_addr.lower()
                                    ):
                                        print(
                                            f"   🎯 Found transfer involving ShapeShift address!"
                                        )
                                        print(f"      From: {from_addr}")
                                        print(f"      To: {to_addr}")
                                        break

                    except Exception as e:
                        print(f"   ❌ Error getting receipt: {e}")

        except Exception as e:
            print(f"❌ Error processing block {block_num}: {e}")
            continue

    print("\n🔍 Investigation complete!")


if __name__ == "__main__":
    investigate_router_events()
