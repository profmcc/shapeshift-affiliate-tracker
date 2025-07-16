#!/usr/bin/env python3
"""
ShapeShift LP Position Tracker - Listener Runner
Fetches all liquidity position events from the last week and stores them in a database.
Focuses only on Uniswap V3 liquidity add/remove/collect events for LP tracking.
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
DB_PATH = 'shapeshift_lp_positions.db'
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')

# LP tracking contract configurations (focusing on major pools)
LP_CONTRACTS = {
    1: {  # Ethereum
        'uniswap_v3_pools': [
            ('0x470e8de2eBaef52014A47Cb5E6aF86884947F08c', 'WETH/FOX LP Pool'),
            ('0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640', 'WETH/USDC V3'),
            ('0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36', 'WETH/USDT V3'),
            ('0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8', 'WETH/USDC V3 0.3%'),
        ],
        'rpc': INFURA_URL
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
    
    conn.commit()
    conn.close()
    logger.info("LP position database setup complete")

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain"""
    config = LP_CONTRACTS.get(chain_id)
    if not config:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    return Web3(Web3.HTTPProvider(config['rpc']))

def get_block_range_for_week(chain_id: int) -> Tuple[int, int]:
    """Get block range for the last week"""
    w3 = get_web3_connection(chain_id)
    
    # Get current block
    current_block = w3.eth.block_number
    
    # Estimate blocks per day (varies by chain)
    blocks_per_day = {
        1: 7200,      # Ethereum ~12s blocks
    }
    
    blocks_per_week = blocks_per_day.get(chain_id, 7200) * 7
    start_block = max(0, current_block - blocks_per_week)
    
    logger.info(f"Chain {chain_id}: Blocks {start_block} to {current_block}")
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
    
    # Get all unique position identifiers
    cursor.execute('''
        SELECT DISTINCT pool_address, owner, tick_lower, tick_upper
        FROM (
            SELECT pool_address, owner, tick_lower, tick_upper FROM increase_liquidity_events
            UNION
            SELECT pool_address, owner, tick_lower, tick_upper FROM decrease_liquidity_events
        )
    ''')
    
    positions = cursor.fetchall()
    
    for position in positions:
        pool_address, owner, tick_lower, tick_upper = position
        
        # Calculate net liquidity for this position
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_increase,
                COALESCE(SUM(CAST(amount0 AS INTEGER)), 0) as total_amount0_increase,
                COALESCE(SUM(CAST(amount1 AS INTEGER)), 0) as total_amount1_increase
            FROM increase_liquidity_events
            WHERE pool_address = ? AND owner = ? AND tick_lower = ? AND tick_upper = ?
        ''', (pool_address, owner, tick_lower, tick_upper))
        
        increase_data = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CAST(amount AS INTEGER)), 0) as total_decrease,
                COALESCE(SUM(CAST(amount0 AS INTEGER)), 0) as total_amount0_decrease,
                COALESCE(SUM(CAST(amount1 AS INTEGER)), 0) as total_amount1_decrease
            FROM decrease_liquidity_events
            WHERE pool_address = ? AND owner = ? AND tick_lower = ? AND tick_upper = ?
        ''', (pool_address, owner, tick_lower, tick_upper))
        
        decrease_data = cursor.fetchone()
        
        # Calculate net position
        net_liquidity = increase_data[0] - decrease_data[0]
        net_amount0 = increase_data[1] - decrease_data[1]
        net_amount1 = increase_data[2] - decrease_data[2]
        
        # Get pool name
        cursor.execute('SELECT pool_name FROM increase_liquidity_events WHERE pool_address = ? LIMIT 1', (pool_address,))
        pool_name_result = cursor.fetchone()
        pool_name = pool_name_result[0] if pool_name_result else 'Unknown Pool'
        
        # Update or insert position summary
        cursor.execute('''
            INSERT OR REPLACE INTO lp_position_summary 
            (pool_address, pool_name, owner, tick_lower, tick_upper, 
             total_liquidity, total_amount0, total_amount1, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (pool_address, pool_name, owner, tick_lower, tick_upper, 
              str(net_liquidity), str(net_amount0), str(net_amount1)))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Calculated LP positions for {len(positions)} unique positions")

def main():
    """Main function to run the LP position listener for the last week"""
    logger.info("Starting ShapeShift LP position tracker")
    
    # Setup database
    setup_database()
    
    # Process each chain
    for chain_id in LP_CONTRACTS.keys():
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block range for the last week
            start_block, end_block = get_block_range_for_week(chain_id)
            
            # Fetch LP events
            fetch_increase_liquidity_events(chain_id, start_block, end_block)
            fetch_decrease_liquidity_events(chain_id, start_block, end_block)
            fetch_collect_events(chain_id, start_block, end_block)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    # Calculate LP positions
    calculate_lp_positions()
    
    logger.info("LP position listener run complete!")
    
    # Print summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM increase_liquidity_events")
    increase_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM decrease_liquidity_events")
    decrease_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM collect_events")
    collect_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lp_position_summary")
    position_count = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"LP Position Summary:")
    logger.info(f"  IncreaseLiquidity events: {increase_count}")
    logger.info(f"  DecreaseLiquidity events: {decrease_count}")
    logger.info(f"  Collect events: {collect_count}")
    logger.info(f"  Active LP positions: {position_count}")
    logger.info(f"  Total LP events: {increase_count + decrease_count + collect_count}")

if __name__ == "__main__":
    main() 