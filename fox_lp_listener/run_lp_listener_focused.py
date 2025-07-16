#!/usr/bin/env python3
"""
ShapeShift FOX LP Position Tracker - Focused Listener
Fetches FOX token liquidity events from the last 7 days for specific pools.
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
DB_PATH = 'fox_lp_positions.db'

# RPC endpoint
RPC_ENDPOINT = 'https://eth.llamarpc.com'

# FOX token address
FOX_TOKEN = '0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d'

# Focus on specific FOX pools
FOX_POOLS = {
    1: [  # Ethereum
        ('0x470e8de2eBaef52014A47Cb5E6aF86884947F08c', 'WETH/FOX LP Pool'),
        # Add more FOX pools here if needed
    ]
}

# Event signatures for Uniswap V3 LP events
LP_EVENT_SIGNATURES = {
    'increase_liquidity': '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f',
    'decrease_liquidity': '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4',
    'collect': '0x40d0efd1a53d60ecbf40971b9d9e18502887ace780a0564668d6d65605f3c5de'
}

def setup_database():
    """Create the database and tables for FOX LP tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # FOX LP events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fox_lp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # FOX LP activity summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fox_lp_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT,
            total_adds TEXT,
            total_removes TEXT,
            net_change TEXT,
            unique_lps INTEGER,
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("FOX LP database setup complete")

