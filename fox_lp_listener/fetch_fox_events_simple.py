#!/usr/bin/env python3
"""
ShapeShift FOX LP Event Fetcher - Simplified
Fetches actual LP events from the last 7 days for the most active FOX pools.
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

# Focus on the most active FOX pools with proper checksum addresses
ACTIVE_FOX_POOLS = [
    {
        'chain_name': 'ethereum',
        'pool_address': Web3.to_checksum_address('0x470e8de2ebaef52014a47cb5e6af86884947f08c'),
        'pool_name': 'WETH/FOX',
        'type': 'uniswap_v3',
        'rpc': 'https://eth.llamarpc.com',
        'total_usd': 3060022.47229936,
        'fox_balance': 67483795.582372
    },
    {
        'chain_name': 'arbitrum',
        'pool_address': Web3.to_checksum_address('0x5f6ce0ca13b87bd738519545d3e018e70e339c24'),
        'pool_name': 'WETH/FOX V2',
        'type': 'uniswap_v2',
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'total_usd': 117966.027662768,
        'fox_balance': 2674852.29310537
    },
    {
        'chain_name': 'polygon',
        'pool_address': Web3.to_checksum_address('0x93ef615f1ddd27d0e141ad7192623a5c45e8f200'),
        'pool_name': 'WETH/FOX',
        'type': 'uniswap_v3',
        'rpc': 'https://polygon-rpc.com',
        'total_usd': 83484.628841133,
        'fox_balance': 1815610.43843394
    }
]

# Event signatures
EVENT_SIGNATURES = {
    'uniswap_v3': {
        'increase_liquidity': '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f',
        'decrease_liquidity': '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4'
    },
    'uniswap_v2': {
        'mint': '0x4c209b5fc8ad21358ac9a3b7e4b8b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b',
        'burn': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
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
            amount TEXT,
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

def fetch_pool_events(pool: Dict, start_block: int, end_block: int):
    """Fetch LP events for a specific pool"""
    w3 = get_web3_connection(pool['rpc'])
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    pool_address = pool['pool_address']
    pool_name = pool['pool_name']
    pool_type = pool['type']
    chain_name = pool['chain_name']
    
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
                            amount = str(decoded[3])  # liquidity amount
                            
                            cursor.execute('''
                                INSERT INTO fox_lp_events 
                                (chain_name, pool_address, pool_name, event_type, block_number, tx_hash,
                                 owner, amount, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                chain_name, pool_address, pool_name, event_type, log['blockNumber'], 
                                log['transactionHash'].hex(), owner, amount, int(time.time())
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
                            # For V2, we'll store basic info
                            owner = '0x' + log['topics'][1][-40:].hex() if len(log['topics']) > 1 else 'unknown'
                            
                            cursor.execute('''
                                INSERT INTO fox_lp_events 
                                (chain_name, pool_address, pool_name, event_type, block_number, tx_hash,
                                 owner, amount, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                chain_name, pool_address, pool_name, event_type, log['blockNumber'], 
                                log['transactionHash'].hex(), owner, '0', int(time.time())
                            ))
                            
                            total_events += 1
                            
                        except Exception as e:
                            logger.warning(f"Error processing V2 event: {e}")
                            continue
            
            if total_events > 0 and total_events % 5 == 0:
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
        
        for pool in ACTIVE_FOX_POOLS:
            chain_name = pool['chain_name']
            pool_address = pool['pool_address']
            pool_name = pool['pool_name']
            
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

def display_results():
    """Display the FOX LP analysis results"""
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
    
    # Pool summary
    print("\n" + "="*100)
    print("ACTIVE FOX POOLS SUMMARY")
    print("="*100)
    
    for pool in ACTIVE_FOX_POOLS:
        print(f"{pool['chain_name'].upper()}: {pool['pool_name']}")
        print(f"  Address: {pool['pool_address']}")
        print(f"  Total USD: ${pool['total_usd']:,.2f}")
        print(f"  FOX Balance: {pool['fox_balance']:,.2f} FOX")
        print()
    
    conn.close()

def main():
    """Main function to fetch FOX LP events"""
    logger.info("Starting FOX LP event fetcher (simplified)")
    
    setup_events_table()
    
    # Fetch events for last 7 days for each pool
    for pool in ACTIVE_FOX_POOLS:
        try:
            w3 = get_web3_connection(pool['rpc'])
            start_block, end_block = get_block_range_for_days(w3, 7)
            fetch_pool_events(pool, start_block, end_block)
            
        except Exception as e:
            logger.error(f"Error processing {pool['pool_name']}: {e}")
    
    # Update activity analysis
    update_activity_analysis()
    
    # Display results
    display_results()
    
    logger.info("FOX LP event fetching complete!")

if __name__ == "__main__":
    main() 