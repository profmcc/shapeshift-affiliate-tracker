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


def analyze_relay_partner_data(tx_hash: str, chain_name: str = "base"):
    """Analyze a Relay transaction for partner/affiliate identifiers"""
    load_dotenv()

    # Connect to RPC
    rpc_url = (
        f"https://{chain_name}-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
    )
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    print(f"Analyzing transaction: {tx_hash}")
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
    print(f"Input data length: {len(tx['input'])} bytes")
    print()

    # Analyze the transaction input data
    if tx["input"] and tx["input"] != "0x":
        input_data = bytes.fromhex(tx["input"].hex()[2:])
        print("Transaction input analysis:")
        print(f"  Raw input: {tx['input'].hex()[:100]}...")

        # Look for function selectors
        if len(input_data) >= 4:
            function_selector = input_data[:4].hex()
            print(f"  Function selector: 0x{function_selector}")

            # Common Relay function selectors
            selectors = {
                "0x2213bc0b": "exec",
                "0x3b2253c8": "cleanupErc20s",
                "0x2e17de78": "execute",
                "0x1cff79cd": "multicall",
                "0x5ae401dc": "multicall",
            }

            if function_selector in selectors:
                print(f"  Function: {selectors[function_selector]}")

                # Try to decode the function parameters
                if selectors[function_selector] == "exec":
                    decode_exec_params(input_data)
                elif selectors[function_selector] == "multicall":
                    decode_multicall_params(input_data)

    # Analyze logs for any partner/affiliate information
    print("\nLog analysis:")
    for i, log in enumerate(receipt["logs"]):
        if not log["topics"]:
            continue

        topic0 = log["topics"][0].hex()
        print(f"  Log {i}: topic0 = {topic0}")

        # Look for any events that might contain partner info
        if topic0 == "0x2213bc0b":  # SolverCallExecuted
            print(f"    SolverCallExecuted event")
            if len(log["data"]) > 2:
                data = bytes.fromhex(log["data"][2:])
                analyze_solver_call_data(data)

        # Look for Transfer events that might be affiliate payments
        elif (
            topic0
            == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        ):
            print(f"    Transfer event")
            if len(log["topics"]) >= 3:
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()
                print(f"      From: {from_addr}")
                print(f"      To: {to_addr}")

                # Check if this is a transfer to a known affiliate address
                affiliate_addresses = [
                    "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
                    "0x35339070f178dC4119732982C23F5a8d88D3f8a3",
                ]

                for affiliate_addr in affiliate_addresses:
                    if to_addr.lower() == affiliate_addr.lower():
                        print(
                            f"      *** POTENTIAL AFFILIATE PAYMENT TO {affiliate_addr} ***"
                        )
                        if len(log["data"]) > 2:
                            amount = int(log["data"], 16)
                            print(f"      Amount: {amount}")

                # Also check if this is a transfer from the Relay contract
                if from_addr.lower() == "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222":
                    print(f"      *** TRANSFER FROM RELAY CONTRACT ***")
                    if len(log["data"]) > 2:
                        amount = int(log["data"], 16)
                        print(f"      Amount: {amount}")

        # Look for other events that might be relevant
        elif (
            topic0
            == "0x93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324"
        ):
            print(f"    Unknown event (might be partner/affiliate related)")
            if len(log["data"]) > 2:
                data = bytes.fromhex(log["data"][2:])
                print(f"      Data length: {len(data)} bytes")
                print(f"      Data: {data.hex()[:100]}...")

        elif (
            topic0
            == "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
        ):
            print(f"    Unknown event (might be swap/execution related)")
            if len(log["data"]) > 2:
                data = bytes.fromhex(log["data"][2:])
                print(f"      Data length: {len(data)} bytes")
                print(f"      Data: {data.hex()[:100]}...")


def decode_exec_params(data):
    """Decode exec function parameters"""
    if len(data) < 68:
        return

    target = "0x" + data[4:24].hex()
    value = int.from_bytes(data[24:56], "big")
    data_offset = int.from_bytes(data[56:68], "big")

    print(f"    Target: {target}")
    print(f"    Value: {value}")
    print(f"    Data offset: {data_offset}")

    # Try to decode the nested call data
    if data_offset > 0 and len(data) > data_offset:
        nested_data = data[data_offset:]
        if len(nested_data) >= 4:
            nested_selector = nested_data[:4].hex()
            print(f"    Nested function: 0x{nested_selector}")

            # Look for partner/affiliate parameters in the nested call
            if len(nested_data) >= 68:
                # Common patterns for partner/affiliate data
                for i in range(4, min(len(nested_data) - 31, 100), 32):
                    param = nested_data[i : i + 32]
                    # Check if this looks like an address (not all zeros)
                    if param[:12] != b"\x00" * 12:
                        addr = "0x" + param[-20:].hex()
                        print(f"    Parameter {i//32}: {addr}")


def decode_multicall_params(data):
    """Decode multicall function parameters"""
    if len(data) < 36:
        return

    # Multicall typically has an array of calls
    offset = int.from_bytes(data[4:36], "big")
    print(f"    Calls offset: {offset}")

    if offset > 0 and len(data) > offset:
        calls_data = data[offset:]
        if len(calls_data) >= 32:
            calls_count = int.from_bytes(calls_data[:32], "big")
            print(f"    Number of calls: {calls_count}")

            # Try to decode each call
            for i in range(min(calls_count, 5)):  # Limit to first 5 calls
                call_offset = 32 + i * 32
                if len(calls_data) > call_offset + 32:
                    call_data_offset = int.from_bytes(
                        calls_data[call_offset : call_offset + 32], "big"
                    )
                    print(f"    Call {i} data offset: {call_data_offset}")


def analyze_solver_call_data(data):
    """Analyze SolverCallExecuted data for partner information"""
    if len(data) < 4:
        return

    selector = data[:4].hex()
    print(f"      SolverCallExecuted selector: 0x{selector}")

    # Look for any string data that might contain partner/affiliate info
    # Partner identifiers are often passed as strings or encoded addresses
    for i in range(4, min(len(data) - 31, 200), 32):
        chunk = data[i : i + 32]
        # Try to decode as string
        try:
            # Remove trailing zeros
            while chunk and chunk[-1] == 0:
                chunk = chunk[:-1]
            if chunk:
                string_data = chunk.decode("utf-8", errors="ignore")
                if string_data and string_data.isprintable() and len(string_data) > 2:
                    print(f"      String data at {i}: '{string_data}'")
        except:
            pass

        # Also check if this looks like an address
        if chunk[:12] != b"\x00" * 12:
            addr = "0x" + chunk[-20:].hex()
            print(f"      Address at {i}: {addr}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_relay_partner_data.py <tx_hash>")
        sys.exit(1)

    tx_hash = sys.argv[1]
    analyze_relay_partner_data(tx_hash)
