#!/usr/bin/env python3
"""
Simple FOX LP Activity Checker
Checks for recent LP activity on FOX pools with minimal RPC calls.
"""

import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List
from web3 import Web3
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'fox_pools_analysis.db'

# Focus on the most active FOX pools
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
    }
]

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

def check_recent_activity(pool: Dict, hours: int = 24):
    """Check for recent LP activity on a pool"""
    w3 = get_web3_connection(pool['rpc'])
    
    current_block = w3.eth.block_number
    blocks_per_hour = 300  # Approximate for most chains
    blocks_for_period = blocks_per_hour * hours
    start_block = max(0, current_block - blocks_for_period)
    
    logger.info(f"Checking {pool['pool_name']} on {pool['chain_name']} for last {hours} hours")
    logger.info(f"Blocks {start_block} to {current_block}")
    
    try:
        # Just check if there are any logs at all for this pool
        logs = w3.eth.get_logs({
            'address': pool['pool_address'],
            'fromBlock': start_block,
            'toBlock': current_block
        })
        
        logger.info(f"Found {len(logs)} total logs for {pool['pool_name']}")
        
        if logs:
            # Show some sample logs
            for i, log in enumerate(logs[:5]):  # Show first 5 logs
                logger.info(f"Log {i+1}: Block {log['blockNumber']}, Topics: {log['topics'][:2]}")
        
        return len(logs)
        
    except Exception as e:
        logger.error(f"Error checking {pool['pool_name']}: {e}")
        return 0

def check_specific_events(pool: Dict, hours: int = 24):
    """Check for specific LP events"""
    w3 = get_web3_connection(pool['rpc'])
    
    current_block = w3.eth.block_number
    blocks_per_hour = 300
    blocks_for_period = blocks_per_hour * hours
    start_block = max(0, current_block - blocks_for_period)
    
    logger.info(f"Checking specific events for {pool['pool_name']}")
    
    try:
        if pool['type'] == 'uniswap_v3':
            # Check for V3 LP events
            increase_liquidity_topic = '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f'
            decrease_liquidity_topic = '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4'
            
            increase_logs = w3.eth.get_logs({
                'address': pool['pool_address'],
                'topics': [increase_liquidity_topic],
                'fromBlock': start_block,
                'toBlock': current_block
            })
            
            decrease_logs = w3.eth.get_logs({
                'address': pool['pool_address'],
                'topics': [decrease_liquidity_topic],
                'fromBlock': start_block,
                'toBlock': current_block
            })
            
            logger.info(f"V3 LP Events for {pool['pool_name']}:")
            logger.info(f"  Increase Liquidity: {len(increase_logs)}")
            logger.info(f"  Decrease Liquidity: {len(decrease_logs)}")
            
            return len(increase_logs), len(decrease_logs)
            
        elif pool['type'] == 'uniswap_v2':
            # Check for V2 LP events (mint/burn)
            mint_topic = '0x4c209b5fc8ad21358ac9a3b7e4b8b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b8c4b'
            burn_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
            
            mint_logs = w3.eth.get_logs({
                'address': pool['pool_address'],
                'topics': [mint_topic],
                'fromBlock': start_block,
                'toBlock': current_block
            })
            
            burn_logs = w3.eth.get_logs({
                'address': pool['pool_address'],
                'topics': [burn_topic],
                'fromBlock': start_block,
                'toBlock': current_block
            })
            
            logger.info(f"V2 LP Events for {pool['pool_name']}:")
            logger.info(f"  Mint: {len(mint_logs)}")
            logger.info(f"  Burn: {len(burn_logs)}")
            
            return len(mint_logs), len(burn_logs)
    
    except Exception as e:
        logger.error(f"Error checking specific events for {pool['pool_name']}: {e}")
        return 0, 0

def display_pool_summary():
    """Display the FOX pools summary"""
    print("\n" + "="*100)
    print("FOX POOLS SUMMARY")
    print("="*100)
    
    for pool in ACTIVE_FOX_POOLS:
        print(f"{pool['chain_name'].upper()}: {pool['pool_name']}")
        print(f"  Address: {pool['pool_address']}")
        print(f"  Type: {pool['type']}")
        print(f"  Total USD: ${pool['total_usd']:,.2f}")
        print(f"  FOX Balance: {pool['fox_balance']:,.2f} FOX")
        print()

def main():
    """Main function to check FOX LP activity"""
    logger.info("Starting FOX LP activity checker")
    
    display_pool_summary()
    
    print("\n" + "="*100)
    print("RECENT ACTIVITY CHECK (Last 24 Hours)")
    print("="*100)
    
    for pool in ACTIVE_FOX_POOLS:
        try:
            # Check general activity
            total_logs = check_recent_activity(pool, hours=24)
            
            # Check specific LP events
            event1_count, event2_count = check_specific_events(pool, hours=24)
            
            print(f"\n{pool['chain_name'].upper()}: {pool['pool_name']}")
            print(f"  Total Logs: {total_logs}")
            if pool['type'] == 'uniswap_v3':
                print(f"  Increase Liquidity Events: {event1_count}")
                print(f"  Decrease Liquidity Events: {event2_count}")
            elif pool['type'] == 'uniswap_v2':
                print(f"  Mint Events: {event1_count}")
                print(f"  Burn Events: {event2_count}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error processing {pool['pool_name']}: {e}")
    
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print("This script checks for recent LP activity on FOX pools.")
    print("If no events are found, it could mean:")
    print("1. No LP activity in the last 24 hours")
    print("2. RPC rate limiting issues")
    print("3. Pool addresses may be incorrect")
    print("4. Event signatures may need updating")
    
    logger.info("FOX LP activity check complete!")

if __name__ == "__main__":
    main() 