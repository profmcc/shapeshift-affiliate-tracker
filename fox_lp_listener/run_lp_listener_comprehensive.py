#!/usr/bin/env python3
"""
ShapeShift LP Position Tracker - Comprehensive Listener
Fetches all liquidity position events and creates analysis tables for different time periods.
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
DB_PATH = 'shapeshift_lp_positions.db'

# Multiple RPC endpoints for redundancy
RPC_ENDPOINTS = {
    1: [  # Ethereum
        'https://eth.llamarpc.com',
        'https://rpc.ankr.com/eth',
        'https://cloudflare-eth.com',
        'https://ethereum.publicnode.com'
    ]
}

# LP tracking contract configurations (focusing on major pools)
LP_CONTRACTS = {
    1: {  # Ethereum
        'uniswap_v3_pools': [
            ('0x470e8de2eBaef52014A47Cb5E6aF86884947F08c', 'WETH/FOX LP Pool'),
            ('0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640', 'WETH/USDC V3'),
            ('0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36', 'WETH/USDT V3'),
            ('0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8', 'WETH/USDC V3 0.3%'),
        ]
    }
}

# Event signatures for Uniswap V3 LP events
LP_EVENT_SIGNATURES = {
    'increase_liquidity': '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f',
    'decrease_liquidity': '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4',
    'collect': '0x40d0efd1a53d60ecbf40971b9d9e18502887ace780a0564668d6d65605f3c5de'
}

def setup_database():
    """Create the database and tables for LP position tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Uniswap V3 IncreaseLiquidity events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS increase_liquidity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            pool_address TEXT,
            pool_name TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
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
    
    # Uniswap V3 DecreaseLiquidity events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decrease_liquidity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            pool_address TEXT,
            pool_name TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
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
    
    # Uniswap V3 Collect events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collect_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            pool_address TEXT,
            pool_name TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
            sender TEXT,
            recipient TEXT,
            amount0 TEXT,
            amount1 TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # LP position summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lp_position_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_address TEXT,
            pool_name TEXT,
            owner TEXT,
            tick_lower INTEGER,
            tick_upper INTEGER,
            total_liquidity TEXT,
            total_amount0 TEXT,
            total_amount1 TEXT,
            last_updated TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # LP activity analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lp_activity_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_address TEXT,
            pool_name TEXT,
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
    
    # LP pool balances table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lp_pool_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_address TEXT,
            pool_name TEXT,
            total_liquidity TEXT,
            total_amount0 TEXT,
            total_amount1 TEXT,
            unique_positions INTEGER,
            last_updated TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("LP position database setup complete")

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain with fallback RPCs"""
    endpoints = RPC_ENDPOINTS.get(chain_id, [])
    
    for endpoint in endpoints:
        try:
            w3 = Web3(Web3.HTTPProvider(endpoint))
            # Test the connection
            w3.eth.block_number
            logger.info(f"Connected to {endpoint}")
            return w3
        except Exception as e:
            logger.warning(f"Failed to connect to {endpoint}: {e}")
            continue
    
    raise ValueError(f"No working RPC endpoint found for chain {chain_id}")

def get_block_range_for_period(chain_id: int, days: int) -> Tuple[int, int]:
    """Get block range for a specific number of days"""
    w3 = get_web3_connection(chain_id)
    
    # Get current block
    current_block = w3.eth.block_number
    
    # Estimate blocks per day (varies by chain)
    blocks_per_day = {
        1: 7200,      # Ethereum ~12s blocks
    }
    
    blocks_for_period = blocks_per_day.get(chain_id, 7200) * days
    start_block = max(0, current_block - blocks_for_period)
    
    logger.info(f"Chain {chain_id}: Blocks {start_block} to {current_block} ({days} days)")
    return start_block, current_block

def fetch_increase_liquidity_events(chain_id: int, start_block: int, end_block: int):
    """Fetch Uniswap V3 IncreaseLiquidity events"""
    w3 = get_web3_connection(chain_id)
    config = LP_CONTRACTS[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for pool_address, pool_name in config.get('uniswap_v3_pools', []):
        logger.info(f"Fetching IncreaseLiquidity events for {pool_name} on chain {chain_id}")
        
        try:
            logs = w3.eth.get_logs({
                'address': pool_address,
                'topics': [LP_EVENT_SIGNATURES['increase_liquidity']],
                'fromBlock': start_block,
                'toBlock': end_block
            })
            
            for log in logs:
                # Decode the IncreaseLiquidity event
                decoded = decode(
                    ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                    bytes.fromhex(log['data'][2:])
                )
                
                owner = '0x' + log['topics'][1][-40:].hex()
                tick_lower = int.from_bytes(log['topics'][2][-3:], 'big', signed=True)
                tick_upper = int.from_bytes(log['topics'][3][-3:], 'big', signed=True)
                
                cursor.execute('''
                    INSERT INTO increase_liquidity_events 
                    (chain_id, pool_address, pool_name, block_number, tx_hash, log_index,
                     owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_id, pool_address, pool_name, log['blockNumber'], log['transactionHash'].hex(),
                    log['logIndex'], owner, tick_lower, tick_upper, str(decoded[3]), str(decoded[4]),
                    str(decoded[5]), int(time.time())
                ))
            
            logger.info(f"Found {len(logs)} IncreaseLiquidity events for {pool_name}")
            
        except Exception as e:
            logger.error(f"Error fetching IncreaseLiquidity events for {pool_name}: {e}")
    
    conn.commit()
    conn.close()

def fetch_decrease_liquidity_events(chain_id: int, start_block: int, end_block: int):
    """Fetch Uniswap V3 DecreaseLiquidity events"""
    w3 = get_web3_connection(chain_id)
    config = LP_CONTRACTS[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for pool_address, pool_name in config.get('uniswap_v3_pools', []):
        logger.info(f"Fetching DecreaseLiquidity events for {pool_name} on chain {chain_id}")
        
        try:
            logs = w3.eth.get_logs({
                'address': pool_address,
                'topics': [LP_EVENT_SIGNATURES['decrease_liquidity']],
                'fromBlock': start_block,
                'toBlock': end_block
            })
            
            for log in logs:
                # Decode the DecreaseLiquidity event
                decoded = decode(
                    ['address', 'int24', 'int24', 'uint128', 'uint256', 'uint256'],
                    bytes.fromhex(log['data'][2:])
                )
                
                owner = '0x' + log['topics'][1][-40:].hex()
                tick_lower = int.from_bytes(log['topics'][2][-3:], 'big', signed=True)
                tick_upper = int.from_bytes(log['topics'][3][-3:], 'big', signed=True)
                
                cursor.execute('''
                    INSERT INTO decrease_liquidity_events 
                    (chain_id, pool_address, pool_name, block_number, tx_hash, log_index,
                     owner, tick_lower, tick_upper, amount, amount0, amount1, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_id, pool_address, pool_name, log['blockNumber'], log['transactionHash'].hex(),
                    log['logIndex'], owner, tick_lower, tick_upper, str(decoded[3]), str(decoded[4]),
                    str(decoded[5]), int(time.time())
                ))
            
            logger.info(f"Found {len(logs)} DecreaseLiquidity events for {pool_name}")
            
        except Exception as e:
            logger.error(f"Error fetching DecreaseLiquidity events for {pool_name}: {e}")
    
    conn.commit()
    conn.close()

def fetch_collect_events(chain_id: int, start_block: int, end_block: int):
    """Fetch Uniswap V3 Collect events"""
    w3 = get_web3_connection(chain_id)
    config = LP_CONTRACTS[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for pool_address, pool_name in config.get('uniswap_v3_pools', []):
        logger.info(f"Fetching Collect events for {pool_name} on chain {chain_id}")
        
        try:
            logs = w3.eth.get_logs({
                'address': pool_address,
                'topics': [LP_EVENT_SIGNATURES['collect']],
                'fromBlock': start_block,
                'toBlock': end_block
            })
            
            for log in logs:
                # Decode the Collect event
                decoded = decode(
                    ['address', 'address', 'uint256', 'uint256'],
                    bytes.fromhex(log['data'][2:])
                )
                
                sender = '0x' + log['topics'][1][-40:].hex()
                recipient = '0x' + log['topics'][2][-40:].hex()
                
                cursor.execute('''
                    INSERT INTO collect_events 
                    (chain_id, pool_address, pool_name, block_number, tx_hash, log_index,
                     sender, recipient, amount0, amount1, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_id, pool_address, pool_name, log['blockNumber'], log['transactionHash'].hex(),
                    log['logIndex'], sender, recipient, str(decoded[2]), str(decoded[3]), int(time.time())
                ))
            
            logger.info(f"Found {len(logs)} Collect events for {pool_name}")
            
        except Exception as e:
            logger.error(f"Error fetching Collect events for {pool_name}: {e}")
    
    conn.commit()
    conn.close()

def calculate_lp_positions():
    """Calculate current LP positions from events"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all unique positions
    cursor.execute('''
        SELECT DISTINCT pool_address, pool_name, owner, tick_lower, tick_upper
        FROM (
            SELECT pool_address, pool_name, owner, tick_lower, tick_upper FROM increase_liquidity_events
            UNION
            SELECT pool_address, pool_name, owner, tick_lower, tick_upper FROM decrease_liquidity_events
        )
    ''')
    
    positions = cursor.fetchall()
    logger.info(f"Calculated LP positions for {len(positions)} unique positions")
    
    # Calculate net liquidity for each position
    for position in positions:
        pool_address, pool_name, owner, tick_lower, tick_upper = position
        
        # Sum all increases
        cursor.execute('''
            SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_increase
            FROM increase_liquidity_events
            WHERE pool_address = ? AND owner = ? AND tick_lower = ? AND tick_upper = ?
        ''', (pool_address, owner, tick_lower, tick_upper))
        total_increase = cursor.fetchone()[0]
        
        # Sum all decreases
        cursor.execute('''
            SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_decrease
            FROM decrease_liquidity_events
            WHERE pool_address = ? AND owner = ? AND tick_lower = ? AND tick_upper = ?
        ''', (pool_address, owner, tick_lower, tick_upper))
        total_decrease = cursor.fetchone()[0]
        
        # Net liquidity
        net_liquidity = total_increase - total_decrease
        
        if net_liquidity > 0:
            # Get latest amounts
            cursor.execute('''
                SELECT amount0, amount1 FROM increase_liquidity_events
                WHERE pool_address = ? AND owner = ? AND tick_lower = ? AND tick_upper = ?
                ORDER BY block_number DESC LIMIT 1
            ''', (pool_address, owner, tick_lower, tick_upper))
            latest_amounts = cursor.fetchone()
            
            if latest_amounts:
                amount0, amount1 = latest_amounts
                
                # Insert or update position summary
                cursor.execute('''
                    INSERT OR REPLACE INTO lp_position_summary
                    (pool_address, pool_name, owner, tick_lower, tick_upper, 
                     total_liquidity, total_amount0, total_amount1, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pool_address, pool_name, owner, tick_lower, tick_upper,
                      str(net_liquidity), amount0, amount1, datetime.now()))
    
    conn.commit()
    conn.close()

def create_activity_analysis_tables():
    """Create analysis tables for different time periods"""
    conn = sqlite3.connect(DB_PATH)
    
    # Define time periods
    periods = [
        (3, "3_days"),
        (7, "7_days"), 
        (14, "14_days"),
        (30, "30_days"),
        (90, "90_days")
    ]
    
    for days, period_name in periods:
        logger.info(f"Creating analysis for {period_name}")
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query for each pool
        for chain_id, config in LP_CONTRACTS.items():
            for pool_address, pool_name in config.get('uniswap_v3_pools', []):
                
                # Get adds in period
                adds_query = '''
                    SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_adds,
                           COUNT(DISTINCT owner) as unique_lps
                    FROM increase_liquidity_events
                    WHERE pool_address = ? AND timestamp >= ?
                '''
                
                cursor = conn.cursor()
                cursor.execute(adds_query, (pool_address, int(start_date.timestamp())))
                adds_result = cursor.fetchone()
                total_adds, unique_lps = adds_result
                
                # Get removes in period
                removes_query = '''
                    SELECT COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_removes
                    FROM decrease_liquidity_events
                    WHERE pool_address = ? AND timestamp >= ?
                '''
                
                cursor.execute(removes_query, (pool_address, int(start_date.timestamp())))
                total_removes = cursor.fetchone()[0]
                
                # Calculate net change
                net_change = total_adds - total_removes
                
                # Insert analysis
                cursor.execute('''
                    INSERT OR REPLACE INTO lp_activity_analysis
                    (pool_address, pool_name, period, total_adds, total_removes, 
                     net_change, unique_lps, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pool_address, pool_name, period_name, str(total_adds), str(total_removes),
                      str(net_change), unique_lps, start_date.isoformat(), end_date.isoformat()))
    
    conn.commit()
    conn.close()

