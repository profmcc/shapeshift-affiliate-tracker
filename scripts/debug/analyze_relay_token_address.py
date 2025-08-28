#!/usr/bin/env python3
"""
Debug script to analyze Relay transactions and check token address detection
"""

import sys
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


def analyze_transaction(tx_hash: str, chain: str = "arbitrum"):
    """Analyze a specific transaction to see token addresses"""

    # Get RPC URL
    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if chain == "arbitrum":
        rpc_url = f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}"
    elif chain == "base":
        rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"
    else:
        print(f"Unsupported chain: {chain}")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"Transaction: {tx_hash}")
        print(f"Chain: {chain}")
        print(f"Block: {receipt['blockNumber']}")
        print(f"Logs: {len(receipt['logs'])}")
        print()

        # Check for Global Solver involvement
        global_solver = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
        global_solver_involved = False

        # Look for ERC-20 Transfer events
        erc20_transfers = []

        for i, log in enumerate(receipt["logs"]):
            if not log["topics"]:
                continue

            topic0 = log["topics"][0].hex()
            print(f"Log {i}: topic0={topic0}, address={log['address']}")

            # ERC-20 Transfer event
            if (
                topic0
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                erc20_transfers.append(log["address"])
                print(f"  -> ERC-20 Transfer from {log['address']}")

            # SolverCallExecuted event
            elif (
                topic0
                == "93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324"
            ):
                if len(log["data"]) >= 96:
                    to_address = "0x" + log["data"][:32][-20:].hex()
                    amount = int.from_bytes(log["data"][64:96], "big")
                    print(f"  -> SolverCallExecuted to {to_address}, amount: {amount}")

                    if to_address.lower() == global_solver.lower():
                        global_solver_involved = True
                        print(f"  -> GLOBAL SOLVER INVOLVED!")

            # SolverNativeTransfer event
            elif (
                topic0
                == "d35467972d1fda5b63c735f59d3974fa51785a41a92aa3ed1b70832836f8dba6"
            ):
                if len(log["data"]) >= 64:
                    to_address = "0x" + log["data"][:32][-20:].hex()
                    amount = int.from_bytes(log["data"][32:64], "big")
                    print(
                        f"  -> SolverNativeTransfer to {to_address}, amount: {amount}"
                    )

                    if to_address.lower() == global_solver.lower():
                        global_solver_involved = True
                        print(f"  -> GLOBAL SOLVER INVOLVED!")

        print()
        print(f"Global Solver involved: {global_solver_involved}")
        print(f"ERC-20 tokens found: {erc20_transfers}")

        if global_solver_involved:
            if erc20_transfers:
                print(f"Token address should be: {erc20_transfers[0]}")
            else:
                print(
                    "Token address should be: 0x0000000000000000000000000000000000000000 (native token)"
                )

    except Exception as e:
        print(f"Error analyzing transaction: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_relay_token_address.py <tx_hash> [chain]")
        sys.exit(1)

    tx_hash = sys.argv[1]
    chain = sys.argv[2] if len(sys.argv) > 2 else "arbitrum"

    analyze_transaction(tx_hash, chain)