def get_web3_connection() -> Web3:
    """Get Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
        w3.eth.block_number  # Test connection
        logger.info(f"Connected to {RPC_ENDPOINT}")
        return w3
    except Exception as e:
        logger.error(f"Failed to connect to {RPC_ENDPOINT}: {e}")
        raise

def get_block_range_for_days(days: int) -> Tuple[int, int]:
    """Get block range for specific number of days"""
    w3 = get_web3_connection()
    
    current_block = w3.eth.block_number
    blocks_per_day = 7200  # Ethereum ~12s blocks
    blocks_for_period = blocks_per_day * days
    start_block = max(0, current_block - blocks_for_period)
    
    logger.info(f"Blocks {start_block} to {current_block} ({days} days)")
    return start_block, current_block

def fetch_fox_lp_events(start_block: int, end_block: int):
    """Fetch FOX LP events in chunks"""
    w3 = get_web3_connection()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    chunk_size = 1000
    total_events = 0
    
    for pool_address, pool_name in FOX_POOLS[1]:
        logger.info(f"Fetching FOX LP events for {pool_name}")
        
        current_block = start_block
        while current_block < end_block:
            chunk_end = min(current_block + chunk_size - 1, end_block)
            
            try:
                # Fetch increase liquidity events
                increase_logs = w3.eth.get_logs({
                    'address': pool_address,
                    'topics': [LP_EVENT_SIGNATURES['increase_liquidity']],
                    'fromBlock': current_block,
                    'toBlock': chunk_end
                })
                
                for log in increase_logs:
                    decoded = decode(
                        ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                        bytes.fromhex(log['data'][2:])
                    )
                    
                    owner = '0x' + log['topics'][1][-40:].hex()
                    tick_lower = int.from_bytes(log['topics'][2][-3:], 'big', signed=True)
                    tick_upper = int.from_bytes(log['topics'][3][-3:], 'big', signed=True)
                    
                    cursor.execute('''
                        INSERT INTO fox_lp_events 
                        (pool_address, pool_name, event_type, block_number, tx_hash,
                         owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pool_address, pool_name, 'increase', log['blockNumber'], 
                        log['transactionHash'].hex(), owner, tick_lower, tick_upper,
                        str(decoded[3]), str(decoded[4]), str(decoded[5]), int(time.time())
                    ))
                
                # Fetch decrease liquidity events
                decrease_logs = w3.eth.get_logs({
                    'address': pool_address,
                    'topics': [LP_EVENT_SIGNATURES['decrease_liquidity']],
                    'fromBlock': current_block,
                    'toBlock': chunk_end
                })
                
                for log in decrease_logs:
                    decoded = decode(
                        ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                        bytes.fromhex(log['data'][2:])
                    )
                    
                    owner = '0x' + log['topics'][1][-40:].hex()
                    tick_lower = int.from_bytes(log['topics'][2][-3:], 'big', signed=True)
                    tick_upper = int.from_bytes(log['topics'][3][-3:], 'big', signed=True)
                    
                    cursor.execute('''
                        INSERT INTO fox_lp_events 
                        (pool_address, pool_name, event_type, block_number, tx_hash,
                         owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pool_address, pool_name, 'decrease', log['blockNumber'], 
                        log['transactionHash'].hex(), owner, tick_lower, tick_upper,
                        str(decoded[3]), str(decoded[4]), str(decoded[5]), int(time.time())
                    ))
                
                events_in_chunk = len(increase_logs) + len(decrease_logs)
                total_events += events_in_chunk
                
                if events_in_chunk > 0:
                    logger.info(f"Blocks {current_block}-{chunk_end}: {events_in_chunk} events")
                
            except Exception as e:
                logger.error(f"Error processing blocks {current_block}-{chunk_end}: {e}")
            
            current_block = chunk_end + 1
            time.sleep(0.1)  # Rate limiting
    
    conn.commit()
    conn.close()
    logger.info(f"Total FOX LP events: {total_events}")

def create_activity_summary():
    """Create activity summary for different time periods"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    periods = [
        (3, "3_days"),
        (7, "7_days"),
        (14, "14_days"),
        (30, "30_days")
    ]
    
    for days, period_name in periods:
        logger.info(f"Creating summary for {period_name}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get adds in period
        cursor.execute('''
            SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_adds,
                   COUNT(DISTINCT owner) as unique_lps
            FROM fox_lp_events
            WHERE event_type = 'increase' AND timestamp >= ?
        ''', (int(start_date.timestamp()),))
        
        adds_result = cursor.fetchone()
        total_adds, unique_lps = adds_result
        
        # Get removes in period
        cursor.execute('''
            SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_removes
            FROM fox_lp_events
            WHERE event_type = 'decrease' AND timestamp >= ?
        ''', (int(start_date.timestamp()),))
        
        total_removes = cursor.fetchone()[0]
        net_change = total_adds - total_removes
        
        # Insert summary
        cursor.execute('''
            INSERT OR REPLACE INTO fox_lp_summary
            (period, total_adds, total_removes, net_change, unique_lps, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (period_name, str(total_adds), str(total_removes), str(net_change),
              unique_lps, start_date.isoformat(), end_date.isoformat()))
    
    conn.commit()
    conn.close()

def display_results():
    """Display the FOX LP analysis results"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*80)
    print("FOX LP ACTIVITY SUMMARY")
    print("="*80)
    
    # Activity summary
    df_summary = pd.read_sql_query('''
        SELECT period, total_adds, total_removes, net_change, unique_lps
        FROM fox_lp_summary
        ORDER BY period
    ''', conn)
    
    if not df_summary.empty:
        print(df_summary.to_string(index=False))
    else:
        print("No FOX LP activity data available")
    
    print("\n" + "="*80)
    print("FOX LP EVENTS DETAIL")
    print("="*80)
    
    # Event details
    df_events = pd.read_sql_query('''
        SELECT pool_name, event_type, COUNT(*) as event_count, 
               COUNT(DISTINCT owner) as unique_lps
        FROM fox_lp_events
        GROUP BY pool_name, event_type
        ORDER BY pool_name, event_type
    ''', conn)
    
    if not df_events.empty:
        print(df_events.to_string(index=False))
    else:
        print("No FOX LP events found")
    
    conn.close()

def main():
    """Main function to run the focused FOX LP listener"""
    logger.info("Starting FOX LP position tracker")
    
    setup_database()
    
    try:
        # Get block range for last 7 days
        start_block, end_block = get_block_range_for_days(7)
        
        # Fetch FOX LP events
        fetch_fox_lp_events(start_block, end_block)
        
        # Create activity summary
        create_activity_summary()
        
        # Display results
        display_results()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    
    logger.info("FOX LP position listener run complete!")

if __name__ == "__main__":
    main() 