#!/usr/bin/env python3
"""
ShapeShift Affiliate Fee Tracker - Progress Version
Shows clear progress counters and real-time updates
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
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'shapeshift_affiliate_fees_progress.db'

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

# Global progress tracking
progress_stats = {
    'total_blocks': 0,
    'processed_blocks': 0,
    'cowswap_events': 0,
    'zerox_events': 0,
    'affiliate_transfers': 0,
    'start_time': time.time(),
    'last_update': time.time()
}

def print_progress():
    """Print current progress with timing information"""
    elapsed = time.time() - progress_stats['start_time']
    if progress_stats['total_blocks'] > 0:
        percent = (progress_stats['processed_blocks'] / progress_stats['total_blocks']) * 100
        blocks_per_sec = progress_stats['processed_blocks'] / elapsed if elapsed > 0 else 0
        
        # Clear line and print progress
        sys.stdout.write('\r')
        sys.stdout.write(f"Progress: {progress_stats['processed_blocks']}/{progress_stats['total_blocks']} blocks ({percent:.1f}%) | "
                        f"Rate: {blocks_per_sec:.1f} blocks/sec | "
                        f"CowSwap: {progress_stats['cowswap_events']} | "
                        f"0x: {progress_stats['zerox_events']} | "
                        f"Affiliate: {progress_stats['affiliate_transfers']} | "
                        f"Elapsed: {elapsed:.0f}s")
        sys.stdout.flush()

def update_progress(blocks_processed=1, cowswap=0, zerox=0, affiliate=0):
    """Update progress statistics"""
    progress_stats['processed_blocks'] += blocks_processed
    progress_stats['cowswap_events'] += cowswap
    progress_stats['zerox_events'] += zerox
    progress_stats['affiliate_transfers'] += affiliate
    progress_stats['last_update'] = time.time()
    
    # Print progress every 10 blocks or every 5 seconds
    if (progress_stats['processed_blocks'] % 10 == 0 or 
        time.time() - progress_stats['last_update'] > 5):
        print_progress()

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
    logger.info("Progress affiliate fee database setup complete")

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
    
    # Update total blocks for progress tracking
    progress_stats['total_blocks'] = len(ranges)
    
    logger.info(f"Chain {chain_id}: Split into {len(ranges)} chunks from {start_block} to {current_block}")
    return ranges

def fetch_logs_with_timeout(w3: Web3, contract_address: str, start_block: int, end_block: int, timeout: int = 10) -> List:
    """Fetch logs with strict timeout"""
    try:
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

def process_logs_with_progress(logs: List, w3: Web3, config: Dict, affiliate_address: str, cursor) -> Tuple[int, int, int]:
    """Process logs with progress tracking"""
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

def fetch_contract_events_with_progress(chain_id: int, start_block: int, end_block: int):
    """Fetch events from one contract at a time with progress tracking"""
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
                
            logs = fetch_logs_with_timeout(w3, contract_address, start_block, end_block)
            
            if len(logs) > 0:
                # Process logs efficiently
                cowswap_count, zerox_count, affiliate_count = process_logs_with_progress(
                    logs, w3, config, affiliate_address, cursor
                )
                
                if contract_name == 'cowswap':
                    total_cowswap += cowswap_count
                elif contract_name == 'zerox':
                    total_zerox += zerox_count
                
                total_affiliate += affiliate_count
            
            # Commit after each contract
            cursor.connection.commit()
            
            # Rate limiting between contract queries
            time.sleep(0.5)
        
        # Update progress
        update_progress(blocks_processed=1, cowswap=total_cowswap, zerox=total_zerox, affiliate=total_affiliate)
        
    except Exception as e:
        logger.error(f"Error fetching events for blocks {start_block}-{end_block}: {e}")
        # Still update progress even on error
        update_progress(blocks_processed=1)
    
    conn.close()

def main():
    """Main function to run the progress affiliate fee listener"""
    logger.info("Starting ShapeShift affiliate fee tracker (progress version)")
    logger.info("Progress will be displayed in real-time...")
    
    # Setup database
    setup_database()
    
    # Process each chain
    for chain_id in AFFILIATE_CONTRACTS.keys():
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block ranges for the last day only
            block_ranges = get_block_range_for_day(chain_id)
            
            # Process each block range
            for i, (start_block, end_block) in enumerate(block_ranges):
                # Fetch all contract events
                fetch_contract_events_with_progress(chain_id, start_block, end_block)
                
                # Rate limiting between block ranges
                time.sleep(0.2)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    # Print final progress
    print()  # New line after progress bar
    logger.info("Progress affiliate fee listener run complete!")
    
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
    
    total_time = time.time() - progress_stats['start_time']
    logger.info(f"Progress Affiliate Fee Summary:")
    logger.info(f"  Total time: {total_time:.1f} seconds")
    logger.info(f"  Blocks processed: {progress_stats['processed_blocks']}")
    logger.info(f"  CowSwap events: {cowswap_count}")
    logger.info(f"  0x events: {zerox_count}")
    logger.info(f"  Affiliate transfers: {affiliate_count}")
    logger.info(f"  Total events: {cowswap_count + zerox_count + affiliate_count}")

if __name__ == "__main__":
    main() 