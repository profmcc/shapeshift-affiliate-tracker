#!/usr/bin/env python3
"""
ShapeShift Affiliate Fee Tracker - Corrected Version
Fetches affiliate fee events with proper CRM data structure matching.
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
DB_PATH = 'shapeshift_affiliate_fees_corrected.db'

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

# Event signatures
EVENT_SIGNATURES = {
    'cowswap_trade': '0xd78ad95fa46c994b6551d0da85fc275fe613ce3b7d2a7c2c2cfd7c6c3b7aadb3',
    'portals_portal': '0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03',
    'erc20_transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
}

def setup_database():
    """Create the database and tables matching CRM structure"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Portals affiliate events - matching CRM structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portals_affiliate_events (
            tx_hash TEXT,
            block_number INTEGER,
            input_token TEXT,
            input_amount TEXT,
            output_token TEXT,
            output_amount TEXT,
            sender TEXT,
            broadcaster TEXT,
            recipient TEXT,
            partner TEXT,
            timestamp INTEGER,
            affiliate_token TEXT,
            affiliate_amount TEXT
        )
    ''')
    
    # CowSwap affiliate trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cowswap_affiliate_trades (
            tx_hash TEXT,
            block_number INTEGER,
            owner TEXT,
            sell_token TEXT,
            buy_token TEXT,
            sell_amount TEXT,
            buy_amount TEXT,
            fee_amount TEXT,
            order_uid TEXT,
            timestamp INTEGER
        )
    ''')
    
    # 0x Protocol affiliate fee payments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zerox_affiliate_fees (
            tx_hash TEXT,
            block_number INTEGER,
            sender TEXT,
            affiliate_fee_token TEXT,
            affiliate_fee_amount TEXT,
            affiliate_address TEXT,
            timestamp INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Corrected affiliate fee database setup complete")

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

