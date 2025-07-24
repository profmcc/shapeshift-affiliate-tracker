"""
Portals Affiliate Fee Listener

Listens for affiliate fee events on supported chains and stores them in a database.

- Uses shared.config for config loading
- Uses shared.logging for logger setup
- Uses shared.db for database access

Example usage:
    PYTHONPATH=. python listeners/portals_listener.py
"""

import os
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_utils import to_bytes, to_hex, to_checksum_address, to_canonical_address
import requests

from shared.logging import setup_logger, get_logger
from shared.db import connect_db, ensure_schema
from shared.config import load_config

setup_logger()
logger = get_logger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'portals_listener_config.yaml')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), 'portals_progress.json')
DB_PATH = 'databases/portals_transactions.db'

ERC20_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

PORTALS_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "inputToken", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "inputAmount", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "outputToken", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "outputAmount", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "broadcaster", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "partner", "type": "address"}
        ],
        "name": "Portal",
        "type": "event"
    }
]

def get_portals_event_topic() -> str:
    """
    Calculate the Portals event topic hash.
    Returns:
        str: The event topic hash for the Portals event.
    """
    from eth_utils import keccak
    event_signature = "Portal(address,uint256,address,uint256,address,address,address,address)"
    return '0x' + keccak(text=event_signature).hex()

PORTALS_EVENT_TOPIC = get_portals_event_topic()

