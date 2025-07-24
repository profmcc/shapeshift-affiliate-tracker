#!/usr/bin/env python3
"""
Portals Affiliate Fee Listener - Consolidated Version
Collects Portals affiliate fee data from EVM chains for ShapeShift affiliate tracking.
"""

import os
import sqlite3
import time
import json
import yaml
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from web3 import Web3
from concurrent.futures import ProcessPoolExecutor, as_completed
from dotenv import load_dotenv
import re
from eth_utils import to_bytes, to_hex, to_checksum_address, to_canonical_address
import requests

from shared.config import load_yaml_config
from shared.logging import setup_logging, get_logger
from shared.db import db_connection, init_table

setup_logging()
logger = get_logger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'portals_listener_config.yaml')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), 'portals_progress.json')
DB_PATH = 'databases/portals_transactions.db'

ERC20_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
PORTALS_EVENT_TOPIC = '0x0000000000000000000000000000000000000000000000000000000000000000'  # Placeholder, will be calculated

# Portals ABI for event parsing
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

# Calculate the Portal event topic
def get_portals_event_topic():
    from eth_utils import keccak
    event_signature = "Portal(address,uint256,address,uint256,address,address,address,address)"
    return '0x' + keccak(text=event_signature).hex()

PORTALS_EVENT_TOPIC = get_portals_event_topic()

# --- Config/Progress ---
def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(progress, f, indent=2)

# --- DB ---
def init_database(db_path=DB_PATH):
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
    init_table(db_path, schema_sql)

INFURA_API_KEY = os.getenv('INFURA_API_KEY')
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')

CHAIN_INFURA_URLS = {
    'ethereum': f'https://mainnet.infura.io/v3/{INFURA_API_KEY}' if INFURA_API_KEY else None,
    'polygon': f'https://polygon-mainnet.infura.io/v3/{INFURA_API_KEY}' if INFURA_API_KEY else None,
    'arbitrum': f'https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}' if INFURA_API_KEY else None,
    'optimism': f'https://optimism-mainnet.infura.io/v3/{INFURA_API_KEY}' if INFURA_API_KEY else None,
    'base': f'https://base-mainnet.infura.io/v3/{INFURA_API_KEY}' if INFURA_API_KEY else None,
}
CHAIN_ALCHEMY_URLS = {
    'ethereum': f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
    'polygon': f'https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
    'arbitrum': f'https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
    'optimism': f'https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
    'base': f'https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}' if ALCHEMY_API_KEY else None,
}

# Modified fetch_logs_with_retry to support fallback and log provider

def fetch_logs_with_retry(w3, filter_params, chain_name, block_start, block_end, max_retries=5, fallback_w3=None):
    logger.info(f"[{chain_name}] Using provider: {getattr(w3.provider, 'endpoint_uri', 'unknown')}")
    for attempt in range(max_retries):
        try:
            return w3.eth.get_logs(filter_params), w3
        except Exception as e:
            is_429 = False
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                is_429 = True
            elif '429' in str(e):
                is_429 = True
            if is_429 and fallback_w3 is not None and 'infura' in getattr(w3.provider, 'endpoint_uri', ''):
                logger.warning(f"{chain_name}: Rate limited by Infura. Switching to Alchemy for all further requests...")
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

def find_block_by_timestamp(w3, target_timestamp, start_block, end_block):
    # Binary search for the first block with timestamp >= target_timestamp
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

