#!/usr/bin/env python3
"""
Scan all logs emitted by the WETH/FOX pool contract on Arbitrum in the last 1,000 blocks.
Prints block, tx hash, topics, and data for each log.
"""
from web3 import Web3
from typing import List, Dict, Any
import sys

ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
POOL_ADDRESS = "0x5f6ce0ca13b87bd738519545d3e018e70e339c24"


def main():
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        print("Failed to connect to Arbitrum RPC")
        sys.exit(1)
    
    current_block = w3.eth.block_number
    start_block = current_block - 1000
    pool = w3.to_checksum_address(POOL_ADDRESS)
    print(f"Connected to Arbitrum. Current block: {current_block}")
    print(f"Scanning all logs emitted by pool {pool} from block {start_block} to {current_block}")
    print()
    try:
        logs = w3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": current_block,
            "address": pool
        })
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return
    print(f"Found {len(logs)} logs emitted by the pool.\n")
    print(f"{'Block':<10} {'TxHash':<66} {'Topics':<80} {'Data'}")
    print("-"*180)
    for log in logs:
        block = log['blockNumber']
        tx_hash = log['transactionHash'].hex()
        topics = ','.join([t.hex() for t in log['topics']])
        data = log['data']
        print(f"{block:<10} {tx_hash:<66} {topics:<80} {data}")

if __name__ == "__main__":
    main() 