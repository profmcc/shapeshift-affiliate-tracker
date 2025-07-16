#!/usr/bin/env python3
"""
Test script to verify ShapeShift affiliate addresses and test with smaller time ranges
"""

import os
import sqlite3
import time
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'test_affiliate_addresses.db'

# Use environment variables for RPC URLs
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
POLYGON_RPC = os.getenv('POLYGON_RPC', 'https://polygon-rpc.com')

# ShapeShift affiliate addresses to test
AFFILIATE_ADDRESSES = {
    1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",      # Ethereum
    137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",     # Polygon
}

# Alternative addresses to test (from common sources)
ALTERNATIVE_ADDRESSES = {
    1: [
        "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Original
        "0x9B4e2568107412151D6f8De914B3e2f7F073D900",  # Alternative 1
        "0x8B396ddF906D552b2Fc4A6f1F9cB3C1C3C3C3C3C",  # Alternative 2
    ],
    137: [
        "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Original
        "0x9B4e2568107412151D6f8De914B3e2f7F073D900",  # Alternative 1
        "0x8B396ddF906D552b2Fc4A6f1F9cB3C1C3C3C3C3C",  # Alternative 2
    ]
}

def test_address_activity(chain_id: int, address: str, w3: Web3) -> dict:
    """Test if an address has recent activity"""
    try:
        # Get current block
        current_block = w3.eth.block_number
        
        # Check last 1000 blocks for any transactions
        start_block = current_block - 1000
        
        # Get transaction count
        tx_count = w3.eth.get_transaction_count(address)
        
        # Get balance
        balance = w3.eth.get_balance(address)
        
        # Check for recent ERC20 transfers to this address
        erc20_transfer_sig = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
        
        try:
            logs = w3.eth.get_logs({
                'topics': [erc20_transfer_sig, None, '0x' + '0' * 24 + address[2:]],  # Transfer to this address
                'fromBlock': start_block,
                'toBlock': current_block
            })
            recent_transfers = len(logs)
        except:
            recent_transfers = 0
        
        return {
            'address': address,
            'transaction_count': tx_count,
            'balance': balance,
            'recent_transfers': recent_transfers,
            'active': tx_count > 0 or recent_transfers > 0
        }
        
    except Exception as e:
        logger.error(f"Error testing address {address}: {e}")
        return {
            'address': address,
            'transaction_count': 0,
            'balance': 0,
            'recent_transfers': 0,
            'active': False,
            'error': str(e)
        }

def test_small_time_range(chain_id: int, start_block: int, end_block: int):
    """Test with a small time range to avoid getting hung up"""
    w3 = Web3(Web3.HTTPProvider(INFURA_URL if chain_id == 1 else POLYGON_RPC))
    
    logger.info(f"Testing small time range: blocks {start_block} to {end_block} on chain {chain_id}")
    
    # Test CowSwap contract
    cowswap_address = '0x9008D19f58AAbD9eD0D60971565AA8510560ab41'
    
    try:
        logs = w3.eth.get_logs({
            'address': cowswap_address,
            'fromBlock': start_block,
            'toBlock': end_block
        })
        
        logger.info(f"Found {len(logs)} CowSwap logs in test range")
        
        # Check for any affiliate-related events
        affiliate_address = AFFILIATE_ADDRESSES[chain_id]
        affiliate_events = 0
        
        for log in logs:
            if len(log['topics']) > 0:
                event_sig = log['topics'][0].hex() if hasattr(log['topics'][0], 'hex') else log['topics'][0]
                
                # Check if this event involves the affiliate address
                for topic in log['topics']:
                    topic_hex = topic.hex() if hasattr(topic, 'hex') else str(topic)
                    if affiliate_address.lower() in topic_hex.lower():
                        affiliate_events += 1
                        logger.info(f"Found affiliate-related event: {event_sig}")
        
        logger.info(f"Found {affiliate_events} affiliate-related events")
        
    except Exception as e:
        logger.error(f"Error testing CowSwap: {e}")

def main():
    """Main test function"""
    logger.info("Starting affiliate address verification test")
    
    # Test each chain
    for chain_id in [1, 137]:
        logger.info(f"\n=== Testing Chain {chain_id} ===")
        
        # Connect to the chain
        rpc_url = INFURA_URL if chain_id == 1 else POLYGON_RPC
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        try:
            current_block = w3.eth.block_number
            logger.info(f"Current block: {current_block}")
            
            # Test each affiliate address
            for address in ALTERNATIVE_ADDRESSES[chain_id]:
                logger.info(f"\nTesting address: {address}")
                result = test_address_activity(chain_id, address, w3)
                
                logger.info(f"  Transaction count: {result['transaction_count']}")
                logger.info(f"  Balance: {result['balance']}")
                logger.info(f"  Recent transfers: {result['recent_transfers']}")
                logger.info(f"  Active: {result['active']}")
                
                if 'error' in result:
                    logger.error(f"  Error: {result['error']}")
            
            # Test small time range
            test_start = current_block - 1000
            test_end = current_block - 500
            test_small_time_range(chain_id, test_start, test_end)
            
        except Exception as e:
            logger.error(f"Error testing chain {chain_id}: {e}")
    
    logger.info("\nAffiliate address verification test complete!")

if __name__ == "__main__":
    main() 