def load_progress() -> dict:
    """Load progress from file or return empty dict."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress: dict) -> None:
    """
    Save progress to a JSON file.
    Args:
        progress (dict): Progress data to save.
    """
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(progress, f, indent=2)

def init_database() -> None:
    """Initialize the database schema using shared.db.ensure_schema."""
    schema_sql = '''
        CREATE TABLE IF NOT EXISTS portals_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT NOT NULL,
            tx_hash TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            block_timestamp INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            token TEXT,
            amount TEXT,
            sender TEXT,
            recipient TEXT,
            input_token TEXT,
            input_amount TEXT,
            output_token TEXT,
            output_amount TEXT,
            broadcaster TEXT,
            partner TEXT,
            is_portals_router BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    ensure_schema(DB_PATH, schema_sql)

def get_web3_providers(chain_name: str, chain_cfg: dict, alchemy_urls: dict) -> (Web3, Optional[Web3]):
    """
    Get primary and fallback Web3 providers for a chain.
    Args:
        chain_name (str): Name of the chain.
        chain_cfg (dict): Chain configuration.
        alchemy_urls (dict): Alchemy fallback URLs.
    Returns:
        (Web3, Optional[Web3]): Primary and fallback Web3 providers.
    """
    if chain_name == 'ethereum' and alchemy_urls.get('ethereum'):
        w3 = Web3(Web3.HTTPProvider(alchemy_urls['ethereum']))
        logger.info(f"[ethereum] FORCED to use Alchemy provider: {alchemy_urls['ethereum']}")
        fallback_w3 = None
    else:
        w3 = Web3(Web3.HTTPProvider(chain_cfg['rpc_url']))
        fallback_w3 = Web3(Web3.HTTPProvider(alchemy_urls[chain_name])) if alchemy_urls.get(chain_name) else None
    return w3, fallback_w3

def get_block_range(w3: Web3, chain_cfg: dict, progress: dict, today_mode: bool) -> (int, int):
    """
    Determine start and end block for scanning.
    Args:
        w3 (Web3): Web3 provider.
        chain_cfg (dict): Chain configuration.
        progress (dict): Progress data.
        today_mode (bool): Whether to scan only today's blocks.
    Returns:
        (int, int): Start and latest block numbers.
    """
    latest_block = w3.eth.block_number
    if today_mode:
        now = datetime.now(timezone.utc)
        today_utc = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        target_timestamp = int(today_utc.timestamp())
        config_start_block = chain_cfg['start_block']
        start_block = find_block_by_timestamp(w3, target_timestamp, config_start_block, latest_block)
        logger.info(f"Scanning only today's blocks: {start_block} to {latest_block}")
    else:
        start_block = progress.get(chain_cfg['name'], chain_cfg['start_block'])
        logger.info(f"Scanning blocks {start_block} to {latest_block}")
    return start_block, latest_block

def find_block_by_timestamp(w3: Web3, target_timestamp: int, start_block: int, end_block: int) -> int:
    """
    Binary search for the first block with timestamp >= target_timestamp.
    Args:
        w3 (Web3): Web3 provider.
        target_timestamp (int): Target UTC timestamp.
        start_block (int): Start block number.
        end_block (int): End block number.
    Returns:
        int: Block number with timestamp >= target_timestamp.
    """
    low = start_block
    high = end_block
    result = end_block
    while low <= high:
        mid = (low + high) // 2
        block = w3.eth.get_block(mid)
        if block['timestamp'] < target_timestamp:
            low = mid + 1
        else:
            result = mid
            high = mid - 1
    return result

def fetch_logs_with_retry(w3: Web3, filter_params: dict, chain_name: str, block_start: int, block_end: int, max_retries: int = 5, fallback_w3: Optional[Web3] = None) -> (List[Any], Web3):
    """
    Fetch logs with retry and fallback logic.
    Args:
        w3 (Web3): Web3 provider.
        filter_params (dict): Log filter parameters.
        chain_name (str): Name of the chain.
        block_start (int): Start block.
        block_end (int): End block.
        max_retries (int): Max retry attempts.
        fallback_w3 (Optional[Web3]): Fallback provider.
    Returns:
        (List[Any], Web3): Logs and the Web3 provider used.
    """
    logger.info(f"[{chain_name}] Using provider: {getattr(w3.provider, 'endpoint_uri', 'unknown')}")
    for attempt in range(max_retries):
        try:
            return w3.eth.get_logs(filter_params), w3
        except Exception as e:
            is_429 = '429' in str(e)
            if is_429 and fallback_w3 is not None and 'infura' in getattr(w3.provider, 'endpoint_uri', ''):
                logger.warning(f"{chain_name}: Rate limited by Infura. Switching to Alchemy...")
                logger.info(f"[{chain_name}] Switching to provider: {getattr(fallback_w3.provider, 'endpoint_uri', 'unknown')}")
                return 'SWITCH_TO_ALCHEMY', fallback_w3
            if is_429:
                wait = 2 ** attempt
                logger.warning(f"{chain_name}: Rate limited fetching logs {block_start}-{block_end}. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise
    logger.error(f"{chain_name}: Max retries exceeded for blocks {block_start}-{block_end}")
    return [], w3

def process_log_entry(log: dict, chain_name: str, dao_address: str, portals_contracts: List[str], w3: Web3) -> Optional[dict]:
    """
    Process a single log entry and return an event dict if relevant.
    Args:
        log (dict): Log entry.
        chain_name (str): Name of the chain.
        dao_address (str): DAO address.
        portals_contracts (List[str]): List of Portals router addresses.
        w3 (Web3): Web3 provider.
    Returns:
        Optional[dict]: Parsed event dict or None.
    """
    event_topic = log['topics'][0].hex()
    if not event_topic.startswith('0x'):
        event_topic = '0x' + event_topic
    if event_topic == ERC20_TRANSFER_TOPIC:
        return parse_erc20_transfer_event(log, chain_name, dao_address, portals_contracts, w3)
    elif event_topic == PORTALS_EVENT_TOPIC:
        return parse_portals_event(log, chain_name, w3)
    else:
        logger.debug(f"Skipping log with unknown event topic: {event_topic}")
        return None

def parse_erc20_transfer_event(log: dict, chain_name: str, dao_address: str, portals_contracts: List[str], w3: Web3) -> Optional[dict]:
    """
    Parse an ERC-20 Transfer event log.
    Args:
        log (dict): Log entry.
        chain_name (str): Name of the chain.
        dao_address (str): DAO address.
        portals_contracts (List[str]): List of Portals router addresses.
        w3 (Web3): Web3 provider.
    Returns:
        Optional[dict]: Parsed event dict or None.
    """
    try:
        from_address = to_checksum_address('0x' + log['topics'][1].hex()[-40:])
        to_address = to_checksum_address('0x' + log['topics'][2].hex()[-40:])
        dao_address_norm = to_checksum_address(dao_address)
        if to_address != dao_address_norm:
            logger.debug(f"Skipping - recipient is not DAO address")
            return None
        tx_hash = log['transactionHash'].hex()
        tx = w3.eth.get_transaction(tx_hash)
        is_portals_router = False
        if tx['to']:
            tx_to_norm = to_checksum_address(tx['to'])
            is_portals_router = any(to_checksum_address(router) == tx_to_norm for router in portals_contracts)
        block_number = log['blockNumber']
        try:
            block = w3.eth.get_block(block_number)
            timestamp = block['timestamp']
        except Exception:
            timestamp = 0
        try:
            amount = int(log['data'].hex(), 16)
        except Exception as e:
            logger.warning(f"Failed to parse amount from log data: {e}")
            amount = 0
        return {
            'chain': chain_name,
            'tx_hash': tx_hash,
            'block_number': block_number,
            'block_timestamp': timestamp,
            'event_type': 'ERC20_TRANSFER',
            'token': log['address'],
            'amount': str(amount),
            'sender': from_address,
            'recipient': to_address,
            'input_token': None,
            'input_amount': None,
            'output_token': None,
            'output_amount': None,
            'broadcaster': None,
            'partner': None,
            'is_portals_router': is_portals_router
        }
    except Exception as e:
        logger.warning(f"Malformed ERC-20 log: {e}")
        return None

def parse_portals_event(log: dict, chain_name: str, w3: Web3) -> Optional[dict]:
    """
    Parse a Portals event log.
    Args:
        log (dict): Log entry.
        chain_name (str): Name of the chain.
        w3 (Web3): Web3 provider.
    Returns:
        Optional[dict]: Parsed event dict or None.
    """
    try:
        sender = '0x' + log['topics'][1].hex()[-40:]
        broadcaster = '0x' + log['topics'][2].hex()[-40:]
        partner = '0x' + log['topics'][3].hex()[-40:]
        data = log['data']
        data_hex = data.hex() if hasattr(data, 'hex') else data
        data_bytes = bytes.fromhex(data_hex[2:])
        input_token = '0x' + data_bytes[0:32].hex()[-40:]
        input_amount = int.from_bytes(data_bytes[32:64], 'big')
        output_token = '0x' + data_bytes[64:96].hex()[-40:]
        output_amount = int.from_bytes(data_bytes[96:128], 'big')
        recipient = '0x' + data_bytes[128:160].hex()[-40:]
        tx_hash = log['transactionHash'].hex()
        block_number = log['blockNumber']
        try:
            block = w3.eth.get_block(block_number)
            timestamp = block['timestamp']
        except Exception:
            timestamp = 0
        return {
            'chain': chain_name,
            'tx_hash': tx_hash,
            'block_number': block_number,
            'block_timestamp': timestamp,
            'input_token': input_token,
            'input_amount': str(input_amount),
            'output_token': output_token,
            'output_amount': str(output_amount),
            'sender': sender,
            'broadcaster': broadcaster,
            'recipient': recipient,
            'partner': partner,
            'event_type': 'portals_event'
        }
    except Exception as e:
        logger.warning(f"Malformed Portals event log: {e}")
        return None

def scan_chain(
    chain_name: str,
    chain_cfg: dict,
    dao_address: str,
    portals_contracts: List[str],
    progress: dict,
    batch_size: int = 1000,
    today_mode: bool = False,
    alchemy_urls: dict = None
) -> int:
    """
    Scan a chain for Portals and ERC-20 events.
    Args:
        chain_name (str): Name of the chain.
        chain_cfg (dict): Chain configuration.
        dao_address (str): DAO address.
        portals_contracts (List[str]): List of Portals router addresses.
        progress (dict): Progress data.
        batch_size (int): Batch size for log fetching.
        today_mode (bool): Whether to scan only today's blocks.
        alchemy_urls (dict): Alchemy fallback URLs.
    Returns:
        int: Total number of events found.
    """
    w3, fallback_w3 = get_web3_providers(chain_name, chain_cfg, alchemy_urls or {})
    if not w3.is_connected():
        logger.error(f"Failed to connect to {chain_name}")
        return 0
    start_block, latest_block = get_block_range(w3, chain_cfg, progress, today_mode)
    min_batch, max_batch = 10, 1000
    adaptive_batch = batch_size
    block_start = start_block
    total_found = 0
    while block_start <= latest_block:
        block_end = min(block_start + adaptive_batch - 1, latest_block)
        dao_topic = '0x' + to_canonical_address(dao_address).hex().rjust(64, '0')
        filter_params = {
            'fromBlock': block_start,
            'toBlock': block_end,
            'topics': [
                [ERC20_TRANSFER_TOPIC, PORTALS_EVENT_TOPIC],
                None,
                dao_topic
            ]
        }
        logger.info(f"[{chain_name}] filter_params: {filter_params} (batch size: {adaptive_batch})")
        try:
            logs, new_w3 = fetch_logs_with_retry(w3, filter_params, chain_name, block_start, block_end, fallback_w3=fallback_w3)
            if logs == 'SWITCH_TO_ALCHEMY':
                w3 = new_w3
                logs, _ = fetch_logs_with_retry(w3, filter_params, chain_name, block_start, block_end, fallback_w3=None)
            if not isinstance(logs, list):
                logs = []
            if adaptive_batch < max_batch:
                adaptive_batch = min(adaptive_batch * 2, max_batch)
            logger.info(f"[{chain_name}] Success: {len(logs)} logs, increasing batch size to {adaptive_batch}")
        except Exception as e:
            if '400' in str(e) and adaptive_batch > min_batch:
                adaptive_batch = max(adaptive_batch // 2, min_batch)
                logger.warning(f"[{chain_name}] 400 error, reducing batch size to {adaptive_batch}")
                continue
            logger.error(f"{chain_name}: Error fetching logs {block_start}-{block_end}: {e}")
            block_start += adaptive_batch
            continue
        events = []
        for log in logs:
            event = process_log_entry(log, chain_name, dao_address, portals_contracts, w3)
            if event:
                events.append(event)
        save_events_to_db(events)
        total_found += len(events)
        progress[chain_name] = block_end + 1
        save_progress(progress)
        logger.info(f"{chain_name}: {len(events)} events in blocks {block_start}-{block_end}")
        time.sleep(1)
        block_start = block_end + 1
    return total_found

def save_events_to_db(events: List[dict]) -> None:
    """
    Save a list of event dicts to the database.
    Args:
        events (List[dict]): List of event dicts.
    """
    if not events:
        return
    with connect_db(DB_PATH) as conn:
        cursor = conn.cursor()
        for event in events:
            try:
                if event['event_type'] == 'ERC20_TRANSFER':
                    cursor.execute('''
                        INSERT OR IGNORE INTO portals_transactions 
                        (chain, tx_hash, block_number, block_timestamp, event_type, token, amount, sender, recipient, is_portals_router)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event['chain'], event['tx_hash'], event['block_number'], event['block_timestamp'], 
                        event['event_type'], event['token'], event['amount'], event['sender'], event['recipient'],
                        event.get('is_portals_router', False)
                    ))
                elif event['event_type'] == 'portals_event':
                    cursor.execute('''
                        INSERT OR IGNORE INTO portals_transactions 
                        (chain, tx_hash, block_number, block_timestamp, event_type, sender, recipient, 
                         input_token, input_amount, output_token, output_amount, broadcaster, partner)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event['chain'], event['tx_hash'], event['block_number'], event['block_timestamp'],
                        event['event_type'], event['sender'], event['recipient'], event['input_token'],
                        event['input_amount'], event['output_token'], event['output_amount'],
                        event['broadcaster'], event['partner']
                    ))
            except Exception as e:
                logger.error(f"Failed to save event: {e}")

def main() -> None:
    """
    Main entry point for the Portals affiliate fee listener.
    Loads config, sets up logging and database, and starts event processing.
    """
    logger = setup_logger("portals_listener")
    config = load_config("listeners/portals_listener_config.yaml")
    db_path = config.get("db_path", "portals_affiliate_fees.sqlite")
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

    progress = load_progress()
    init_database()

    chains = config['chains']
    dao_addresses = config['dao_addresses']
    portals_contracts = config.get('portals_contracts', [])

    # Alchemy URLs for fallback
    ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
    alchemy_urls = {
        'ethereum': f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
        'polygon': f'https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
        'arbitrum': f'https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
        'optimism': f'https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
        'base': f'https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
    }

    logger.info("🚀 Starting Portals affiliate fee listener (refactored)")
    results = {}
    for chain_name, chain_cfg in chains.items():
        dao_address = dao_addresses.get(chain_name)
        batch_size = 10  # You can make this configurable
        try:
            found = scan_chain(
                chain_name,
                chain_cfg,
                dao_address,
                portals_contracts,
                progress,
                batch_size,
                today_mode=args.today,
                alchemy_urls=alchemy_urls
            )
            results[chain_name] = found
        except Exception as e:
            logger.error(f"{chain_name}: Error in scan: {e}")
    logger.info("\n✅ Portals listener completed!")
    for chain, found in results.items():
        logger.info(f"   {chain}: {found} events found")

if __name__ == "__main__":
    main() 