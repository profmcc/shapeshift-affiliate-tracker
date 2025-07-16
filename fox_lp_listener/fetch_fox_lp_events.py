#!/usr/bin/env python3
"""
ShapeShift FOX LP Event Fetcher
Fetches actual LP events from the last 7 days for all FOX pools.
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
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'fox_pools_analysis.db'

# FOX token address
FOX_TOKEN = '0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d'

# All FOX pools with their details and RPC endpoints
FOX_POOLS = {
    # Arbitrum
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'pools': [
            {
                'address': '0x5f6ce0ca13b87bd738519545d3e018e70e339c24',
                'name': 'WETH/FOX V2',
                'type': 'uniswap_v2',
                'chain_id': 42161
            },
            {
                'address': '0x76d4d1eaa0c4b3645e75c46e573c1d4f75e9041e',
                'name': 'WETH/FOX V3',
                'type': 'uniswap_v3',
                'chain_id': 42161
            }
        ]
    },
    # Ethereum
    'ethereum': {
        'rpc': 'https://eth.llamarpc.com',
        'pools': [
            {
                'address': '0xad0e10df5dcdf21396b9d64715aadaf543f8b376',
                'name': 'GIV/FOX',
                'type': 'uniswap_v2',
                'chain_id': 1
            },
            {
                'address': '0x470e8de2ebaef52014a47cb5e6af86884947f08c',
                'name': 'WETH/FOX',
                'type': 'uniswap_v3',
                'chain_id': 1
            }
        ]
    },
    # Gnosis
    'gnosis': {
        'rpc': 'https://rpc.gnosischain.com',
        'pools': [
            {
                'address': '0x75594f01da2e4231e16e67f841c307c4df2313d1',
                'name': 'GIV/FOX',
                'type': 'uniswap_v2',
                'chain_id': 100
            },
            {
                'address': '0xc22313fd39f7d4d73a89558f9e8e444c86464bac',
                'name': 'wxDAI/FOX',
                'type': 'uniswap_v2',
                'chain_id': 100
            },
            {
                'address': '0x8a0bee989c591142414ad67fb604539d917889df',
                'name': 'HNY/FOX',
                'type': 'uniswap_v2',
                'chain_id': 100
            }
        ]
    },
    # Polygon
    'polygon': {
        'rpc': 'https://polygon-rpc.com',
        'pools': [
            {
                'address': '0x93ef615f1ddd27d0e141ad7192623a5c45e8f200',
                'name': 'WETH/FOX',
                'type': 'uniswap_v3',
                'chain_id': 137
            }
        ]
    }
}

# Event signatures for different pool types
EVENT_SIGNATURES = {
    'uniswap_v2': {
        'sync': '0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1',
        'mint': '0x4c209b5fc8ad21358ac9a3b7e4b8b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b',
        'burn': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    },
    'uniswap_v3': {
        'increase_liquidity': '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f',
        'decrease_liquidity': '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4',
        'collect': '0x40d0efd1a53d60ecbf40971b9d9e18502887ace780a0564668d6d65605f3c5de'
    }
}

def setup_events_table():
    """Create table for storing LP events"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # FOX LP events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fox_lp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_name TEXT,
            pool_address TEXT,
            pool_name TEXT,
            event_type TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            owner TEXT,
            tick_lower INTEGER,
            tick_upper INTEGER,
            amount TEXT,
            amount0 TEXT,
            amount1 TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("FOX LP events table setup complete")

