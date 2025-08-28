import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from web3 import Web3
from eth_abi import decode
import time

# Configuration
PAIR_ADDRESS = "0x5f6ce0ca13b87bd738519545d3e018e70e339c24"
DB_PATH = "arbitrum_weth_fox_events.db"
ABI_PATH = "abis/UniswapV2Pair.json"
INFURA_URL = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"

# Create tables SQL
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS mint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    sender TEXT,
    amount0 TEXT,
    amount1 TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS burn (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    sender TEXT,
    amount0 TEXT,
    amount1 TEXT,
    to_addr TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS swap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    sender TEXT,
    amount0In TEXT,
    amount1In TEXT,
    amount0Out TEXT,
    amount1Out TEXT,
    to_addr TEXT,
    timestamp TEXT
);
"""


def get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    return w3


def load_abi() -> list:
    with open(ABI_PATH, "r") as f:
        return json.load(f)


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(CREATE_TABLES_SQL)
    return conn


def fetch_and_store_events(start_block: int = None, end_block: int = None):
    w3 = get_web3()
    abi = load_abi()
    # Convert to checksum address
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)
    contract = w3.eth.contract(address=checksum_address, abi=abi)
    conn = connect_db()
    cur = conn.cursor()

    if end_block is None:
        end_block = w3.eth.block_number
    if start_block is None:
        start_block = max(0, end_block - 10000)

    # Event signatures for Uniswap V2 Pair events
    event_map = {
        "Mint": (
            "mint",
            "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
        ),
        "Burn": (
            "burn",
            "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496",
        ),
        "Swap": (
            "swap",
            "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
        ),
    }

    for event_name, (table, event_signature) in event_map.items():
        try:
            topics = [event_signature]
            log_filter = {
                "address": checksum_address,
                "topics": topics,
                "fromBlock": start_block,
                "toBlock": end_block,
            }
            print(f"\nRequesting logs for {event_name} with filter:")
            print(log_filter)
            logs = w3.eth.get_logs(log_filter)
            for log in logs:
                block = w3.eth.get_block(log["blockNumber"])
                timestamp = datetime.utcfromtimestamp(block["timestamp"]).isoformat()

                # Decode the log data based on event type
                if event_name == "Mint":
                    # Mint: sender (indexed), amount0 (non-indexed), amount1 (non-indexed)
                    sender = log["topics"][1].hex()  # Remove '0x' prefix and pad
                    sender = "0x" + sender[-40:]  # Get last 20 bytes (40 hex chars)
                    decoded = decode(
                        ["uint256", "uint256"], bytes.fromhex(log["data"].hex()[2:])
                    )
                    cur.execute(
                        f"""
                        INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0, amount1, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            log["blockNumber"],
                            log["transactionHash"].hex(),
                            log["logIndex"],
                            sender,
                            str(decoded[0]),  # amount0
                            str(decoded[1]),  # amount1
                            timestamp,
                        ),
                    )
                elif event_name == "Burn":
                    # Burn: sender (indexed), to (indexed), amount0 (non-indexed), amount1 (non-indexed)
                    sender = log["topics"][1].hex()
                    sender = "0x" + sender[-40:]
                    to_addr = log["topics"][2].hex()
                    to_addr = "0x" + to_addr[-40:]
                    try:
                        # Ensure the data is properly padded for burn events
                        data_hex = log["data"].hex()
                        if (
                            len(data_hex) % 64 != 0
                        ):  # Each uint256 is 32 bytes = 64 hex chars
                            data_hex = data_hex.zfill(
                                128
                            )  # Pad to 2 * 64 = 128 hex chars for 2 uint256s

                        decoded = decode(
                            ["uint256", "uint256"], bytes.fromhex(data_hex)
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0, amount1, to_addr, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                log["blockNumber"],
                                log["transactionHash"].hex(),
                                log["logIndex"],
                                sender,
                                str(decoded[0]),  # amount0
                                str(decoded[1]),  # amount1
                                to_addr,
                                timestamp,
                            ),
                        )
                    except Exception as e:
                        print(f"Error decoding Burn event: {e}")
                        print(f"Log data length: {len(log['data'])} bytes")
                        print(f"Log data: {log['data'].hex()}")
                        continue
                elif event_name == "Swap":
                    # Swap: sender (indexed), to (indexed), amount0In (non-indexed), amount1In (non-indexed), amount0Out (non-indexed), amount1Out (non-indexed)
                    sender = log["topics"][1].hex()
                    sender = "0x" + sender[-40:]
                    to_addr = log["topics"][2].hex()
                    to_addr = "0x" + to_addr[-40:]
                    try:
                        # Ensure the data is properly padded
                        data_hex = log["data"].hex()
                        if (
                            len(data_hex) % 64 != 0
                        ):  # Each uint256 is 32 bytes = 64 hex chars
                            data_hex = data_hex.zfill(
                                256
                            )  # Pad to 4 * 64 = 256 hex chars

                        decoded = decode(
                            ["uint256", "uint256", "uint256", "uint256"],
                            bytes.fromhex(data_hex),
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0In, amount1In, amount0Out, amount1Out, to_addr, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                log["blockNumber"],
                                log["transactionHash"].hex(),
                                log["logIndex"],
                                sender,
                                str(decoded[0]),  # amount0In
                                str(decoded[1]),  # amount1In
                                str(decoded[2]),  # amount0Out
                                str(decoded[3]),  # amount1Out
                                to_addr,
                                timestamp,
                            ),
                        )
                    except Exception as e:
                        print(f"Error decoding Swap event: {e}")
                        print(f"Log data length: {len(log['data'])} bytes")
                        print(f"Log data: {log['data'].hex()}")
                        continue
            print(f"Fetched and stored {len(logs)} {event_name} events.")
        except Exception as e:
            print(f"Error fetching {event_name}: {e}")
    conn.commit()
    conn.close()


def get_latest_block(w3: Web3) -> int:
    return w3.eth.block_number


def get_block_by_timestamp(w3: Web3, target_ts: int) -> int:
    latest = w3.eth.block_number
    earliest = 1
    while earliest < latest:
        mid = (earliest + latest) // 2
        block = w3.eth.get_block(mid)
        if block["timestamp"] < target_ts:
            earliest = mid + 1
        else:
            latest = mid
    return earliest


def fetch_last_week_events():
    w3 = get_web3()
    abi = load_abi()
    # Convert to checksum address
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)
    contract = w3.eth.contract(address=checksum_address, abi=abi)
    conn = connect_db()
    cur = conn.cursor()

    latest_block = w3.eth.block_number
    one_week_ago = int((datetime.utcnow() - timedelta(days=7)).timestamp())
    start_block = get_block_by_timestamp(w3, one_week_ago)
    print(f"Fetching from block {start_block} to {latest_block}")

    chunk_size = 1000
    for chunk_start in range(start_block, latest_block + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, latest_block)
        print(f"Processing blocks {chunk_start} to {chunk_end}")
        fetch_and_store_events(chunk_start, chunk_end)
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        start_block = int(sys.argv[1])
        end_block = int(sys.argv[2])
        print(f"Fetching events from block {start_block} to {end_block}")
        fetch_and_store_events(start_block, end_block)
    else:
        print("No block range provided, fetching last week of events...")
        fetch_last_week_events()
    print("Done. Data is in arbitrum_weth_fox_events.db.")