def fetch_portals_affiliate_events(chain_id: int, start_block: int, end_block: int):
    """Fetch Portals events where ShapeShift is the partner (affiliate)"""
    w3 = get_web3_connection(chain_id)
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    if 'portals' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        logs = w3.eth.get_logs({
            'address': config['portals'],
            'topics': [EVENT_SIGNATURES['portals_portal']],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        affiliate_events = 0
        
        for log in logs:
            # Decode the portal event
            decoded = decode(
                ['address', 'uint256', 'address', 'uint256', 'address', 'address', 'address', 'address'],
                bytes.fromhex(log['data'][2:])
            )
            
            sender = '0x' + log['topics'][1][-40:].hex()
            broadcaster = '0x' + log['topics'][2][-40:].hex()
            partner = '0x' + log['topics'][3][-40:].hex()
            
            # Only track events where ShapeShift is the partner (affiliate)
            if partner.lower() == affiliate_address.lower():
                # Get block timestamp
                try:
                    block = w3.eth.get_block(log['blockNumber'])
                    timestamp = block['timestamp']
                except:
                    timestamp = int(time.time())
                
                # Look for affiliate fee payment in transaction
                affiliate_token, affiliate_amount = fetch_affiliate_payment(w3, log['transactionHash'], affiliate_address)
                
                cursor.execute('''
                    INSERT INTO portals_affiliate_events 
                    (tx_hash, block_number, input_token, input_amount, output_token, output_amount,
                     sender, broadcaster, recipient, partner, timestamp, affiliate_token, affiliate_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log['transactionHash'].hex(), log['blockNumber'], decoded[0], str(decoded[1]),
                    decoded[2], str(decoded[3]), sender, broadcaster, decoded[4], partner,
                    timestamp, affiliate_token, affiliate_amount
                ))
                affiliate_events += 1
        
        if affiliate_events > 0:
            logger.info(f"Found {affiliate_events} Portals affiliate events in blocks {start_block}-{end_block}")
        
    except Exception as e:
        logger.error(f"Error fetching Portals affiliate events for blocks {start_block}-{end_block}: {e}")
    
    conn.commit()
    conn.close()

def fetch_affiliate_payment(w3: Web3, tx_hash: bytes, affiliate_address: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch affiliate fee payment from transaction logs"""
    try:
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        for log in tx_receipt['logs']:
            if (log['topics'][0].hex() == EVENT_SIGNATURES['erc20_transfer'] and
                len(log['topics']) >= 3):
                
                to_address = '0x' + log['topics'][2][-40:].hex()
                
                if to_address.lower() == affiliate_address.lower():
                    token_address = log['address']
                    amount = int(log['data'], 16)
                    return token_address, str(amount)
        
        return None, None
    except Exception as e:
        logger.error(f"Error fetching affiliate payment for tx {tx_hash.hex()}: {e}")
        return None, None

def fetch_cowswap_affiliate_trades(chain_id: int, start_block: int, end_block: int):
    """Fetch CowSwap trades where ShapeShift is the owner (affiliate trades)"""
    w3 = get_web3_connection(chain_id)
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    if 'cowswap' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        logs = w3.eth.get_logs({
            'address': config['cowswap'],
            'topics': [EVENT_SIGNATURES['cowswap_trade']],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        affiliate_trades = 0
        
        for log in logs:
            # Decode the trade event
            decoded = decode(
                ['address', 'address', 'address', 'uint256', 'uint256', 'uint256', 'bytes', 'bytes32'],
                bytes.fromhex(log['data'][2:])
            )
            
            owner = decoded[0]
            
            # Only track trades where ShapeShift is the owner (affiliate trades)
            if owner.lower() == affiliate_address.lower():
                # Get block timestamp
                try:
                    block = w3.eth.get_block(log['blockNumber'])
                    timestamp = block['timestamp']
                except:
                    timestamp = int(time.time())
                
                cursor.execute('''
                    INSERT INTO cowswap_affiliate_trades 
                    (tx_hash, block_number, owner, sell_token, buy_token, sell_amount, buy_amount, fee_amount, order_uid, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log['transactionHash'].hex(), log['blockNumber'], owner, decoded[1], decoded[2],
                    str(decoded[3]), str(decoded[4]), str(decoded[5]), decoded[6].hex(), timestamp
                ))
                affiliate_trades += 1
        
        if affiliate_trades > 0:
            logger.info(f"Found {affiliate_trades} CowSwap affiliate trades in blocks {start_block}-{end_block}")
        
    except Exception as e:
        logger.error(f"Error fetching CowSwap affiliate trades for blocks {start_block}-{end_block}: {e}")
    
    conn.commit()
    conn.close()

def fetch_zerox_affiliate_fees(chain_id: int, start_block: int, end_block: int):
    """Fetch 0x transformERC20 calls and identify affiliate fee payments"""
    w3 = get_web3_connection(chain_id)
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    if 'zerox' not in config:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all transactions to the 0x contract
        logs = w3.eth.get_logs({
            'address': config['zerox'],
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        affiliate_fees = 0
        
        for log in logs:
            # Check if this is a transformERC20 call
            if len(log['topics']) > 0 and log['topics'][0].hex() == '0x68c6fa61':  # transformERC20 signature
                try:
                    # Get transaction details
                    tx = w3.eth.get_transaction(log['transactionHash'])
                    
                    # Look for ERC20 transfers to the affiliate address
                    affiliate_token, affiliate_amount = fetch_affiliate_payment(w3, log['transactionHash'], affiliate_address)
                    
                    if affiliate_token and affiliate_amount:
                        # Get block timestamp
                        try:
                            block = w3.eth.get_block(log['blockNumber'])
                            timestamp = block['timestamp']
                        except:
                            timestamp = int(time.time())
                        
                        cursor.execute('''
                            INSERT INTO zerox_affiliate_fees 
                            (tx_hash, block_number, sender, affiliate_fee_token, affiliate_fee_amount, affiliate_address, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            log['transactionHash'].hex(), log['blockNumber'], tx['from'],
                            affiliate_token, affiliate_amount, affiliate_address, timestamp
                        ))
                        affiliate_fees += 1
                    
                except Exception as e:
                    logger.error(f"Error processing 0x transaction {log['transactionHash'].hex()}: {e}")
        
        if affiliate_fees > 0:
            logger.info(f"Found {affiliate_fees} 0x affiliate fee payments in blocks {start_block}-{end_block}")
        
    except Exception as e:
        logger.error(f"Error fetching 0x affiliate fees for blocks {start_block}-{end_block}: {e}")
    
    conn.commit()
    conn.close()

def main():
    """Main function to run the corrected affiliate fee listener"""
    logger.info("Starting ShapeShift affiliate fee tracker (corrected)")
    
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
                
                # Fetch affiliate fee events
                fetch_portals_affiliate_events(chain_id, start_block, end_block)
                fetch_cowswap_affiliate_trades(chain_id, start_block, end_block)
                fetch_zerox_affiliate_fees(chain_id, start_block, end_block)
                
                # Small delay to avoid overwhelming RPC
                time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error processing chain {chain_id}: {e}")
            continue
    
    logger.info("Corrected affiliate fee listener run complete!")
    
    # Print summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM portals_affiliate_events")
    portals_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cowswap_affiliate_trades")
    cowswap_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM zerox_affiliate_fees")
    zerox_count = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"Corrected Affiliate Fee Summary:")
    logger.info(f"  Portals affiliate events: {portals_count}")
    logger.info(f"  CowSwap affiliate trades: {cowswap_count}")
    logger.info(f"  0x affiliate fee payments: {zerox_count}")
    logger.info(f"  Total affiliate events: {portals_count + cowswap_count + zerox_count}")

if __name__ == "__main__":
    main() 