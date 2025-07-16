#!/usr/bin/env python3
"""
Analyze logs to find actual event signatures
"""

import os
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use environment variables for RPC URLs
POLYGON_RPC = os.getenv('POLYGON_RPC', 'https://polygon-rpc.com')

def analyze_cowswap_logs():
    """Analyze CowSwap logs to find actual event signatures"""
    logger.info("=== Analyzing CowSwap Logs ===")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    cowswap_address = '0x9008D19f58AAbD9eD0D60971565AA8510560ab41'
    
    # Get recent logs
    current_block = w3.eth.block_number
    recent_block = current_block - 1000
    
    logs = w3.eth.get_logs({
        'address': cowswap_address,
        'fromBlock': recent_block,
        'toBlock': current_block
    })
    
    logger.info(f"Found {len(logs)} CowSwap logs")
    
    # Analyze each log
    for i, log in enumerate(logs):
        logger.info(f"\nLog {i+1}:")
        logger.info(f"  Topics: {[topic.hex() for topic in log['topics']]}")
        logger.info(f"  Data length: {len(log['data'])}")
        
        # Try to decode as different event types
        if len(log['topics']) > 0:
            event_sig = log['topics'][0].hex()
            logger.info(f"  Event signature: {event_sig}")
            
            # Check if this matches our expected signature
            expected_sig = '0xd78ad95fa46c994b6551d0da85fc275fe613ce3b7d2a7c2c2cfd7c6c3b7aadb3'
            if event_sig == expected_sig:
                logger.info("  ✓ Matches expected CowSwap trade signature")
            else:
                logger.info("  ✗ Does not match expected signature")

def analyze_zerox_logs():
    """Analyze 0x logs to find actual event signatures"""
    logger.info("\n=== Analyzing 0x Logs ===")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    zerox_address = '0xDef1C0ded9bec7F1a1670819833240f027b25EfF'
    
    # Get recent logs
    current_block = w3.eth.block_number
    recent_block = current_block - 1000
    
    logs = w3.eth.get_logs({
        'address': zerox_address,
        'fromBlock': recent_block,
        'toBlock': current_block
    })
    
    logger.info(f"Found {len(logs)} 0x logs")
    
    # Analyze each log
    for i, log in enumerate(logs):
        logger.info(f"\nLog {i+1}:")
        logger.info(f"  Topics: {[topic.hex() for topic in log['topics']]}")
        logger.info(f"  Data length: {len(log['data'])}")
        
        # Try to decode as different event types
        if len(log['topics']) > 0:
            event_sig = log['topics'][0].hex()
            logger.info(f"  Event signature: {event_sig}")
            
            # Check if this matches our expected signature
            expected_sig = '0x68c6fa61'  # transformERC20
            if event_sig == expected_sig:
                logger.info("  ✓ Matches expected 0x transformERC20 signature")
            else:
                logger.info("  ✗ Does not match expected signature")

def main():
    """Main function"""
    logger.info("Starting log analysis")
    
    analyze_cowswap_logs()
    analyze_zerox_logs()
    
    logger.info("Analysis complete!")

if __name__ == "__main__":
    main() 