def get_web3_connection(rpc_url: str) -> Web3:
    """Get Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        w3.eth.block_number  # Test connection
        logger.info(f"Connected to {rpc_url}")
        return w3
    except Exception as e:
        logger.error(f"Failed to connect to {rpc_url}: {e}")
        raise

def get_block_range_for_days(w3: Web3, days: int) -> Tuple[int, int]:
    """Get block range for specific number of days"""
    current_block = w3.eth.block_number
    blocks_per_day = 7200  # Approximate for most chains
    blocks_for_period = blocks_per_day * days
    start_block = max(0, current_block - blocks_for_period)
    
    logger.info(f"Blocks {start_block} to {current_block} ({days} days)")
    return start_block, current_block

def fetch_pool_events(chain_name: str, pool: Dict, start_block: int, end_block: int):
    """Fetch LP events for a specific pool"""
    w3 = get_web3_connection(FOX_POOLS[chain_name]['rpc'])
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    pool_address = pool['address']
    pool_name = pool['name']
    pool_type = pool['type']
    
    logger.info(f"Fetching {pool_type} events for {pool_name} on {chain_name}")
    
    chunk_size = 1000
    total_events = 0
    
    current_block = start_block
    while current_block < end_block:
        chunk_end = min(current_block + chunk_size - 1, end_block)
        
        try:
            if pool_type == 'uniswap_v3':
                # Fetch V3 events
                events_to_fetch = ['increase_liquidity', 'decrease_liquidity']
                
                for event_type in events_to_fetch:
                    logs = w3.eth.get_logs({
                        'address': pool_address,
                        'topics': [EVENT_SIGNATURES['uniswap_v3'][event_type]],
                        'fromBlock': current_block,
                        'toBlock': chunk_end
                    })
                    
                    for log in logs:
                        try:
                            decoded = decode(
                                ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                                bytes.fromhex(log['data'][2:])
                            )
                            
                            owner = '0x' + log['topics'][1][-40:].hex()
                            tick_lower = int.from_bytes(log['topics'][2][-3:], 'big', signed=True)
                            tick_upper = int.from_bytes(log['topics'][3][-3:], 'big', signed=True)
                            
                            cursor.execute('''
                                INSERT INTO fox_lp_events 
                                (chain_name, pool_address, pool_name, event_type, block_number, tx_hash,
                                 owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                chain_name, pool_address, pool_name, event_type, log['blockNumber'], 
                                log['transactionHash'].hex(), owner, tick_lower, tick_upper,
                                str(decoded[3]), str(decoded[4]), str(decoded[5]), int(time.time())
                            ))
                            
                            total_events += 1
                            
                        except Exception as e:
                            logger.warning(f"Error decoding event: {e}")
                            continue
            
            elif pool_type == 'uniswap_v2':
                # Fetch V2 events (mint/burn for LP activity)
                events_to_fetch = ['mint', 'burn']
                
                for event_type in events_to_fetch:
                    logs = w3.eth.get_logs({
                        'address': pool_address,
                        'topics': [EVENT_SIGNATURES['uniswap_v2'][event_type]],
                        'fromBlock': current_block,
                        'toBlock': chunk_end
                    })
                    
                    for log in logs:
                        try:
                            # For V2, we'll store basic info since decoding is more complex
                            owner = '0x' + log['topics'][1][-40:].hex() if len(log['topics']) > 1 else 'unknown'
                            
                            cursor.execute('''
                                INSERT INTO fox_lp_events 
                                (chain_name, pool_address, pool_name, event_type, block_number, tx_hash,
                                 owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                chain_name, pool_address, pool_name, event_type, log['blockNumber'], 
                                log['transactionHash'].hex(), owner, 0, 0, '0', '0', '0', int(time.time())
                            ))
                            
                            total_events += 1
                            
                        except Exception as e:
                            logger.warning(f"Error processing V2 event: {e}")
                            continue
            
            if total_events > 0 and total_events % 10 == 0:
                logger.info(f"Processed {total_events} events so far...")
                
        except Exception as e:
            logger.error(f"Error processing blocks {current_block}-{chunk_end}: {e}")
        
        current_block = chunk_end + 1
        time.sleep(0.1)  # Rate limiting
    
    conn.commit()
    conn.close()
    logger.info(f"Total events for {pool_name}: {total_events}")

def update_activity_analysis():
    """Update the activity analysis with real event data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing activity data
    cursor.execute('DELETE FROM fox_lp_activity')
    
    periods = [
        (3, "3_days"),
        (7, "7_days"),
        (14, "14_days"),
        (30, "30_days")
    ]
    
    for days, period_name in periods:
        logger.info(f"Creating activity analysis for {period_name}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all pools from the summary table
        cursor.execute('''
            SELECT DISTINCT chain_name, pool_address, pool_name
            FROM fox_pool_summary
        ''')
        
        pools = cursor.fetchall()
        
        for chain_name, pool_address, pool_name in pools:
            # Get adds in period
            cursor.execute('''
                SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_adds,
                       COUNT(DISTINCT owner) as unique_lps
                FROM fox_lp_events
                WHERE chain_name = ? AND pool_address = ? AND event_type = 'increase_liquidity'
                AND timestamp >= ?
            ''', (chain_name, pool_address, int(start_date.timestamp())))
            
            adds_result = cursor.fetchone()
            total_adds, unique_lps = adds_result
            
            # Get removes in period
            cursor.execute('''
                SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_removes
                FROM fox_lp_events
                WHERE chain_name = ? AND pool_address = ? AND event_type = 'decrease_liquidity'
                AND timestamp >= ?
            ''', (chain_name, pool_address, int(start_date.timestamp())))
            
            total_removes = cursor.fetchone()[0]
            net_change = total_adds - total_removes
            
            # Insert analysis
            cursor.execute('''
                INSERT INTO fox_lp_activity
                (chain_name, pool_address, pool_name, period, total_adds, total_removes,
                 net_change, unique_lps, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (chain_name, pool_address, pool_name, period_name,
                  total_adds, total_removes, net_change, unique_lps,
                  start_date.isoformat(), end_date.isoformat()))
    
    conn.commit()
    conn.close()
    logger.info("Activity analysis updated with real event data")

def display_updated_results():
    """Display the updated FOX LP analysis results"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*100)
    print("FOX LP EVENTS SUMMARY (Last 7 Days)")
    print("="*100)
    
    # Event summary
    df_events = pd.read_sql_query('''
        SELECT chain_name, pool_name, event_type, COUNT(*) as event_count,
               COUNT(DISTINCT owner) as unique_lps
        FROM fox_lp_events
        GROUP BY chain_name, pool_name, event_type
        ORDER BY chain_name, pool_name, event_type
    ''', conn)
    
    if not df_events.empty:
        print(df_events.to_string(index=False))
    else:
        print("No FOX LP events found in the last 7 days")
    
    print("\n" + "="*100)
    print("FOX LP ACTIVITY ANALYSIS (Last 7 Days)")
    print("="*100)
    
    # Activity analysis
    df_activity = pd.read_sql_query('''
        SELECT chain_name, pool_name, period, total_adds, total_removes, net_change, unique_lps
        FROM fox_lp_activity
        WHERE period = '7_days'
        ORDER BY chain_name, pool_name
    ''', conn)
    
    if not df_activity.empty:
        print(df_activity.to_string(index=False, float_format='%.2f'))
    else:
        print("No activity data available")
    
    # Total events
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM fox_lp_events')
    total_events = cursor.fetchone()[0]
    
    print(f"\nTotal FOX LP Events Found: {total_events}")
    
    conn.close()

def main():
    """Main function to fetch FOX LP events"""
    logger.info("Starting FOX LP event fetcher")
    
    setup_events_table()
    
    # Fetch events for last 7 days
    for chain_name, chain_data in FOX_POOLS.items():
        logger.info(f"Processing {chain_name}")
        
        try:
            w3 = get_web3_connection(chain_data['rpc'])
            start_block, end_block = get_block_range_for_days(w3, 7)
            
            for pool in chain_data['pools']:
                fetch_pool_events(chain_name, pool, start_block, end_block)
                
        except Exception as e:
            logger.error(f"Error processing {chain_name}: {e}")
    
    # Update activity analysis
    update_activity_analysis()
    
    # Display results
    display_updated_results()
    
    logger.info("FOX LP event fetching complete!")

if __name__ == "__main__":
    main() 