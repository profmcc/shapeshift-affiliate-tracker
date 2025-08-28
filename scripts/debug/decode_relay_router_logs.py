import json
from web3 import Web3
from web3._utils.events import get_event_data, event_abi_to_log_topic
import sqlite3
import os
from typing import List

# Load ABI
with open("shared/relay_erc20router_abi.json") as f:
    ABI = json.load(f)

# Add chain RPCs
CHAIN_RPCS = {
    "base": "https://base-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms",
    "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms",
    "ethereum": "https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms",
    "polygon": "https://polygon-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms",
    "optimism": "https://opt-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms",
}

# Add known ShapeShift affiliate addresses (lowercase for comparison)
SHAPESHIFT_ADDRESSES = {
    "0x35339070f178dc4119732982c23f5a8d88d3f8a3",  # payout address
    "0xf525ff21c370beb8d9f5c12dc0da2b583f4b949f",  # affiliate/credit address
}

# Database setup
DB_PATH = "relay_affiliate_events.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(
    """CREATE TABLE IF NOT EXISTS affiliate_events (
    tx_hash TEXT,
    block_number INTEGER,
    event_type TEXT,
    matched_address TEXT,
    amount TEXT,
    token TEXT,
    timestamp INTEGER
)"""
)
conn.commit()


def process_tx(tx_hash: str, chain: str):
    chain_lc = chain.lower()
    rpc_url = CHAIN_RPCS.get(chain_lc)
    if not rpc_url:
        print(f"[WARN] Unknown chain '{chain}' for tx {tx_hash}, skipping.")
        return []
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        block = w3.eth.get_block(receipt["blockNumber"])
        timestamp = block["timestamp"]
        results = []
        event_sigs = {}
        for item in ABI:
            if item.get("type") == "event":
                topic = event_abi_to_log_topic(item)
                event_sigs[topic.hex().lower()] = item
        for i, log in enumerate(receipt["logs"]):
            topic0 = log["topics"][0].hex().lower()
            abi = event_sigs.get(topic0)
            if abi and abi["name"] == "SolverCallExecuted":
                decoded = get_event_data(w3.codec, abi, log)
                data_bytes = decoded["args"]["data"]
                selector = data_bytes[:4].hex() if len(data_bytes) >= 4 else None
                if selector == "2213bc0b" and len(data_bytes) >= 4 + 32 * 5:
                    try:
                        args_head = data_bytes[4 : 4 + 32 * 5]
                        addr1 = "0x" + args_head[12:32].hex()
                        addr2 = "0x" + args_head[44:64].hex()
                        uint_val = int.from_bytes(args_head[64:96], "big")
                        addr3 = "0x" + args_head[108:128].hex()
                        bytes_offset = int.from_bytes(args_head[128:160], "big")
                        bytes_start = 4 + bytes_offset
                        bytes_len = int.from_bytes(
                            data_bytes[bytes_start : bytes_start + 32], "big"
                        )
                        for a in [addr1, addr2, addr3]:
                            if a.lower() in SHAPESHIFT_ADDRESSES:
                                results.append(
                                    (
                                        tx_hash,
                                        receipt["blockNumber"],
                                        "exec",
                                        a,
                                        str(uint_val),
                                        addr3,
                                        timestamp,
                                    )
                                )
                    except Exception as e:
                        pass
                elif selector == "3b2253c8":
                    try:
                        if len(data_bytes) < 4 + 32 * 3:
                            raise Exception("data too short for cleanupErc20s")
                        offsets = [
                            int.from_bytes(
                                data_bytes[4 + i * 32 : 4 + (i + 1) * 32], "big"
                            )
                            for i in range(3)
                        ]
                        arrays = []
                        for off in offsets:
                            arr_start = 4 + off
                            arr_len = int.from_bytes(
                                data_bytes[arr_start : arr_start + 32], "big"
                            )
                            arr = []
                            for j in range(arr_len):
                                val = data_bytes[
                                    arr_start
                                    + 32
                                    + j * 32 : arr_start
                                    + 32
                                    + (j + 1) * 32
                                ]
                                arr.append(val)
                            arrays.append(arr)
                        addr_arr1 = ["0x" + x[-20:].hex() for x in arrays[0]]
                        addr_arr2 = ["0x" + x[-20:].hex() for x in arrays[1]]
                        uint_arr = [int.from_bytes(x, "big") for x in arrays[2]]
                        for i, recipient in enumerate(addr_arr2):
                            if recipient.lower() in SHAPESHIFT_ADDRESSES:
                                results.append(
                                    (
                                        tx_hash,
                                        receipt["blockNumber"],
                                        "cleanupErc20s",
                                        recipient,
                                        str(uint_arr[i]),
                                        addr_arr1[i],
                                        timestamp,
                                    )
                                )
                    except Exception as e:
                        pass
        return results
    except Exception as e:
        print(f"[ERROR] {tx_hash} ({chain}): {e}")
        return []


def process_batch(tx_hashes: List[tuple]):
    all_results = []
    for chain, tx_hash in tx_hashes:
        print(f"Processing {tx_hash} on {chain}...")
        results = process_tx(tx_hash, chain)
        if results:
            c.executemany(
                "INSERT INTO affiliate_events VALUES (?, ?, ?, ?, ?, ?, ?)", results
            )
            conn.commit()
            all_results.extend(results)
    print(f"\nSummary: {len(all_results)} affiliate events found.")
    for r in all_results:
        print(r)


if __name__ == "__main__":
    # Expect tx_hashes.txt to have lines: chain,tx_hash
    tx_hashes = []
    if os.path.exists("tx_hashes.txt"):
        with open("tx_hashes.txt") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    tx_hashes.append((parts[0].strip(), parts[1].strip()))
    else:
        # Fallback: single example
        tx_hashes = [
            (
                "base",
                "0xb58fae7234a4d88aef03c09e31eca3f739f50b7a37090ab53d70ec32c53dba55",
            )
        ]
    process_batch(tx_hashes)
