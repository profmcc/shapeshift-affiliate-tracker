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


def analyze_relay_tx_detailed(tx_hash: str, chain_name: str = "base"):
    """Detailed analysis of a Relay transaction for affiliate fee events"""
    load_dotenv()

    # Connect to RPC
    if chain_name == "arbitrum":
        rpc_url = f"https://arb-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
    else:
        rpc_url = f"https://{chain_name}-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    print(f"Detailed analysis of: {tx_hash}")
    print(f"Chain: {chain_name}")
    print()

    # Get transaction details
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    tx = w3.eth.get_transaction(tx_hash)
    block = w3.eth.get_block(receipt["blockNumber"])

    print(f"Block: {receipt['blockNumber']}")
    print(f"Timestamp: {block['timestamp']}")
    print(f"From: {tx['from']}")
    print(f"To: {tx['to']}")
    print(f"Value: {tx['value']}")
    print(f"Number of logs: {len(receipt['logs'])}")
    print()

    # Load the Relay ABI
    with open("shared/abis/relay/ERC20Router.json", "r") as f:
        abi = json.load(f)

    # Build event signature map
    event_signatures = {}
    for item in abi:
        if item.get("type") == "event":
            event_name = item["name"]
            event_abi = {
                "type": "event",
                "name": event_name,
                "inputs": item.get("inputs", []),
            }
            # Generate topic hash
            from web3._utils.events import event_abi_to_log_topic

            topic = event_abi_to_log_topic(event_abi)
            event_signatures[topic.hex().lower()] = event_abi

    # Target affiliate address
    affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower()

    print(f"Looking for affiliate address: {affiliate_address}")
    print(f"Available event signatures: {list(event_signatures.keys())}")
    print()

    # Analyze each log
    for i, log in enumerate(receipt["logs"]):
        if not log["topics"]:
            continue

        topic0 = log["topics"][0].hex().lower()
        print(f"Log {i}: topic0 = {topic0}")

        event_abi = event_signatures.get(topic0)
        if event_abi:
            print(f"  Event: {event_abi['name']}")

            # Check for SolverCallExecuted
            if event_abi["name"] == "SolverCallExecuted":
                # Manual decoding for anonymous events
                if len(log["data"]) >= 96:  # 3 * 32 bytes for to, data offset, amount
                    to_address = "0x" + log["data"][:32][-20:].hex()
                    data_offset = int.from_bytes(log["data"][32:64], "big")
                    amount = int.from_bytes(log["data"][64:96], "big")

                    # Extract data from the offset
                    if data_offset > 0 and len(log["data"]) > data_offset + 32:
                        data_length = int.from_bytes(
                            log["data"][data_offset : data_offset + 32], "big"
                        )
                        if len(log["data"]) >= data_offset + 32 + data_length:
                            data = log["data"][
                                data_offset + 32 : data_offset + 32 + data_length
                            ]
                        else:
                            data = b""
                    else:
                        data = b""
                else:
                    print(f"  Insufficient data for manual decoding")
                    continue

                print(f"  To address: {to_address}")
                print(f"  Amount: {amount}")
                print(f"  Data length: {len(data)} bytes")

                if to_address == affiliate_address:
                    print(f"  *** FOUND AFFILIATE FEE EVENT! ***")
                    print(f"  Data: {data.hex()}")

                    # Try to decode the transfer data
                    if len(data) >= 4:
                        transfer_selector = (
                            b"\xa9\x05\x9c\xbb"  # transfer(address,uint256)
                        )
                        if data.startswith(transfer_selector) and len(data) >= 68:
                            recipient = "0x" + data[4:24].hex()
                            transfer_amount = int.from_bytes(data[24:56], "big")
                            print(f"  Transfer to: {recipient}")
                            print(f"  Transfer amount: {transfer_amount}")

            # Check for SolverNativeTransfer
            elif event_abi["name"] == "SolverNativeTransfer":
                # Manual decoding for anonymous events
                if len(log["data"]) >= 64:  # 2 * 32 bytes for to, amount
                    to_address = "0x" + log["data"][:32][-20:].hex()
                    amount = int.from_bytes(log["data"][32:64], "big")
                else:
                    print(f"  Insufficient data for manual decoding")
                    continue

                print(f"  To address: {to_address}")
                print(f"  Amount: {amount}")

                if to_address == affiliate_address:
                    print(f"  *** FOUND AFFILIATE FEE EVENT! ***")

        else:
            print(f"  Unknown event")

        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_relay_tx_detailed.py <tx_hash> [chain_name]")
        sys.exit(1)

    tx_hash = sys.argv[1]
    chain_name = sys.argv[2] if len(sys.argv) > 2 else "base"
    analyze_relay_tx_detailed(tx_hash, chain_name)
