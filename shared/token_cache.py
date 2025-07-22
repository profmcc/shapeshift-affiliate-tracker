import sqlite3
from typing import Optional, Dict
from web3 import Web3
import threading
import os

_DB_PATH = os.path.expanduser('~/.token_cache.sqlite')
_WEB3 = None
_DB_LOCK = threading.Lock()

# --- DB Schema ---
_SCHEMA = '''
CREATE TABLE IF NOT EXISTS tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    decimals INTEGER,
    price REAL,
    updated_at INTEGER
);
'''

# --- Web3 Init ---
def init_web3(rpc_url: str) -> None:
    """Initialize Web3 connection for fallback lookups."""
    global _WEB3
    _WEB3 = Web3(Web3.HTTPProvider(rpc_url))

# --- DB Connection ---
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(_SCHEMA)
    return conn

# --- Main API ---
def get_token_info(address: str) -> Optional[Dict]:
    """Get token info from cache, fallback to Web3 if missing."""
    address = Web3.to_checksum_address(address)
    with _DB_LOCK:
        conn = _get_conn()
        cur = conn.execute('SELECT symbol, name, decimals, price FROM tokens WHERE address = ?', (address,))
        row = cur.fetchone()
        if row:
            symbol, name, decimals, price = row
            return {'address': address, 'symbol': symbol, 'name': name, 'decimals': decimals, 'price': price}
        # Fallback to Web3
        if not _WEB3:
            raise RuntimeError('Web3 not initialized. Call init_web3() first.')
        try:
            contract = _WEB3.eth.contract(address=address, abi=[
                {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
                {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
                {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
            ])
            symbol = contract.functions.symbol().call()
            name = contract.functions.name().call()
            decimals = contract.functions.decimals().call()
            price = None
            # Insert into cache
            conn.execute('INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) VALUES (?, ?, ?, ?, ?, strftime("%s","now"))',
                         (address, symbol, name, decimals, price))
            conn.commit()
            return {'address': address, 'symbol': symbol, 'name': name, 'decimals': decimals, 'price': price}
        except Exception as e:
            return None
        finally:
            conn.close()

def format_token_amount(amount: int, address: str) -> str:
    """Format a raw token amount using cached decimals."""
    info = get_token_info(address)
    if not info or info['decimals'] is None:
        return str(amount)
    decimals = info['decimals']
    return f"{amount / (10 ** decimals):,.6f} {info['symbol'] or ''}" 