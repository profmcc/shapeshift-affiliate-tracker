"""
Relay Affiliate Fee Listener

Listens for affiliate fee events on supported chains and stores them in a database.

- Uses shared.config for config loading
- Uses shared.logging for logger setup
- Uses shared.db for database access

Example usage:
    PYTHONPATH=. python listeners/relay_listener.py
"""
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3

from shared.logging import setup_logger, get_logger
from shared.db import connect_db, ensure_schema
from shared.config import load_config

setup_logger()
logger = get_logger(__name__)

DB_PATH = 'shapeshift_relay_transactions.db'
RELAY_CONTRACT = "0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98"
ARBITRUM_RPC = f"https://arbitrum-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')}"

# --- DB ---
def init_database(db_path: str = DB_PATH) -> None:
    """Initialize the relay_transactions table."""
    schema_sql = '''
        CREATE TABLE IF NOT EXISTS relay_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE NOT NULL,
            block_number INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            from_address TEXT NOT NULL,
            volume_usd REAL NOT NULL,
            tokens TEXT NOT NULL,
            raw_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    '''
    ensure_schema(db_path, schema_sql)

# --- Web3 Helpers ---
def get_web3_connection(rpc_url: str) -> Optional[Web3]:
    """Get a Web3 connection for a given RPC URL."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if w3.is_connected():
        return w3
    logger.error(f"Failed to connect to {rpc_url}")
    return None

# --- Event Parsing ---
def parse_relay_event(log: dict, w3: Web3) -> Optional[dict]:
    """Parse a relay contract event log. (Stub: implement actual parsing logic)"""
    try:
        tx_hash = log['transactionHash'].hex()
        block_number = log['blockNumber']
        block = w3.eth.get_block(block_number)
        timestamp = datetime.utcfromtimestamp(block['timestamp']).isoformat()
        # Example fields (replace with actual event parsing):
        return {
            'tx_hash': tx_hash,
            'block_number': block_number,
            'timestamp': timestamp,
            'from_address': None,
            'volume_usd': None,
            'tokens': None,
            'raw_data': str(log)
        }
    except Exception as e:
        logger.warning(f"Malformed relay log: {e}")
        return None

# --- Main Chain Scan ---
def scan_chain(rpc_url: str, contract_address: str) -> int:
    """Scan the relay contract for events."""
    w3 = get_web3_connection(rpc_url)
    if not w3:
        return 0
    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - 2000)
    batch_size = 1000
    block_start = start_block
    total_found = 0
    while block_start <= latest_block:
        block_end = min(block_start + batch_size - 1, latest_block)
        filter_params = {
            'fromBlock': block_start,
            'toBlock': block_end,
            'address': contract_address,
            # 'topics': [...],
        }
        logger.info(f"[relay] filter_params: {filter_params}")
        try:
            logs = w3.eth.get_logs(filter_params)
        except Exception as e:
            logger.error(f"relay: Error fetching logs {block_start}-{block_end}: {e}")
            block_start += batch_size
            continue
        events = []
        for log in logs:
            event = parse_relay_event(log, w3)
            if event:
                events.append(event)
        save_events_to_db(events)
        total_found += len(events)
        logger.info(f"relay: {len(events)} events in blocks {block_start}-{block_end}")
        time.sleep(1)
        block_start = block_end + 1
    return total_found

# --- DB Save ---
def save_events_to_db(events: List[dict], db_path: str = DB_PATH) -> None:
    """Save a list of event dicts to the database."""
    if not events:
        return
    with connect_db(db_path) as conn:
        cursor = conn.cursor()
        for event in events:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO relay_transactions 
                    (tx_hash, block_number, timestamp, from_address, volume_usd, tokens, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['tx_hash'], event['block_number'], event['timestamp'], event['from_address'],
                    event['volume_usd'], event['tokens'], event['raw_data']
                ))
            except Exception as e:
                logger.error(f"Failed to save event: {e}")

# --- Main ---
def main() -> None:
    """
    Main entry point for the Relay affiliate fee listener.
    Loads config, sets up logging and database, and starts event processing.
    """
    logger = setup_logger("relay_listener")
    config = load_config("listeners/relay_listener_config.yaml")
    db_path = config.get("db_path", "relay_affiliate_fees.sqlite")
    conn = connect_db(db_path)
    schema_sql = config.get("schema_sql", """
        CREATE TABLE IF NOT EXISTS affiliate_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            affiliate_address TEXT,
            fee_amount TEXT,
            token_address TEXT,
            timestamp INTEGER
        );
    """)
    ensure_schema(conn, schema_sql)
    # ... rest of event processing ...

if __name__ == "__main__":
    main() 