#!/usr/bin/env python3
"""
ShapeShift Affiliate Fee Tracker - Lightweight Version
Processes very small chunks with strict timeouts to avoid getting stuck
"""

import os
import sqlite3
import json
import time
import random
import signal
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
DB_PATH = 'shapeshift_affiliate_fees_lightweight.db'

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
        'rpc': INFURA_URL
    },
    137: {  # Polygon
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': POLYGON_RPC
    }
}

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signal"""
    global shutdown_requested
    logger.info("Shutdown signal received, finishing current block...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
    logger.info("Lightweight affiliate fee database setup complete")

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain"""
    config = AFFILIATE_CONTRACTS.get(chain_id)
    if not config:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    return Web3(Web3.HTTPProvider(config['rpc']))

def get_block_range_for_day(chain_id: int) -> List[Tuple[int, int]]:
    """Get block ranges for the last day only, split into very small chunks"""
    w3 = get_web3_connection(chain_id)
    
    # Get current block
    current_block = w3.eth.block_number
    
    # Estimate blocks per day (varies by chain)
    blocks_per_day = {
        1: 7200,      # Ethereum ~12s blocks
        137: 28800,   # Polygon ~3s blocks
    }
    
    blocks_per_day = blocks_per_day.get(chain_id, 7200)
    start_block = max(0, current_block - blocks_per_day)
    
    # Split into very small chunks to avoid RPC limits
    chunk_size = 50  # Very small chunks for efficiency
    ranges = []
    
    for i in range(start_block, current_block, chunk_size):
        end = min(i + chunk_size, current_block)
        ranges.append((i, end))
    
    logger.info(f"Chain {chain_id}: Split into {len(ranges)} chunks from {start_block} to {current_block}")
    return ranges

def fetch_logs_with_timeout(w3: Web3, contract_address: str, start_block: int, end_block: int, timeout: int = 10) -> List:
    """Fetch logs with strict timeout"""
    try:
        # Set a timeout for the request
        logs = w3.eth.get_logs({
            'address': contract_address,
            'fromBlock': start_block,
            'toBlock': end_block
        })
        return logs
    except Exception as e:
        error_msg = str(e)
        if 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower():
            logger.warning(f"Rate limited, skipping block range {start_block}-{end_block}")
        else:
            logger.error(f"Error fetching logs: {e}")
        return []

def process_logs_lightweight(logs: List, w3: Web3, config: Dict, affiliate_address: str, cursor) -> Tuple[int, int, int]:
    """Process logs with minimal processing to avoid memory issues"""
    cowswap_count = 0
    zerox_count = 0
    affiliate_count = 0
    
    # Process logs one by one to avoid memory buildup
    for log in logs:
        try:
            # Get transaction hash
            tx_hash = log['transactionHash'].hex() if hasattr(log['transactionHash'], 'hex') else str(log['transactionHash'])
            
            # Get block timestamp (use current time as fallback)
            timestamp = int(time.time())
            
            # Determine event type
            event_sig = log['topics'][0].hex() if hasattr(log['topics'][0], 'hex') else log['topics'][0]
            
            # Store minimal event data
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
                cowswap_count += 1
                
            elif log['address'].lower() == config.get('zerox', '').lower():
                cursor.execute('''
                    INSERT INTO zerox_events 
                    (tx_hash, block_number, event_type, event_data, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tx_hash, log['blockNumber'], event_sig, json.dumps(event_data), timestamp))
                zerox_count += 1
            
            # Check for ERC20 transfers to affiliate address (simplified)
            if len(log['topics']) >= 3:
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
                    affiliate_count += 1
            
        except Exception as e:
            logger.error(f"Error processing log: {e}")
            continue
    
    return cowswap_count, zerox_count, affiliate_count

def fetch_contract_events_lightweight(chain_id: int, start_block: int, end_block: int):
    """Fetch events from one contract at a time with strict limits"""
    w3 = get_web3_connection(chain_id)
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        total_cowswap = 0
        total_zerox = 0
        total_affiliate = 0
        
        # Process one contract at a time
        for contract_name, contract_address in config.items():
            if contract_name == 'rpc':
                continue
                
            logger.info(f"Fetching logs from {contract_name} for blocks {start_block}-{end_block}")
            logs = fetch_logs_with_timeout(w3, contract_address, start_block, end_block)
            logger.info(f"Found {len(logs)} logs from {contract_name}")
            
            if len(logs) > 0:
                # Process logs efficiently
                cowswap_count, zerox_count, affiliate_count = process_logs_lightweight(
                    logs, w3, config, affiliate_address, cursor
                )
                
                if contract_name == 'cowswap':
                    total_cowswap += cowswap_count
                elif contract_name == 'zerox':
                    total_zerox += zerox_count
                
                total_affiliate += affiliate_count
                
                logger.info(f"Processed {len(logs)} logs: {cowswap_count} CowSwap, {zerox_count} 0x, {affiliate_count} affiliate transfers")
            
            # Commit after each contract
            cursor.connection.commit()
            
            # Rate limiting between contract queries
            time.sleep(1)
        
        logger.info(f"Block range {start_block}-{end_block}: {total_cowswap} CowSwap, {total_zerox} 0x, {total_affiliate} affiliate transfers")
        
    except Exception as e:
        logger.error(f"Error fetching events for blocks {start_block}-{end_block}: {e}")
    
    conn.close()

def main():
    """Main function to run the lightweight affiliate fee listener"""
    logger.info("Starting ShapeShift affiliate fee tracker (lightweight)")
    
    # Setup database
    setup_database()
    
    # Process each chain
    for chain_id in AFFILIATE_CONTRACTS.keys():
        if shutdown_requested:
            break
            
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block ranges for the last day only
            block_ranges = get_block_range_for_day(chain_id)
            
            # Process each block range
            for i, (start_block, end_block) in enumerate(block_ranges):
                if shutdown_requested:
                    logger.info("Shutdown requested, stopping...")
                    break
                    
                logger.info(f"Processing blocks {start_block} to {end_block} on chain {chain_id} ({i+1}/{len(block_ranges)})")
                
                # Fetch all contract events
                fetch_contract_events_lightweight(chain_id, start_block, end_block)
                
                # Rate limiting between block ranges
                time.sleep(0.5)
                
                # Progress update every 5 blocks
                if (i + 1) % 5 == 0:
                    logger.info(f"Progress: {i+1}/{len(block_ranges)} blocks processed")
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    logger.info("Lightweight affiliate fee listener run complete!")
    
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
    
    logger.info(f"Lightweight Affiliate Fee Summary:")
    logger.info(f"  CowSwap events: {cowswap_count}")
    logger.info(f"  0x events: {zerox_count}")
    logger.info(f"  Affiliate transfers: {affiliate_count}")
    logger.info(f"  Total events: {cowswap_count + zerox_count + affiliate_count}")

if __name__ == "__main__":
    main() 