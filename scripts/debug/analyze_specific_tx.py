#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from dotenv import load_dotenv
import json

# Add the project root to the path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from listeners.relay_listener import RelayListener


def analyze_transaction(tx_hash: str, chain_name: str = "base"):
    """Analyze a specific transaction for affiliate fees"""
    load_dotenv()

    # Initialize the relay listener
    listener = RelayListener()

    # Get chain config
    chain_config = listener._get_chain_config(chain_name)
    if not chain_config:
        print(f"Chain {chain_name} not found in configuration")
        return

    # Connect to the RPC
    w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
    print(f"Connected to {chain_name} RPC")

    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    block = w3.eth.get_block(receipt["blockNumber"])
    timestamp = block["timestamp"]

    print(f"Transaction: {tx_hash}")
    print(f"Block: {receipt['blockNumber']}")
    print(f"Timestamp: {timestamp}")
    print(f"Number of logs: {len(receipt['logs'])}")
    print(f"Affiliate address we're looking for: {listener.affiliate_address}")
    print()

    # Check each log for SolverCallExecuted events
    for log_index, log in enumerate(receipt["logs"]):
        if not log["topics"]:
            continue

        topic0 = log["topics"][0].hex().lower()
        event_abi = listener.event_signatures.get(topic0)

        if event_abi and event_abi["name"] == "SolverCallExecuted":
            print(f"Found SolverCallExecuted event at log index {log_index}")

            try:
                decoded = (
                    w3.eth.contract(abi=[event_abi])
                    .events.SolverCallExecuted()
                    .process_log(log)
                )
                data_bytes = decoded["args"]["data"]

                print(f"  Data length: {len(data_bytes)} bytes")
                print(f"  Data (hex): {data_bytes.hex()[:100]}...")

                # Decode the data field to find affiliate transfers
                affiliate_data = listener._decode_solver_call_data(data_bytes)

                if affiliate_data:
                    print(f"  Found affiliate data: {affiliate_data}")
                else:
                    print(f"  No affiliate data found")

                # Let's also try to decode the data manually to see what addresses are in there
                print(f"  Attempting manual decode...")
                try:
                    # Try to extract addresses from the data
                    if len(data_bytes) > 0:
                        # Look for function selectors first (first 4 bytes)
                        if len(data_bytes) >= 4:
                            function_selector = data_bytes[:4].hex()
                            print(f"  Function selector: 0x{function_selector}")

                        # Try to parse the data more carefully
                        # Look for addresses that are properly aligned (after function selector)
                        addresses = []
                        for i in range(
                            4, len(data_bytes) - 19, 32
                        ):  # 32-byte alignment for ABI encoding
                            addr_bytes = data_bytes[i : i + 20]
                            if len(addr_bytes) == 20:
                                addr = "0x" + addr_bytes.hex()
                                if addr != "0x0000000000000000000000000000000000000000":
                                    addresses.append(addr)

                        # Remove duplicates and show unique addresses
                        unique_addresses = list(set(addresses))
                        print(
                            f"  Found {len(unique_addresses)} unique addresses in data (32-byte aligned):"
                        )
                        for addr in unique_addresses[:10]:  # Show first 10
                            print(f"    {addr}")
                        if len(unique_addresses) > 10:
                            print(f"    ... and {len(unique_addresses) - 10} more")

                        # Check if our affiliate address is in the list
                        affiliate_addr_lower = listener.affiliate_address.lower()
                        matching_addresses = [
                            addr
                            for addr in unique_addresses
                            if addr.lower() == affiliate_addr_lower
                        ]
                        if matching_addresses:
                            print(f"  FOUND AFFILIATE ADDRESS: {matching_addresses}")
                        else:
                            print(f"  Affiliate address not found in decoded addresses")

                        # Also check for ShapeShift-related addresses
                        shapeshift_addresses = [
                            addr
                            for addr in unique_addresses
                            if "shapeshift" in addr.lower() or "ss" in addr.lower()
                        ]
                        if shapeshift_addresses:
                            print(
                                f"  FOUND SHAPESHIFT-RELATED ADDRESSES: {shapeshift_addresses}"
                            )
                        else:
                            print(f"  No ShapeShift-related addresses found")

                except Exception as e:
                    print(f"  Error in manual decode: {e}")
            except Exception as e:
                print(f"  Error processing log: {e}")

            print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_specific_tx.py <tx_hash>")
        sys.exit(1)

    tx_hash = sys.argv[1]
    analyze_transaction(tx_hash)
