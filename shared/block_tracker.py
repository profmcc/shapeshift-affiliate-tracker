import sqlite3
import os
from typing import Optional, Dict
from datetime import datetime
from web3 import Web3

_DB_PATH = os.path.expanduser('~/.block_tracker.sqlite')

# RPC endpoints for different chains
RPC_ENDPOINTS = {
    'arbitrum': "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'ethereum': "https://mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'polygon': "https://polygon-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'optimism': "https://optimism-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'base': "https://mainnet.base.org",
    'avalanche': "https://avalanche-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'bsc': "https://bsc-dataseed.binance.org"
}

# July 1st, 2024 timestamps (approximate)
JULY_1ST_TIMESTAMP = 1719792000  # July 1st, 2024 00:00:00 UTC

_SCHEMA = '''
CREATE TABLE IF NOT EXISTS block_tracking (
    listener_name TEXT PRIMARY KEY,
    chain TEXT NOT NULL,
    last_processed_block INTEGER NOT NULL,
    last_run_timestamp INTEGER NOT NULL
);
'''

def init_database():
    """Initialize the block tracking database."""
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(_SCHEMA)
        conn.commit()

def get_july_1st_block(chain: str) -> int:
    """Get the block number closest to July 1st, 2024 for a given chain."""
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[chain]))
    
    # Binary search to find the block closest to July 1st
    left = 0
    right = w3.eth.block_number
    
    while left < right:
        mid = (left + right) // 2
        try:
            block = w3.eth.get_block(mid)
            if block['timestamp'] < JULY_1ST_TIMESTAMP:
                left = mid + 1
            else:
                right = mid
        except:
            right = mid - 1
    
    return left

def get_last_processed_block(listener_name: str) -> Optional[int]:
    """Get the last processed block for a listener."""
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute('SELECT last_processed_block FROM block_tracking WHERE listener_name = ?', (listener_name,))
        row = cur.fetchone()
        return row[0] if row else None

def set_last_processed_block(listener_name: str, chain: str, block_number: int):
    """Set the last processed block for a listener."""
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO block_tracking (listener_name, chain, last_processed_block, last_run_timestamp)
            VALUES (?, ?, ?, ?)
        ''', (listener_name, chain, block_number, int(datetime.now().timestamp())))
        conn.commit()

def get_start_block(listener_name: str, chain: str) -> int:
    """Get the starting block for a listener (either last processed + 1 or July 1st)."""
    last_block = get_last_processed_block(listener_name)
    if last_block is None:
        # First run - start from July 1st
        return get_july_1st_block(chain)
    else:
        # Continue from last processed block + 1
        return last_block + 1

def get_all_listeners_status() -> Dict[str, Dict]:
    """Get status of all listeners."""
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute('SELECT listener_name, chain, last_processed_block, last_run_timestamp FROM block_tracking')
        rows = cur.fetchall()
        
        status = {}
        for row in rows:
            listener_name, chain, last_block, timestamp = row
            status[listener_name] = {
                'chain': chain,
                'last_processed_block': last_block,
                'last_run': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            }
        return status

if __name__ == "__main__":
    # Initialize database
    init_database()
    print("Block tracking database initialized.")
    
    # Show July 1st blocks for all chains
    print("\nJuly 1st, 2024 block numbers:")
    for chain in RPC_ENDPOINTS:
        try:
            block = get_july_1st_block(chain)
            print(f"  {chain}: {block:,}")
        except Exception as e:
            print(f"  {chain}: Error - {e}") 