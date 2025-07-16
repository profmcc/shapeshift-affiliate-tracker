#!/usr/bin/env python3
"""
Debug version of ShapeShift Affiliate Fee Tracker
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
DB_PATH = 'shapeshift_affiliate_fees_debug.db'

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

def get_web3_connection(chain_id: int) -> Web3:
    """Get Web3 connection for a specific chain"""
    config = AFFILIATE_CONTRACTS.get(chain_id)
    if not config:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    return Web3(Web3.HTTPProvider(config['rpc']))

def debug_contract_info(chain_id: int):
    """Debug contract information and connectivity"""
    logger.info(f"=== Debugging Chain {chain_id} ===")
    
    config = AFFILIATE_CONTRACTS[chain_id]
    affiliate_address = SHAPESHIFT_AFFILIATES[chain_id]
    
    logger.info(f"RPC URL: {config['rpc']}")
    logger.info(f"Affiliate Address: {affiliate_address}")
    
    try:
        w3 = get_web3_connection(chain_id)
        
        # Test connection
        current_block = w3.eth.block_number
        logger.info(f"Current block: {current_block}")
        
        # Test each contract
        for contract_name, contract_address in config.items():
            if contract_name == 'rpc':
                continue
                
            logger.info(f"\n--- Testing {contract_name} contract ---")
            logger.info(f"Contract address: {contract_address}")
            
            try:
                # Get contract code
                code = w3.eth.get_code(contract_address)
                logger.info(f"Contract has code: {len(code) > 0}")
                
                # Get recent logs for this contract
                recent_block = current_block - 1000
                logs = w3.eth.get_logs({
                    'address': contract_address,
                    'fromBlock': recent_block,
                    'toBlock': current_block
                })
                logger.info(f"Recent logs found: {len(logs)}")
                
                if len(logs) > 0:
                    logger.info(f"Sample log: {logs[0]}")
                    
            except Exception as e:
                logger.error(f"Error testing {contract_name}: {e}")
                
    except Exception as e:
        logger.error(f"Error connecting to chain {chain_id}: {e}")

def debug_event_signatures():
    """Debug event signature matching"""
    logger.info("=== Debugging Event Signatures ===")
    
    for event_name, signature in EVENT_SIGNATURES.items():
        logger.info(f"{event_name}: {signature}")
        
        # Test signature format
        try:
            # Convert to bytes and back
            sig_bytes = bytes.fromhex(signature[2:])
            sig_hex = '0x' + sig_bytes.hex()
            logger.info(f"  Signature validation: {signature == sig_hex}")
        except Exception as e:
            logger.error(f"  Error with signature {event_name}: {e}")

def main():
    """Debug main function"""
    logger.info("Starting debug affiliate fee tracker")
    
    # Debug event signatures
    debug_event_signatures()
    
    # Debug each chain
    for chain_id in AFFILIATE_CONTRACTS.keys():
        debug_contract_info(chain_id)
    
    logger.info("Debug complete!")

if __name__ == "__main__":
    main() 