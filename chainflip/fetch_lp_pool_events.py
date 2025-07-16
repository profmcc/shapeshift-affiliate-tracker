import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List
from web3 import Web3
# from web3.middleware import geth_poa_middleware  # Deprecated in newer web3.py versions
from web3.types import LogReceipt
import json

# --- CONFIG ---
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
POOL_ADDRESS = Web3.to_checksum_address('0x470e8de2eBaef52014A47Cb5E6aF86884947F08c')
ABI_PATH = os.path.join(os.path.dirname(__file__), 'abis', 'UniswapV3Pool.json')
DB_PATH = os.path.join(os.path.dirname(__file__), 'lp_pool_events.db')

# --- DB SCHEMA ---
CREATE_TABLES_SQL = '''
CREATE TABLE IF NOT EXISTS liquidity_added (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    owner TEXT,
    tick_lower INTEGER,
    tick_upper INTEGER,
    amount TEXT,
    amount0 TEXT,
    amount1 TEXT,
    timestamp TEXT
);
CREATE TABLE IF NOT EXISTS liquidity_removed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    owner TEXT,
    tick_lower INTEGER,
    tick_upper INTEGER,
    amount TEXT,
    amount0 TEXT,
    amount1 TEXT,
    timestamp TEXT
);
CREATE TABLE IF NOT EXISTS fees_collected (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER,
    tx_hash TEXT,
    log_index INTEGER,
    sender TEXT,
    recipient TEXT,
    amount0 TEXT,
    amount1 TEXT,
    timestamp TEXT
);
'''

# --- UTILS ---
def get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    # If using a testnet or chain with PoA, uncomment:
    # w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def load_abi() -> List[Dict[str, Any]]:
    with open(ABI_PATH, 'r') as f:
        return json.load(f)

def get_event_signatures(abi: List[Dict[str, Any]]) -> Dict[str, str]:
    sigs = {}
    for item in abi:
        if item['type'] == 'event':
            types = ','.join([inp['type'] for inp in item['inputs']])
            sig = f"{item['name']}({types})"
            sigs[item['name']] = Web3.keccak(text=sig).hex()
    return sigs

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(CREATE_TABLES_SQL)
    return conn

def parse_event(event_abi, log: LogReceipt, w3: Web3) -> Dict[str, Any]:
    return w3.codec.decode_event(event_abi, log['data'], log['topics'])

# --- MAIN LOGIC ---
def fetch_and_store_events(start_block: int = None, end_block: int = None):
    w3 = get_web3()
    abi = load_abi()
    contract = w3.eth.contract(address=POOL_ADDRESS, abi=abi)
    event_sigs = get_event_signatures(abi)
    conn = connect_db()
    cur = conn.cursor()

    # Get latest block if not specified
    if end_block is None:
        end_block = w3.eth.block_number
    if start_block is None:
        # Default: last 10,000 blocks
        start_block = max(0, end_block - 10000)

    # Map event names to table names and their event signatures
    event_map = {
        'IncreaseLiquidity': ('liquidity_added', '0x9df5f06e17dd42061c93ad3f62f8cd221a70128544002cb650c17544a7734682'),
        'DecreaseLiquidity': ('liquidity_removed', '0xb335532bc337347110ac01eea95b4d2726f9ec357d9724abaab41fae8cb7ba90'),
        'Collect': ('fees_collected', '0xd180a977ce9f029a7ec05d2c280a2eea13167dd64eeae88a1758af2f586d7cc4'),
    }

    for event_name, (table, event_signature) in event_map.items():
        try:
            # Prepare log filter
            log_filter = {
                'address': POOL_ADDRESS,
                'topics': [event_signature],
                'fromBlock': start_block,
                'toBlock': end_block
            }
            print(f"\nRequesting logs for {event_name} with filter:")
            print(log_filter)
            # Get logs using eth_getLogs
            logs = w3.eth.get_logs(log_filter)
            for log in logs:
                block = w3.eth.get_block(log['blockNumber'])
                timestamp = datetime.utcfromtimestamp(block['timestamp']).isoformat()
                
                # Decode the log data based on event type
                if event_name == 'IncreaseLiquidity' or event_name == 'DecreaseLiquidity':
                    # Decode: owner (address), tickLower (int24), tickUpper (int24), amount (uint128), amount0 (uint256), amount1 (uint256)
                    decoded = w3.codec.decode_abi(
                        ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                        bytes.fromhex(log['data'][2:])  # Remove '0x' prefix
                    )
                    cur.execute(f'''
                        INSERT INTO {table} (block_number, tx_hash, log_index, owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log['blockNumber'],
                        log['transactionHash'].hex(),
                        log['logIndex'],
                        decoded[0],  # owner
                        decoded[1],  # tickLower
                        decoded[2],  # tickUpper
                        str(decoded[3]),  # amount
                        str(decoded[4]),  # amount0
                        str(decoded[5]),  # amount1
                        timestamp
                    ))
                elif event_name == 'Collect':
                    # Decode: sender (address), recipient (address), amount0 (uint256), amount1 (uint256)
                    decoded = w3.codec.decode_abi(
                        ['address', 'address', 'uint256', 'uint256'],
                        bytes.fromhex(log['data'][2:])  # Remove '0x' prefix
                    )
                    cur.execute(f'''
                        INSERT INTO {table} (block_number, tx_hash, log_index, sender, recipient, amount0, amount1, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log['blockNumber'],
                        log['transactionHash'].hex(),
                        log['logIndex'],
                        decoded[0],  # sender
                        decoded[1],  # recipient
                        str(decoded[2]),  # amount0
                        str(decoded[3]),  # amount1
                        timestamp
                    ))
            print(f"Fetched and stored {len(logs)} {event_name} events.")
        except Exception as e:
            print(f"Error fetching {event_name}: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Example usage: fetch last 10,000 blocks
    fetch_and_store_events()
    print("Done. Data is in lp_pool_events.db.") 