def create_pool_balances_table():
    """Create summary table of all pool balances"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for chain_id, config in LP_CONTRACTS.items():
        for pool_address, pool_name in config.get('uniswap_v3_pools', []):
            
            # Get total liquidity across all positions
            cursor.execute('''
                SELECT COALESCE(SUM(CAST(total_liquidity AS INTEGER)), 0) as total_liquidity,
                       COUNT(*) as unique_positions
                FROM lp_position_summary
                WHERE pool_address = ?
            ''', (pool_address,))
            
            result = cursor.fetchone()
            total_liquidity, unique_positions = result
            
            # Get latest amounts (from most recent position)
            cursor.execute('''
                SELECT total_amount0, total_amount1
                FROM lp_position_summary
                WHERE pool_address = ?
                ORDER BY last_updated DESC
                LIMIT 1
            ''', (pool_address,))
            
            amounts = cursor.fetchone()
            total_amount0 = amounts[0] if amounts else "0"
            total_amount1 = amounts[1] if amounts else "0"
            
            # Insert pool balance
            cursor.execute('''
                INSERT OR REPLACE INTO lp_pool_balances
                (pool_address, pool_name, total_liquidity, total_amount0, total_amount1,
                 unique_positions, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (pool_address, pool_name, str(total_liquidity), total_amount0, total_amount1,
                  unique_positions, datetime.now()))
    
    conn.commit()
    conn.close()

def display_analysis_tables():
    """Display the analysis tables in a formatted way"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*80)
    print("LP ACTIVITY ANALYSIS (Last 3 Days, 7 Days, 14 Days, 30 Days, 90 Days)")
    print("="*80)
    
    # Activity analysis table
    df_activity = pd.read_sql_query('''
        SELECT pool_name, period, total_adds, total_removes, net_change, unique_lps
        FROM lp_activity_analysis
        ORDER BY pool_name, period
    ''', conn)
    
    if not df_activity.empty:
        print(df_activity.to_string(index=False))
    else:
        print("No activity data available")
    
    print("\n" + "="*80)
    print("LP POOL BALANCES")
    print("="*80)
    
    # Pool balances table
    df_balances = pd.read_sql_query('''
        SELECT pool_name, total_liquidity, total_amount0, total_amount1, unique_positions
        FROM lp_pool_balances
        ORDER BY pool_name
    ''', conn)
    
    if not df_balances.empty:
        print(df_balances.to_string(index=False))
    else:
        print("No balance data available")
    
    conn.close()

def main():
    """Main function to run the comprehensive LP listener"""
    logger.info("Starting ShapeShift LP position tracker")
    
    setup_database()
    
    # Process each chain
    for chain_id in LP_CONTRACTS.keys():
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block range for last 90 days (to cover all analysis periods)
            start_block, end_block = get_block_range_for_period(chain_id, 90)
            
            # Fetch events
            fetch_increase_liquidity_events(chain_id, start_block, end_block)
            fetch_decrease_liquidity_events(chain_id, start_block, end_block)
            fetch_collect_events(chain_id, start_block, end_block)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
    
    # Calculate positions and create analysis tables
    calculate_lp_positions()
    create_activity_analysis_tables()
    create_pool_balances_table()
    
    # Display results
    display_analysis_tables()
    
    logger.info("LP position listener run complete!")

if __name__ == "__main__":
    main() 