# --- Core Logic ---
def scan_chain(chain_name, chain_cfg, dao_address, portals_contracts, progress, batch_size=1000, today_mode=False):
    if chain_name == 'ethereum' and CHAIN_ALCHEMY_URLS.get('ethereum'):
        w3 = Web3(Web3.HTTPProvider(CHAIN_ALCHEMY_URLS['ethereum']))
        logger.info(f"[ethereum] FORCED to use Alchemy provider: {CHAIN_ALCHEMY_URLS['ethereum']}")
        fallback_w3 = None
    else:
        w3 = Web3(Web3.HTTPProvider(chain_cfg['rpc_url']))
        fallback_w3 = None
        if CHAIN_ALCHEMY_URLS.get(chain_name):
            fallback_w3 = Web3(Web3.HTTPProvider(CHAIN_ALCHEMY_URLS[chain_name]))
    if not w3.is_connected():
        logger.error(f"Failed to connect to {chain_name}")
        return 0
    latest_block = w3.eth.block_number
    if today_mode:
        now = datetime.now(timezone.utc)
        today_utc = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        target_timestamp = int(today_utc.timestamp())
        config_start_block = chain_cfg['start_block']
        start_block = find_block_by_timestamp(w3, target_timestamp, config_start_block, latest_block)
        logger.info(f"{chain_name}: Scanning only today's blocks: {start_block} to {latest_block}")
    else:
        start_block = progress.get(chain_name, chain_cfg['start_block'])
        logger.info(f"🔍 {chain_name}: Scanning blocks {start_block} to {latest_block}")
    total_found = 0
    min_batch = 10
    max_batch = 1000
    adaptive_batch = batch_size
    block_start = start_block
    while block_start <= latest_block:
        block_end = min(block_start + adaptive_batch - 1, latest_block)
        dao_topic = '0x' + to_canonical_address(dao_address).hex().rjust(64, '0')
        
        # Fetch both ERC-20 transfers to DAO and Portals events
        filter_params = {
            'fromBlock': block_start,
            'toBlock': block_end,
            'topics': [
                [ERC20_TRANSFER_TOPIC, PORTALS_EVENT_TOPIC],  # Either ERC-20 transfer or Portals event
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
            # If successful, try increasing batch size for next request
            if adaptive_batch < max_batch:
                adaptive_batch = min(adaptive_batch * 2, max_batch)
            logger.info(f"[{chain_name}] Success: {len(logs)} logs, increasing batch size to {adaptive_batch}")
        except Exception as e:
            # If 400 error, halve the batch size and retry
            if '400' in str(e) and adaptive_batch > min_batch:
                adaptive_batch = max(adaptive_batch // 2, min_batch)
                logger.warning(f"[{chain_name}] 400 error, reducing batch size to {adaptive_batch}")
                continue
            logger.error(f"{chain_name}: Error fetching logs {block_start}-{block_end}: {e}")
            block_start += adaptive_batch
            continue
        events = []
        # Process all logs (ERC-20 transfers and Portals events)
        print(f"[DEBUG] Processing {len(logs)} logs for blocks {block_start}-{block_end}")
        for log in logs:
            try:
                print(f"\n[DEBUG] Raw log: {log}")
                event_topic = log['topics'][0].hex()
                print(f"[DEBUG] Event topic: {event_topic}")
                
                # Normalize event topic to include 0x prefix for comparison
                if not event_topic.startswith('0x'):
                    event_topic = '0x' + event_topic
                
                if event_topic == ERC20_TRANSFER_TOPIC:
                    print(f"[DEBUG] Processing ERC-20 transfer event")
                    # Process ERC-20 Transfer event
                    from_address = '0x' + log['topics'][1].hex()[-40:]
                    to_address = '0x' + log['topics'][2].hex()[-40:]
                    from_address = to_checksum_address(from_address)
                    to_address = to_checksum_address(to_address)
                    dao_address_norm = to_checksum_address(dao_address)
                    print(f"[DEBUG] From: {from_address}, To: {to_address}, DAO: {dao_address_norm}")
                    if to_address != dao_address_norm:
                        print(f"[DEBUG] Skipping - recipient is not DAO address")
                        continue
                    print(f"[DEBUG] ✅ Recipient matches DAO address!")
                    
                    tx_hash = log['transactionHash'].hex()
                    tx = w3.eth.get_transaction(tx_hash)
                    print(f"[DEBUG] Found ERC-20 transfer to DAO: tx_hash={tx_hash}, from={from_address}, token={log['address']}, tx_to={tx['to']}")
                    
                    # Check if this is from a Portals router (for logging purposes)
                    is_portals_router = False
                    if tx['to']:
                        tx_to_norm = to_checksum_address(tx['to'])
                        for router in portals_contracts:
                            if to_checksum_address(router) == tx_to_norm:
                                is_portals_router = True
                                break
                    
                    if is_portals_router:
                        print(f"[DEBUG] ✅ Confirmed Portals router transaction!")
                    else:
                        print(f"[DEBUG] ⚠️  ERC-20 transfer to DAO but not direct Portals router call")
                    
                    block_number = log['blockNumber']
                    try:
                        block = w3.eth.get_block(block_number)
                        timestamp = block['timestamp']
                    except Exception:
                        timestamp = 0
                    
                    # Convert HexBytes to hex string for amount parsing
                    try:
                        amount = int(log['data'].hex(), 16)
                    except Exception as e:
                        print(f"[WARNING] Failed to parse amount from log data: {e}")
                        print(f"[DEBUG] Raw data (hex): {log['data'].hex()}")
                        print(f"[DEBUG] Raw data (bytes): {log['data']}")
                        amount = 0
                    
                    events.append({
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
                    })
                    print(f"[DEBUG] ✅ Added event to list. Total events: {len(events)}")
                
                elif event_topic == PORTALS_EVENT_TOPIC:
                    # Process Portals event
                    print(f"[DEBUG] Found Portals event: {log}")
                    # Parse the Portals event data
                    try:
                        # The Portals event has indexed and non-indexed parameters
                        # topics[1] = sender (indexed)
                        # topics[2] = broadcaster (indexed) 
                        # topics[3] = partner (indexed)
                        # data contains: inputToken, inputAmount, outputToken, outputAmount, recipient
                        
                        sender = '0x' + log['topics'][1].hex()[-40:]
                        broadcaster = '0x' + log['topics'][2].hex()[-40:]
                        partner = '0x' + log['topics'][3].hex()[-40:]
                        
                        # Parse the data field (non-indexed parameters)
                        data = log['data']
                        if hasattr(data, 'hex'):
                            data_hex = data.hex()
                        else:
                            data_hex = data
                        
                        # Remove the 0x prefix and parse the data
                        data_bytes = bytes.fromhex(data_hex[2:])
                        
                        # Parse the data according to the ABI structure
                        # Each parameter is 32 bytes (256 bits)
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
                        
                        print(f"[DEBUG] Parsed Portals event: sender={sender}, partner={partner}, input_amount={input_amount}, output_amount={output_amount}")
                        
                        events.append({
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
                        })
                        
                    except Exception as e:
                        print(f"[WARNING] Could not parse Portals event: {e}")
                        print(f"[DEBUG] Portals event data: {log}")
                        continue
                
                else:
                    print(f"[DEBUG] Skipping - event topic {event_topic} does not match ERC20_TRANSFER_TOPIC {ERC20_TRANSFER_TOPIC}")
                
            except Exception as e:
                print(f"[WARNING] Skipping malformed log: {e}")
                print(f"[DEBUG] Malformed log: {log}")
                continue
        
        save_events_to_db(events)
        total_found += len(events)
        progress[chain_name] = block_end + 1
        save_progress(progress)
        logger.info(f"{chain_name}: {len(events)} events in blocks {block_start}-{block_end}")
        time.sleep(1)
        block_start = block_end + 1
    return total_found

def save_events_to_db(events, db_path=DB_PATH):
    if not events:
        return
    with db_connection(db_path) as conn:
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
                print(f"[ERROR] Failed to save event: {e}")

# --- Main ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Portals Affiliate Fee Listener')
    parser.add_argument('--resume', action='store_true', help='Resume from last progress')
    parser.add_argument('--today', action='store_true', help='Scan only today\'s blocks (UTC)')
    args = parser.parse_args()

    config = load_yaml_config(CONFIG_PATH)
    progress = load_progress() if args.resume else {}
    init_database()

    chains = config['chains']
    dao_addresses = config['dao_addresses']
    portals_contracts = config.get('portals_contracts', [])

    logger.info("🚀 Starting Portals affiliate fee listener (sequential)")
    results = {}
    for chain_name, chain_cfg in chains.items():
        dao_address = dao_addresses.get(chain_name)
        batch_size = 10  # Force batch size to 10 for all chains
        try:
            found = scan_chain(chain_name, chain_cfg, dao_address, portals_contracts, progress, batch_size, today_mode=args.today)
            results[chain_name] = found
        except Exception as e:
            logger.error(f"{chain_name}: Error in scan: {e}")
    logger.info("\n✅ Portals listener completed!")
    for chain, found in results.items():
        logger.info(f"   {chain}: {found} events found")

if __name__ == "__main__":
    main() 