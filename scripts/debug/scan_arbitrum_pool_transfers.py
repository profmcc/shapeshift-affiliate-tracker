#!/usr/bin/env python3
"""
Scan for all ERC20 Transfer events involving the WETH/FOX pool on Arbitrum.
Shows deposits (to pool) and withdrawals (from pool) for both tokens.
"""

from web3 import Web3
from typing import List, Dict, Any
from datetime import datetime
import sys

ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
POOL_ADDRESS = "0x5f6ce0ca13b87bd738519545d3e018e70e339c24"
WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
FOX_ADDRESS = "0x7c6d161b367ec0605260628c37b8dd778446256b"

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

TRANSFER_EVENT_SIG = Web3.keccak(text="Transfer(address,address,uint256)").hex()


def get_token_info(w3: Web3, address: str) -> Dict[str, Any]:
    contract = w3.eth.contract(address=address, abi=ERC20_ABI)
    try:
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        return {"symbol": symbol, "decimals": decimals}
    except Exception as e:
        print(f"Error fetching token info for {address}: {e}")
        return {"symbol": "?", "decimals": 18}


def scan_transfers(
    w3: Web3, token_address: str, pool_address: str, start_block: int, end_block: int
) -> List[Dict[str, Any]]:
    """Scan for all Transfer events involving the pool address for a given token."""
    pool_address_checksum = w3.to_checksum_address(pool_address)
    token_address_checksum = w3.to_checksum_address(token_address)
    logs = []
    try:
        # Pool as sender (withdrawal)
        logs += w3.eth.get_logs(
            {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": token_address_checksum,
                "topics": [
                    TRANSFER_EVENT_SIG,
                    w3.to_hex(0).replace("0x", "0x").zfill(66),
                    w3.to_hex(pool_address_checksum).replace("0x", "0x").zfill(66),
                ],
            }
        )
    except Exception:
        pass
    try:
        # Pool as recipient (deposit)
        logs += w3.eth.get_logs(
            {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": token_address_checksum,
                "topics": [
                    TRANSFER_EVENT_SIG,
                    None,
                    w3.to_hex(pool_address_checksum).replace("0x", "0x").zfill(66),
                ],
            }
        )
    except Exception:
        pass
    try:
        # Pool as sender (withdrawal)
        logs += w3.eth.get_logs(
            {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": token_address_checksum,
                "topics": [
                    TRANSFER_EVENT_SIG,
                    w3.to_hex(pool_address_checksum).replace("0x", "0x").zfill(66),
                ],
            }
        )
    except Exception:
        pass
    # Deduplicate logs
    seen = set()
    unique_logs = []
    for log in logs:
        key = (log["transactionHash"].hex(), log["logIndex"])
        if key not in seen:
            seen.add(key)
            unique_logs.append(log)
    return unique_logs


def decode_transfer_log(log: Dict[str, Any]) -> Dict[str, Any]:
    from_addr = "0x" + log["topics"][1].hex()[-40:]
    to_addr = "0x" + log["topics"][2].hex()[-40:]
    value = int(log["data"], 16)
    return {
        "blockNumber": log["blockNumber"],
        "txHash": log["transactionHash"].hex(),
        "from": from_addr,
        "to": to_addr,
        "value": value,
    }


def main():
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        print("Failed to connect to Arbitrum RPC")
        sys.exit(1)

    current_block = w3.eth.block_number
    # Scan last 1000 blocks instead of a week
    start_block = current_block - 1000

    pool = w3.to_checksum_address(POOL_ADDRESS)
    weth = w3.to_checksum_address(WETH_ADDRESS)
    fox = w3.to_checksum_address(FOX_ADDRESS)

    print(f"Connected to Arbitrum. Current block: {current_block}")
    print(f"Scanning blocks {start_block} to {current_block} (last 1000 blocks)")
    print(f"Pool address: {pool}")
    print()

    # Get token info
    weth_info = get_token_info(w3, weth)
    fox_info = get_token_info(w3, fox)

    # Scan for transfers
    print(f"Scanning WETH transfers involving pool...")
    weth_logs = scan_transfers(w3, weth, pool, start_block, current_block)
    print(f"Found {len(weth_logs)} WETH transfer logs.")

    print(f"Scanning FOX transfers involving pool...")
    fox_logs = scan_transfers(w3, fox, pool, start_block, current_block)
    print(f"Found {len(fox_logs)} FOX transfer logs.\n")

    # Decode and print
    print(
        f"{'Block':<10} {'Token':<6} {'From':<42} {'To':<42} {'Amount':<24} {'TxHash'}"
    )
    print("-" * 140)

    for log in weth_logs:
        d = decode_transfer_log(log)
        amount = d["value"] / (10 ** weth_info["decimals"])
        print(
            f"{d['blockNumber']:<10} {weth_info['symbol']:<6} {d['from']:<42} {d['to']:<42} {amount:<24.8f} {d['txHash']}"
        )

    for log in fox_logs:
        d = decode_transfer_log(log)
        amount = d["value"] / (10 ** fox_info["decimals"])
        print(
            f"{d['blockNumber']:<10} {fox_info['symbol']:<6} {d['from']:<42} {d['to']:<42} {amount:<24.8f} {d['txHash']}"
        )

    # Summary
    print(f"\nSummary:")
    print(f"WETH transfers: {len(weth_logs)}")
    print(f"FOX transfers: {len(fox_logs)}")
    print(f"Total transfers: {len(weth_logs) + len(fox_logs)}")


if __name__ == "__main__":
    main()
