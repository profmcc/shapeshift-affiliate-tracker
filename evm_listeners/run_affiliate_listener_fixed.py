#!/usr/bin/env python3
"""
ShapeShift Affiliate Fee Tracker - Fixed Version
Uses actual event signatures found in the logs
"""

import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import requests
from eth_abi import decode
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'shapeshift_affiliate_fees_fixed.db'

# Use environment variables for RPC URLs
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
POLYGON_RPC = os.getenv('POLYGON_RPC', 'https://polygon-rpc.com')

# ShapeShift affiliate addresses by chain
SHAPESHIFT_AFFILIATES = {
    1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",      # Ethereum
    137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",     # Polygon
}

# Affiliate fee contract configurations
AFFILIATE_CONTRACTS = {
    1: {  # Ethereum
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'portals': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'rpc': INFURA_URL
    },
    137: {  # Polygon
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': POLYGON_RPC
    }
}

# Actual event signatures found in logs
EVENT_SIGNATURES = {
    'cowswap_trade': '0xa07a543ab8a018198e99ca0184c93fe9050a79400a0a723441f84de1d972cc17',  # Actual CowSwap event
    'cowswap_order': '0xed99827efb37016f2275f98c4bcf71c7551c75d59e9b450f79fa32e60be672c2',  # CowSwap order event
    'cowswap_invalidation': '0x40338ce1a7c49204f0099533b1e9a7ee0a3d261f84974ab7af36105b8c4e9db4',  # CowSwap invalidation
    'zerox_fill': '0x50273fa02273cceea9cf085b42de5c8af60624140168bd71357db833535877af',  # 0x fill event
    'zerox_cancel': '0xa015ad2dc32f266993958a0fd9884c746b971b254206f3478bc43e2f125c7b9e',  # 0x cancel event
    'erc20_transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
}

def setup_database():
    """Create the database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # CowSwap events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cowswap_events (
            tx_hash TEXT,
            block_number INTEGER,
            event_type TEXT,
            event_data TEXT,
            timestamp INTEGER
        )
    ''')
    
    # 0x Protocol events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zerox_events (
            tx_hash TEXT,
            block_number INTEGER,
            event_type TEXT,
            event_data TEXT,
            timestamp INTEGER
        )
    ''')
    
    # ERC20 transfers to affiliate addresses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS affiliate_transfers (
            tx_hash TEXT,
            block_number INTEGER,
            token_address TEXT,
            from_address TEXT,
            to_address TEXT,
            amount TEXT,
            timestamp INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Fixed affiliate fee database setup complete")

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain"""
    config = AFFILIATE_CONTRACTS.get(chain_id)
    if not config:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    return Web3(Web3.HTTPProvider(config['rpc']))

def get_block_range_for_week(chain_id: int) -> List[Tuple[int, int]]:
    """Get block ranges for the last week, split into smaller chunks"""
    w3 = get_web3_connection(chain_id)
    
    # Get current block
    current_block = w3.eth.block_number
    
    # Estimate blocks per day (varies by chain)
    blocks_per_day = {
        1: 7200,      # Ethereum ~12s blocks
        137: 28800,   # Polygon ~3s blocks
    }
    
    blocks_per_week = blocks_per_day.get(chain_id, 7200) * 7
    start_block = max(0, current_block - blocks_per_week)
    
    # Split into smaller chunks to avoid RPC limits
    chunk_size = 1000  # Smaller chunks
    ranges = []
    
    for i in range(start_block, current_block, chunk_size):
        end = min(i + chunk_size, current_block)
        ranges.append((i, end))
    
    logger.info(f"Chain {chain_id}: Split into {len(ranges)} chunks from {start_block} to {current_block}")
    return ranges

