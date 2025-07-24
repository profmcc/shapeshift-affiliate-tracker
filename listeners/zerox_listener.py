"""
0x Protocol Affiliate Fee Listener

Listens for affiliate fee events on supported chains and stores them in a database.

- Uses shared.config for config loading
- Uses shared.logging for logger setup
- Uses shared.db for database access

Example usage:
    PYTHONPATH=. python listeners/zerox_listener.py
"""
#!/usr/bin/env python3
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_utils import to_checksum_address

from shared.logging import setup_logger
from shared.db import connect_db, ensure_schema
from shared.config import load_config

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'zerox_listener_config.yaml')
DB_PATH = 'shapeshift_zerox_transactions.db'

# --- DB ---
def init_database() -> None:
    """Initialize the database schema using shared.db.ensure_schema."""
    schema_sql = '''
        CREATE TABLE IF NOT EXISTS zerox_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT NOT NULL,
            tx_hash TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            block_timestamp INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            maker TEXT,
            taker TEXT,
            input_token TEXT,
            output_token TEXT,
            input_amount TEXT,
            output_amount TEXT,
            protocol_fee TEXT,
            affiliate_fee_amount TEXT,
            affiliate_fee_usd REAL,
            volume_usd REAL,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            UNIQUE(tx_hash, chain, event_type)
        )
    '''
    ensure_schema(DB_PATH, schema_sql)

# --- Web3 Helpers ---
def get_web3_provider(chain_name: str, chain_cfg: dict, logger) -> Web3:
    """Get Web3 provider for a chain."""
    w3 = Web3(Web3.HTTPProvider(chain_cfg['rpc_url']))
    if w3.is_connected():
        return w3
    logger.error(f"Failed to connect to {chain_cfg['rpc_url']}")
    return None

def fetch_logs(web3: Web3, contract_address: str, from_block: int, to_block: int, logger) -> List[dict]:
    """
    Fetch logs for a contract address and block range.
    
    Args:
        web3: Web3 instance
        contract_address: Contract address as hex string
        from_block: Starting block number
        to_block: Ending block number
        logger: Logger instance
        
    Returns:
        List of log events
    """
    filter_params = {
        'fromBlock': from_block,
        'toBlock': to_block,
        'address': contract_address  # Ensure this is a string
    }
    logger.info(f"filter_params: {filter_params}")
    try:
        logs = web3.eth.get_logs(filter_params)
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs {from_block}-{to_block}: {e}")
        return []

# --- Event Parsing ---
def parse_zerox_event(log: dict, chain_name: str, w3: Web3) -> Optional[dict]:
    """Parse a 0x Protocol event log. (Stub: implement actual parsing logic)"""
    # This is a placeholder. Actual event parsing logic should be implemented here.
    try:
        tx_hash = log['transactionHash'].hex()
        block_number = log['blockNumber']
        block = w3.eth.get_block(block_number)
        timestamp = block['timestamp']
        # Example fields (replace with actual event parsing):
        return {
            'chain': chain_name,
            'tx_hash': tx_hash,
            'block_number': block_number,
            'block_timestamp': timestamp,
            'event_type': '0x_swap',
            'maker': None,
            'taker': None,
            'input_token': None,
            'output_token': None,
            'input_amount': None,
            'output_amount': None,
            'protocol_fee': None,
            'affiliate_fee_amount': None,
            'affiliate_fee_usd': None,
            'volume_usd': None
        }
    except Exception as e:
        logger.warning(f"Malformed 0x log: {e}")
        return None

# --- Main Chain Scan ---
def scan_chain(chain_name: str, chain_cfg: dict, logger) -> int:
    """
    Scan a chain for 0x Protocol events.
    
    Args:
        chain_name: Name of the chain
        chain_cfg: Chain configuration dict
        logger: Logger instance
        
    Returns:
        Number of events found
    """
    w3 = get_web3_provider(chain_name, chain_cfg, logger)
    if not w3:
        return 0
    
    contract_address = chain_cfg['zerox_contract']
    start_block = chain_cfg['start_block']
    chunk_size = chain_cfg['chunk_size']
    
    # Get current block
    try:
        current_block = w3.eth.block_number
    except Exception as e:
        logger.error(f"{chain_name}: Failed to get current block: {e}")
        return 0
    
    total_found = 0
    for from_block in range(start_block, current_block, chunk_size):
        to_block = min(from_block + chunk_size - 1, current_block)
        
        logs = fetch_logs(w3, contract_address, from_block, to_block, logger)
        if logs:
            events = []
            for log in logs:
                event = parse_zerox_event(log, chain_name, w3)
                if event:
                    events.append(event)
            
            if events:
                save_events_to_db(events)
                total_found += len(events)
                logger.info(f"{chain_name}: Found {len(events)} events in blocks {from_block}-{to_block}")
    
    return total_found

# --- DB Save ---
def save_events_to_db(events: List[dict]) -> None:
    """Save processed events to database."""
    if not events:
        return
    with connect_db(DB_PATH) as conn:
        cursor = conn.cursor()
        for event in events:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO zerox_transactions 
                    (chain, tx_hash, block_number, block_timestamp, event_type, maker, taker, input_token, output_token, input_amount, output_amount, protocol_fee, affiliate_fee_amount, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['chain'], event['tx_hash'], event['block_number'], event['block_timestamp'], event['event_type'],
                    event['maker'], event['taker'], event['input_token'], event['output_token'], event['input_amount'],
                    event['output_amount'], event['protocol_fee'], event['affiliate_fee_amount'], event['affiliate_fee_usd'], event['volume_usd']
                ))
            except Exception as e:
                logger.error(f"Failed to save event: {e}")

# --- Main ---
def main() -> None:
    """
    Main entry point for the 0x Protocol affiliate fee listener.
    Loads config, sets up logging and database, and starts event processing.
    """
    logger = setup_logger("zerox_listener")
    config = load_config("listeners/zerox_listener_config.yaml")
    db_path = config.get("db_path", "zerox_affiliate_fees.sqlite")
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
    
    logger.info("🚀 Starting 0x Protocol affiliate fee listener (refactored)")
    chains = config['chains']
    total_found = 0
    
    for chain_name, chain_cfg in chains.items():
        try:
            found = scan_chain(chain_name, chain_cfg, logger)
            total_found += found
            logger.info(f"   {chain_name}: {found} events found")
        except Exception as e:
            logger.error(f"{chain_name}: Error in scan: {e}")
    
    logger.info(f"\n✅ 0x Protocol listener completed!")
    logger.info(f"   ethereum: {total_found} events found")
    logger.info(f"   polygon: {total_found} events found")
    logger.info(f"   arbitrum: {total_found} events found")
    logger.info(f"   optimism: {total_found} events found")
    logger.info(f"   base: {total_found} events found")

if __name__ == "__main__":
    main() 