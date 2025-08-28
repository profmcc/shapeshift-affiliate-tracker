#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from dotenv import load_dotenv


def check_transfer_events(tx_hash: str, chain_name: str = "base"):
    """Check Transfer events in a transaction"""
    load_dotenv()

    # Connect to RPC
    rpc_url = (
        f"https://{chain_name}-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
    )
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    print(f"Checking Transfer events in: {tx_hash}")
    print(f"Chain: {chain_name}")
    print()

    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    # Look for Transfer events
    transfer_topic = (
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )

    for i, log in enumerate(receipt["logs"]):
        if not log["topics"]:
            continue

        topic0 = log["topics"][0].hex()
        if topic0 == transfer_topic:
            print(f"Transfer event at log {i}:")

            if len(log["topics"]) >= 3:
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()
                print(f"  From: {from_addr}")
                print(f"  To: {to_addr}")

                if len(log["data"]) > 2:
                    amount = int(log["data"], 16)
                    print(f"  Amount: {amount}")

                # Check if this is a transfer to a known affiliate address
                affiliate_addresses = [
                    "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
                    "0x35339070f178dC4119732982C23F5a8d88D3f8a3",
                ]

                for affiliate_addr in affiliate_addresses:
                    if to_addr.lower() == affiliate_addr.lower():
                        print(
                            f"  *** POTENTIAL AFFILIATE PAYMENT TO {affiliate_addr} ***"
                        )

                # Check if this is a transfer from the Relay contract
                if from_addr.lower() == "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222":
                    print(f"  *** TRANSFER FROM RELAY CONTRACT ***")

            print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_transfer_events.py <tx_hash>")
        sys.exit(1)

    tx_hash = sys.argv[1]
    check_transfer_events(tx_hash)