def fetch_all_contract_events(chain_id: int, start_block: int, end_block: int):
    """Fetch all events from affiliate contracts and look for ShapeShift involvement"""
    w3 = get_web3_connection(chain_id)
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all logs from all contracts
        all_logs = []
        for contract_name, contract_address in config.items():
            if contract_name == 'rpc':
                continue
                
            try:
                logs = w3.eth.get_logs({
                    'address': contract_address,
                    'fromBlock': start_block,
                    'toBlock': end_block
                })
                all_logs.extend(logs)
                logger.info(f"Found {len(logs)} logs from {contract_name}")
            except Exception as e:
                logger.error(f"Error fetching logs from {contract_name}: {e}")
        
        # Process all logs
        for log in all_logs:
            try:
                # Get transaction hash
                tx_hash = log['transactionHash'].hex() if hasattr(log['transactionHash'], 'hex') else str(log['transactionHash'])
                
                # Get block timestamp
                try:
                    block = w3.eth.get_block(log['blockNumber'])
                    timestamp = block['timestamp']
                except:
                    timestamp = int(time.time())
                
                # Determine event type
                event_sig = log['topics'][0].hex() if hasattr(log['topics'][0], 'hex') else log['topics'][0]
                
                # Store event data
                event_data = {
                    'topics': [topic.hex() if hasattr(topic, 'hex') else str(topic) for topic in log['topics']],
                    'data': log['data'].hex() if hasattr(log['data'], 'hex') else str(log['data']),
                    'address': log['address'],
                    'blockNumber': log['blockNumber'],
                    'logIndex': log['logIndex']
                }
                
                # Determine which contract this came from
                if log['address'].lower() == config.get('cowswap', '').lower():
                    cursor.execute('''
                        INSERT INTO cowswap_events 
                        (tx_hash, block_number, event_type, event_data, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tx_hash, log['blockNumber'], event_sig, json.dumps(event_data), timestamp))
                    
                elif log['address'].lower() == config.get('zerox', '').lower():
                    cursor.execute('''
                        INSERT INTO zerox_events 
                        (tx_hash, block_number, event_type, event_data, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tx_hash, log['blockNumber'], event_sig, json.dumps(event_data), timestamp))
                
                # Check for ERC20 transfers to affiliate address
                if event_sig == EVENT_SIGNATURES['erc20_transfer'] and len(log['topics']) >= 3:
                    to_address = '0x' + log['topics'][2][-40:].hex() if hasattr(log['topics'][2], 'hex') else '0x' + log['topics'][2][-40:]
                    
                    if to_address.lower() == affiliate_address.lower():
                        amount = int(log['data'], 16)
                        from_address = '0x' + log['topics'][1][-40:].hex() if hasattr(log['topics'][1], 'hex') else '0x' + log['topics'][1][-40:]
                        
                        cursor.execute('''
                            INSERT INTO affiliate_transfers 
                            (tx_hash, block_number, token_address, from_address, to_address, amount, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (tx_hash, log['blockNumber'], log['address'], from_address, to_address, str(amount), timestamp))
                        
                        logger.info(f"Found affiliate transfer: {amount} tokens to {to_address}")
                
            except Exception as e:
                logger.error(f"Error processing log: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error fetching events for blocks {start_block}-{end_block}: {e}")
    
    conn.close()

def main():
    """Main function to run the fixed affiliate fee listener"""
    logger.info("Starting ShapeShift affiliate fee tracker (fixed)")
    
    # Setup database
    setup_database()
    
    # Process each chain
    for chain_id in AFFILIATE_CONTRACTS.keys():
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block ranges for the last week
            block_ranges = get_block_range_for_week(chain_id)
            
            # Process each block range
            for start_block, end_block in block_ranges:
                logger.info(f"Processing blocks {start_block} to {end_block} on chain {chain_id}")
                
                # Fetch all contract events
                fetch_all_contract_events(chain_id, start_block, end_block)
                
                # Small delay to avoid overwhelming RPC
                time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    logger.info("Fixed affiliate fee listener run complete!")
    
    # Print summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM cowswap_events")
    cowswap_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM zerox_events")
    zerox_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM affiliate_transfers")
    affiliate_count = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"Fixed Affiliate Fee Summary:")
    logger.info(f"  CowSwap events: {cowswap_count}")
    logger.info(f"  0x events: {zerox_count}")
    logger.info(f"  Affiliate transfers: {affiliate_count}")
    logger.info(f"  Total events: {cowswap_count + zerox_count + affiliate_count}")

if __name__ == "__main__":
    main() 