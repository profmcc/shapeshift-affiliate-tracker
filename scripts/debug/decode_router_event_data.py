#!/usr/bin/env python3
"""
Decode router event data from a specific transaction to understand how affiliate fees might be recorded.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def decode_router_event_data():
    """Decode router event data from a specific transaction."""

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

    # The specific transaction we analyzed
    tx_hash = "0x6d688cc41d208c4b7dd1bce9a174e65201fc6beecdb43ad0edcaba6d6ed69c96"

    print(f"\n🔍 Decoding router event data from transaction: {tx_hash}")

    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        # Find the router events (logs from the router address)
        router_address = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"
        router_events = []

        for i, log in enumerate(receipt["logs"]):
            if log["address"].lower() == router_address.lower():
                router_events.append((i, log))

        print(f"\n📊 Found {len(router_events)} events from router address")

        for event_idx, log in router_events:
            print(f"\n   Router Event {event_idx}:")
            print(f"      Topics: {[topic.hex() for topic in log['topics']]}")
            print(f"      Data: {log['data'].hex()}")

            # Try to decode the data based on the event signature
            if (
                log["topics"][0].hex()
                == "93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324"
            ):
                print(f"      📝 Router Swap Event")

                # This appears to be a swap event with multiple parameters
                data = log["data"]
                print(f"      Raw data length: {len(data)} bytes")

                # Try to parse the data as structured parameters
                # Each parameter is typically 32 bytes (256 bits)
                param_size = 32
                num_params = len(data) // param_size

                print(f"      Estimated parameters: {num_params}")

                for i in range(num_params):
                    start = i * param_size
                    end = start + param_size
                    param_data = data[start:end]

                    print(f"      Parameter {i}: {param_data.hex()}")

                    # Try to interpret as different types
                    try:
                        # As uint256
                        uint_value = int.from_bytes(param_data, "big")
                        print(f"         As uint256: {uint_value}")

                        # As address (if it starts with zeros)
                        if param_data.startswith(b"\x00" * 12):
                            addr = "0x" + param_data[-20:].hex()
                            print(f"         As address: {addr}")

                            # Check if this could be a ShapeShift address
                            shapeshift_addresses = [
                                "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
                                "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower(),
                            ]

                            for shapeshift_addr in shapeshift_addresses:
                                if shapeshift_addr.lower() in addr.lower():
                                    print(
                                        f"         🎯 POTENTIAL SHAPESHIFT ADDRESS FOUND!"
                                    )
                                    print(
                                        f"            ShapeShift address: {shapeshift_addr}"
                                    )
                                    print(f"            Found address: {addr}")

                        # As bytes32 (if it's not an address)
                        elif uint_value > 0:
                            print(f"         As bytes32: {param_data.hex()}")

                    except Exception as e:
                        print(f"         ❌ Error parsing parameter {i}: {e}")

                # Look for patterns in the data that might indicate affiliate information
                print(f"\n      🔍 Looking for affiliate patterns...")

                # Check if any of the parameters contain the ShapeShift address
                shapeshift_pattern = "9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower()
                data_hex = data.hex()

                if shapeshift_pattern in data_hex:
                    print(f"      🎯 Found ShapeShift address pattern in data!")
                    pattern_pos = data_hex.find(shapeshift_pattern)
                    print(f"      Pattern found at position: {pattern_pos}")

                    # Extract the context around the pattern
                    start_pos = max(0, pattern_pos - 64)
                    end_pos = min(len(data_hex), pattern_pos + 64)
                    context = data_hex[start_pos:end_pos]
                    print(f"      Context: {context}")

                # Check for other potential affiliate indicators
                potential_indicators = [
                    "affiliate",
                    "fee",
                    "commission",
                    "reward",
                    "referral",
                ]

                for indicator in potential_indicators:
                    if indicator in data_hex.lower():
                        print(f"      🎯 Found potential indicator: {indicator}")

        # Also analyze the transaction input data for affiliate information
        print(f"\n🔍 Analyzing transaction input data...")

        tx = w3.eth.get_transaction(tx_hash)
        input_data = tx["input"]

        if input_data and input_data != "0x":
            print(f"   Input data length: {len(input_data)} bytes")
            print(f"   Input data: {input_data.hex()}")

            # Look for ShapeShift address in input data
            input_hex = input_data.hex()
            if shapeshift_pattern in input_hex:
                print(f"   🎯 Found ShapeShift address in input data!")
                pattern_pos = input_hex.find(shapeshift_pattern)
                print(f"   Pattern found at position: {pattern_pos}")

                # Extract context
                start_pos = max(0, pattern_pos - 64)
                end_pos = min(len(input_hex), pattern_pos + 64)
                context = input_hex[start_pos:end_pos]
                print(f"   Context: {context}")

    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")


if __name__ == "__main__":
    decode_router_event_data()
