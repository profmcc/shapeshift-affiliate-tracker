#!/usr/bin/env python3
"""
Analyze transaction input data to understand how affiliate fees might be encoded
in transaction parameters rather than as direct transfers.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def analyze_transaction_input_data():
    """Analyze transaction input data for affiliate fee encoding."""

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

    # Known ShapeShift addresses
    shapeshift_addresses = [
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower(),
    ]

    print(f"\n🔍 Analyzing transaction input data for affiliate fee encoding...")

    # Scan recent blocks for router transactions
    start_block = latest_block - 200  # Look at last 200 blocks
    end_block = latest_block

    analyzed_transactions = []

    for block_num in range(start_block, end_block + 1, 5):  # Check every 5th block
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                # Check if this transaction involves a router
                router_involved = False
                for router_addr in router_addresses:
                    if router_addr.lower() in tx["to"].lower() if tx["to"] else False:
                        router_involved = True
                        break

                if router_involved and tx["input"] and tx["input"] != "0x":
                    try:
                        input_data = tx["input"]
                        input_hex = input_data.hex()

                        # Look for ShapeShift addresses in input data
                        shapeshift_found = False
                        for shapeshift_addr in shapeshift_addresses:
                            if shapeshift_addr.lower() in input_hex:
                                shapeshift_found = True
                                break

                        if shapeshift_found:
                            print(
                                f"\n🎯 Found transaction with ShapeShift address in input data: {tx_hash}"
                            )
                            print(f"   Block: {block_num}")
                            print(f"   Input data: {input_hex}")

                            # Try to decode the input data
                            if (
                                len(input_data) >= 10
                            ):  # At least 4 bytes for function selector
                                function_selector = input_data[:10]
                                print(f"   Function selector: {function_selector}")

                                # Remove function selector and analyze remaining data
                                remaining_data = input_data[10:]
                                print(f"   Remaining data: {remaining_data.hex()}")

                                # Try to parse as structured parameters
                                param_size = 32
                                num_params = len(remaining_data) // param_size

                                print(f"   Estimated parameters: {num_params}")

                                for i in range(num_params):
                                    start = i * param_size
                                    end = start + param_size
                                    param_data = remaining_data[start:end]

                                    print(f"   Parameter {i}: {param_data.hex()}")

                                    # Try to interpret as different types
                                    try:
                                        # As uint256
                                        uint_value = int.from_bytes(param_data, "big")
                                        print(f"      As uint256: {uint_value}")

                                        # As address (if it starts with zeros)
                                        if param_data.startswith(b"\x00" * 12):
                                            addr = "0x" + param_data[-20:].hex()
                                            print(f"      As address: {addr}")

                                            # Check if this is a ShapeShift address
                                            for shapeshift_addr in shapeshift_addresses:
                                                if (
                                                    shapeshift_addr.lower()
                                                    in addr.lower()
                                                ):
                                                    print(
                                                        f"      🎯 SHAPESHIFT ADDRESS FOUND!"
                                                    )
                                                    print(
                                                        f"         ShapeShift address: {shapeshift_addr}"
                                                    )
                                                    print(
                                                        f"         Found address: {addr}"
                                                    )

                                        # As bytes32 (if it's not an address)
                                        elif uint_value > 0:
                                            print(
                                                f"      As bytes32: {param_data.hex()}"
                                            )

                                    except Exception as e:
                                        print(
                                            f"      ❌ Error parsing parameter {i}: {e}"
                                        )

                        # Also look for potential affiliate indicators in input data
                        potential_indicators = [
                            "affiliate",
                            "fee",
                            "commission",
                            "reward",
                            "referral",
                            "treasury",
                            "dao",
                        ]

                        for indicator in potential_indicators:
                            if indicator in input_hex.lower():
                                print(
                                    f"\n🎯 Found potential indicator '{indicator}' in transaction: {tx_hash}"
                                )
                                print(f"   Block: {block_num}")
                                print(f"   Input data: {input_hex}")

                        analyzed_transactions.append(
                            {
                                "tx_hash": tx_hash,
                                "block": block_num,
                                "has_shapeshift": shapeshift_found,
                                "input_length": len(input_data),
                            }
                        )

                    except Exception as e:
                        print(f"❌ Error analyzing transaction {tx_hash}: {e}")
                        continue

        except Exception as e:
            print(f"❌ Error processing block {block_num}: {e}")
            continue

    print(f"\n📊 Analysis complete!")
    print(f"   - Analyzed {len(analyzed_transactions)} router transactions")
    print(
        f"   - Transactions with ShapeShift in input: {sum(1 for t in analyzed_transactions if t['has_shapeshift'])}"
    )
    print(
        f"   - Average input data length: {sum(t['input_length'] for t in analyzed_transactions) / len(analyzed_transactions) if analyzed_transactions else 0:.1f} bytes"
    )


if __name__ == "__main__":
    analyze_transaction_input_data()
