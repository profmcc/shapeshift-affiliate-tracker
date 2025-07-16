#!/usr/bin/env python3
"""
ShapeShift Affiliate Tracker - Listener Runner
Fetches all swap events from the last week and stores them in a database.
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
DB_PATH = 'shapeshift_swap_events.db'
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
POLYGON_RPC = os.getenv('POLYGON_RPC', 'https://polygon-rpc.com')
OPTIMISM_RPC = os.getenv('OPTIMISM_RPC', 'https://mainnet.optimism.io')
ARBITRUM_RPC = os.getenv('ARBITRUM_RPC', 'https://arb1.arbitrum.io/rpc')
BASE_RPC = os.getenv('BASE_RPC', 'https://mainnet.base.org')
AVALANCHE_RPC = os.getenv('AVALANCHE_RPC', 'https://api.avax.network/ext/bc/C/rpc')
BSC_RPC = os.getenv('BSC_RPC', 'https://bsc-dataseed.binance.org')

# ShapeShift affiliate addresses by chain
SHAPESHIFT_AFFILIATES = {
    1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",      # Ethereum
    137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",     # Polygon
    10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",     # Optimism
    42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
    8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",   # Base
    43114: "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche
    56: "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"       # BSC
}

# Contract configurations
CONTRACTS = {
    1: {  # Ethereum
        'uniswap_v2_pairs': [
            ('0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc', 'WETH/USDC'),
            ('0x470e8de2eBaef52014A47Cb5E6aF86884947F08c', 'WETH/FOX'),
            ('0x2fDbAdf3C4D5A8666Bc06645B8358ab803996E28', 'WETH/UNI'),
        ],
        'uniswap_v3_pools': [
            ('0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640', 'WETH/USDC V3'),
            ('0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36', 'WETH/USDT V3'),
            ('0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8', 'WETH/USDC V3 0.3%'),
        ],
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'portals': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'rpc': INFURA_URL
    },
    137: {  # Polygon
        'uniswap_v2_pairs': [
            ('0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827', 'WMATIC/USDC'),
            ('0x34965ba0ac2451A34a0471F04CCa3F990b8dea27', 'WMATIC/USDT'),
        ],
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': POLYGON_RPC
    },
    42161: {  # Arbitrum
        'uniswap_v2_pairs': [
            ('0x5f6ce0ca13b87bd738519545d3e018e70e339c24', 'WETH/FOX'),
        ],
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': ARBITRUM_RPC
    },
    8453: {  # Base
        'uniswap_v2_pairs': [
            ('0x4C36388bE6F416A29C8d8ED537538b8e4e5e8B52', 'WETH/USDC'),
        ],
        'cowswap': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': BASE_RPC
    },
    43114: {  # Avalanche
        'uniswap_v2_pairs': [
            ('0x2b4C76d0dc16BE1C31D4C1DC53bF9B45987Fc75c', 'WAVAX/USDC'),
        ],
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': AVALANCHE_RPC
    },
    56: {  # BSC
        'uniswap_v2_pairs': [
            ('0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16', 'WBNB/BUSD'),
        ],
        'zerox': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        'rpc': BSC_RPC
    }
}

# Event signatures
EVENT_SIGNATURES = {
    'uniswap_v2_swap': '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822',
    'uniswap_v3_swap': '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67',
    'cowswap_trade': '0xd78ad95fa46c994b6551d0da85fc275fe613ce3b7d2a7c2c2cfd7c6c3b7aadb3',
    'portals_portal': '0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03',
    'erc20_transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
}

def setup_database():
    """Create the database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for different event types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uniswap_v2_swaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            pair_address TEXT,
            pair_name TEXT,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
            sender TEXT,
            to_address TEXT,
            amount0_in TEXT,
            amount1_in TEXT,
            amount0_out TEXT,
            amount1_out TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uniswap_v3_swaps (
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
            sqrt_price_x96 TEXT,
            liquidity TEXT,
            tick INTEGER,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cowswap_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
            owner TEXT,
            sell_token TEXT,
            buy_token TEXT,
            sell_amount TEXT,
            buy_amount TEXT,
            fee_amount TEXT,
            order_uid TEXT,
            app_data TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zerox_transforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
            sender TEXT,
            input_token TEXT,
            output_token TEXT,
            input_amount TEXT,
            output_amount TEXT,
            affiliate_fee_token TEXT,
            affiliate_fee_amount TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portals_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER,
            block_number INTEGER,
            tx_hash TEXT,
            log_index INTEGER,
            input_token TEXT,
            input_amount TEXT,
            output_token TEXT,
            output_amount TEXT,
            sender TEXT,
            broadcaster TEXT,
            recipient TEXT,
            partner TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database setup complete")

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain"""
    config = CONTRACTS.get(chain_id)
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
        137: 28800,   # Polygon ~3s blocks
        10: 28800,    # Optimism ~3s blocks
        42161: 28800, # Arbitrum ~3s blocks
        8453: 28800,  # Base ~3s blocks
        43114: 28800, # Avalanche ~3s blocks
        56: 28800     # BSC ~3s blocks
    }
    
    blocks_per_week = blocks_per_day.get(chain_id, 28800) * 7
    start_block = max(0, current_block - blocks_per_week)
    
    logger.info(f"Chain {chain_id}: Blocks {start_block} to {current_block}")
    return start_block, current_block

def fetch_uniswap_v2_swaps(chain_id: int, start_block: int, end_block: int):
    """Fetch Uniswap V2 swap events"""
    w3 = get_web3_connection(chain_id)
    config = CONTRACTS[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for pair_address, pair_name in config.get('uniswap_v2_pairs', []):
        logger.info(f"Fetching V2 swaps for {pair_name} on chain {chain_id}")
        
        try:
            logs = w3.eth.get_logs({
                'address': pair_address,
                'topics': [EVENT_SIGNATURES['uniswap_v2_swap']],
                'fromBlock': start_block,
                'toBlock': end_block
            })
            
            for log in logs:
                # Decode the swap event
                decoded = decode(
                    ['address', 'uint256', 'uint256', 'uint256', 'uint256', 'address'],
                    bytes.fromhex(log['data'][2:])  # Remove '0x' prefix
                )
                
                sender = '0x' + log['topics'][1][-40:].hex()
                to_address = '0x' + log['topics'][2][-40:].hex()
                
                cursor.execute('''
                    INSERT INTO uniswap_v2_swaps 
                    (chain_id, pair_address, pair_name, block_number, tx_hash, log_index, 
                     sender, to_address, amount0_in, amount1_in, amount0_out, amount1_out, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_id, pair_address, pair_name, log['blockNumber'], log['transactionHash'].hex(),
                    log['logIndex'], sender, to_address, str(decoded[1]), str(decoded[2]),
                    str(decoded[3]), str(decoded[4]), int(time.time())
                ))
            
            logger.info(f"Found {len(logs)} V2 swaps for {pair_name}")
            
        except Exception as e:
            logger.error(f"Error fetching V2 swaps for {pair_name}: {e}")
    
    conn.commit()
    conn.close()

def fetch_uniswap_v3_swaps(chain_id: int, start_block: int, end_block: int):
    """Fetch Uniswap V3 swap events"""
    w3 = get_web3_connection(chain_id)
    config = CONTRACTS[chain_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for pool_address, pool_name in config.get('uniswap_v3_pools', []):
        logger.info(f"Fetching V3 swaps for {pool_name} on chain {chain_id}")
        
        try:
            logs = w3.eth.get_logs({
                'address': pool_address,
                'topics': [EVENT_SIGNATURES['uniswap_v3_swap']],
                'fromBlock': start_block,
                'toBlock': end_block
            })
            
            for log in logs:
                # Decode the swap event
                decoded = decode(
                    ['address', 'address', 'int256', 'int256', 'uint160', 'uint128', 'int24'],
                    bytes.fromhex(log['data'][2:])
                )
                
                sender = '0x' + log['topics'][1][-40:].hex()
                recipient = '0x' + log['topics'][2][-40:].hex()
                
                cursor.execute('''
                    INSERT INTO uniswap_v3_swaps 
                    (chain_id, pool_address, pool_name, block_number, tx_hash, log_index,
                     sender, recipient, amount0, amount1, sqrt_price_x96, liquidity, tick, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_id, pool_address, pool_name, log['blockNumber'], log['transactionHash'].hex(),
                    log['logIndex'], sender, recipient, str(decoded[2]), str(decoded[3]),
                    str(decoded[4]), str(decoded[5]), decoded[6], int(time.time())
                ))
            
            logger.info(f"Found {len(logs)} V3 swaps for {pool_name}")
            
        except Exception as e:
            logger.error(f"Error fetching V3 swaps for {pool_name}: {e}")
    
    conn.commit()
    conn.close()

def fetch_cowswap_trades(chain_id: int, start_block: int, end_block: int):
    """Fetch CowSwap trade events"""
    w3 = get_web3_connection(chain_id)
    config = CONTRACTS[chain_id]
    
    if 'cowswap' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    logger.info(f"Fetching CowSwap trades on chain {chain_id}")
    
    try:
        logs = w3.eth.get_logs({
            'address': config['cowswap'],
            'topics': [EVENT_SIGNATURES['cowswap_trade']],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        for log in logs:
            # Decode the trade event
            decoded = decode(
                ['address', 'address', 'address', 'uint256', 'uint256', 'uint256', 'bytes', 'bytes32'],
                bytes.fromhex(log['data'][2:])
            )
            
            cursor.execute('''
                INSERT INTO cowswap_trades 
                (chain_id, block_number, tx_hash, log_index, owner, sell_token, buy_token,
                 sell_amount, buy_amount, fee_amount, order_uid, app_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chain_id, log['blockNumber'], log['transactionHash'].hex(), log['logIndex'],
                decoded[0], decoded[1], decoded[2], str(decoded[3]), str(decoded[4]),
                str(decoded[5]), decoded[6].hex(), decoded[7].hex(), int(time.time())
            ))
        
        logger.info(f"Found {len(logs)} CowSwap trades")
        
    except Exception as e:
        logger.error(f"Error fetching CowSwap trades: {e}")
    
    conn.commit()
    conn.close()

def fetch_zerox_transforms(chain_id: int, start_block: int, end_block: int):
    """Fetch 0x transformERC20 function calls"""
    w3 = get_web3_connection(chain_id)
    config = CONTRACTS[chain_id]
    
    if 'zerox' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    logger.info(f"Fetching 0x transforms on chain {chain_id}")
    
    try:
        # Get all transactions to the 0x contract
        logs = w3.eth.get_logs({
            'address': config['zerox'],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        for log in logs:
            # Check if this is a transformERC20 call
            if len(log['topics']) > 0 and log['topics'][0].hex() == '0x68c6fa61':  # transformERC20 signature
                try:
                    # Get transaction details
                    tx = w3.eth.get_transaction(log['transactionHash'])
                    tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
                    
                    # Basic info
                    cursor.execute('''
                        INSERT INTO zerox_transforms 
                        (chain_id, block_number, tx_hash, log_index, sender, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        chain_id, log['blockNumber'], log['transactionHash'].hex(), log['logIndex'],
                        tx['from'], int(time.time())
                    ))
                    
                except Exception as e:
                    logger.error(f"Error processing 0x transaction {log['transactionHash'].hex()}: {e}")
        
        logger.info(f"Found {len(logs)} 0x contract interactions")
        
    except Exception as e:
        logger.error(f"Error fetching 0x transforms: {e}")
    
    conn.commit()
    conn.close()

def fetch_portals_events(chain_id: int, start_block: int, end_block: int):
    """Fetch Portals events"""
    w3 = get_web3_connection(chain_id)
    config = CONTRACTS[chain_id]
    
    if 'portals' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    logger.info(f"Fetching Portals events on chain {chain_id}")
    
    try:
        logs = w3.eth.get_logs({
            'address': config['portals'],
            'topics': [EVENT_SIGNATURES['portals_portal']],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        for log in logs:
            # Decode the portal event
            decoded = decode(
                ['address', 'uint256', 'address', 'uint256', 'address', 'address', 'address', 'address'],
                bytes.fromhex(log['data'][2:])
            )
            
            sender = '0x' + log['topics'][1][-40:].hex()
            broadcaster = '0x' + log['topics'][2][-40:].hex()
            partner = '0x' + log['topics'][3][-40:].hex()
            
            cursor.execute('''
                INSERT INTO portals_events 
                (chain_id, block_number, tx_hash, log_index, input_token, input_amount,
                 output_token, output_amount, sender, broadcaster, recipient, partner, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chain_id, log['blockNumber'], log['transactionHash'].hex(), log['logIndex'],
                decoded[0], str(decoded[1]), decoded[2], str(decoded[3]), sender, broadcaster,
                decoded[4], partner, int(time.time())
            ))
        
        logger.info(f"Found {len(logs)} Portals events")
        
    except Exception as e:
        logger.error(f"Error fetching Portals events: {e}")
    
    conn.commit()
    conn.close()

def main():
    """Main function to run the listener for the last week"""
    logger.info("Starting ShapeShift affiliate tracker listener")
    
    # Setup database
    setup_database()
    
    # Process each chain
    for chain_id in CONTRACTS.keys():
        logger.info(f"Processing chain {chain_id}")
        
        try:
            # Get block range for the last week
            start_block, end_block = get_block_range_for_week(chain_id)
            
            # Fetch different types of events
            fetch_uniswap_v2_swaps(chain_id, start_block, end_block)
            fetch_uniswap_v3_swaps(chain_id, start_block, end_block)
            fetch_cowswap_trades(chain_id, start_block, end_block)
            fetch_zerox_transforms(chain_id, start_block, end_block)
            fetch_portals_events(chain_id, start_block, end_block)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    logger.info("Listener run complete!")
    
    # Print summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM uniswap_v2_swaps")
    v2_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM uniswap_v3_swaps")
    v3_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cowswap_trades")
    cowswap_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM zerox_transforms")
    zerox_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM portals_events")
    portals_count = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"Summary:")
    logger.info(f"  Uniswap V2 swaps: {v2_count}")
    logger.info(f"  Uniswap V3 swaps: {v3_count}")
    logger.info(f"  CowSwap trades: {cowswap_count}")
    logger.info(f"  0x transforms: {zerox_count}")
    logger.info(f"  Portals events: {portals_count}")
    logger.info(f"  Total events: {v2_count + v3_count + cowswap_count + zerox_count + portals_count}")

if __name__ == "__main__":
    main() 