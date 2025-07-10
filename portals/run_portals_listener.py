#!/usr/bin/env python3
"""
Portals Affiliate Fee Listener
Collects Portals affiliate fee data from EVM chains (Ethereum, Polygon, Arbitrum, etc.)
"""

import os
import sqlite3
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'portals_affiliate_events.db'
INFURA_API_KEY = os.getenv('INFURA_API_KEY', 'your_infura_api_key_here')

# Chain configurations with rate limiting considerations
CHAINS = {
    'ethereum': {
        'name': 'Ethereum',
        'rpc_url': f'https://mainnet.infura.io/v3/{INFURA_API_KEY}',
        'chain_id': 1,
        'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'start_block': 22700000,  # Expand block range to find more events
        'latest_block': None,
        'chunk_size': 100,  # Smaller chunks for rate limiting
        'delay': 1.0  # Longer delay between requests
    },
    'polygon': {
        'name': 'Polygon',
        'rpc_url': f'https://polygon-mainnet.infura.io/v3/{INFURA_API_KEY}',
        'chain_id': 137,
        'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'start_block': 45000000,
        'latest_block': None,
        'chunk_size': 200,
        'delay': 0.5
    },
    'arbitrum': {
        'name': 'Arbitrum',
        'rpc_url': f'https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}',
        'chain_id': 42161,
        'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'start_block': 120000000,
        'latest_block': None,
        'chunk_size': 500,
        'delay': 0.3
    },
    'optimism': {
        'name': 'Optimism',
        'rpc_url': f'https://optimism-mainnet.infura.io/v3/{INFURA_API_KEY}',
        'chain_id': 10,
        'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'start_block': 110000000,
        'latest_block': None,
        'chunk_size': 500,
        'delay': 0.3
    },
    'base': {
        'name': 'Base',
        'rpc_url': f'https://base-mainnet.infura.io/v3/{INFURA_API_KEY}',
        'chain_id': 8453,
        'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
        'start_block': 5000000,
        'latest_block': None,
        'chunk_size': 500,
        'delay': 0.3
    }
}

# Event signature for Portals Portal event
PORTALS_PORTAL_EVENT = '0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03'

def init_database():
    """Initialize the Portals database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Portals affiliate events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portals_affiliate_events2 (
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
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_portals_tx_hash 
        ON portals_affiliate_events2(tx_hash)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_portals_block_number 
        ON portals_affiliate_events2(block_number)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Portals database initialized")

def make_rpc_request(url: str, payload: Dict, max_retries: int = 3) -> Optional[Dict]:
    """Make RPC request with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 429:
                # Rate limited - wait longer
                wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                logger.warning(f"Rate limited, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"RPC request failed after {max_retries} attempts: {e}")
                return None
            else:
                wait_time = (2 ** attempt) * 1
                logger.warning(f"Request failed, retrying in {wait_time} seconds: {e}")
                time.sleep(wait_time)
    
    return None

def get_latest_block(chain_config: Dict) -> int:
    """Get the latest block number for a chain"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    
    result = make_rpc_request(chain_config['rpc_url'], payload)
    if result and 'result' in result:
        return int(result['result'], 16)
    else:
        logger.error(f"Error getting latest block for {chain_config['name']}")
        return chain_config['start_block']

def get_last_processed_block(chain_name: str) -> int:
    """Get the last processed block for a chain"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT MAX(block_number) 
            FROM portals_affiliate_events2 
            WHERE tx_hash IN (
                SELECT tx_hash FROM portals_affiliate_events2 
                WHERE block_number IS NOT NULL
            )
        ''')
        
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            return CHAINS[chain_name]['start_block']
            
    except Exception as e:
        logger.error(f"Error getting last processed block: {e}")
        return CHAINS[chain_name]['start_block']
    finally:
        conn.close()

def fetch_portals_events(chain_config: Dict, start_block: int, end_block: int) -> List[Dict]:
    """Fetch Portals events from a block range"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "address": chain_config['portals_router'],
            "topics": [PORTALS_PORTAL_EVENT],
            "fromBlock": hex(start_block),
            "toBlock": hex(end_block)
        }],
        "id": 1
    }
    
    result = make_rpc_request(chain_config['rpc_url'], payload)
    if result and 'result' in result:
        return result['result']
    else:
        logger.error(f"Error fetching Portals events for blocks {start_block}-{end_block}")
        return []

def parse_portals_event(event: Dict, chain_config: Dict) -> Optional[Dict]:
    """Parse a Portals event and extract affiliate fee data"""
    try:
        # The Portals event signature is: Portal(address inputToken, uint256 inputAmount, address outputToken, uint256 outputAmount, address sender, address broadcaster, address recipient, address partner)
        # Based on actual transaction analysis
        
        # Remove the event signature from topics
        topics = event.get('topics', [])
        if len(topics) < 4:  # Need event signature + 3 indexed parameters
            return None
            
        # The data field contains the non-indexed parameters
        data = event.get('data', '')
        if not data or len(data) < 2:
            return None
            
        # Remove '0x' prefix
        data = data[2:]
        
        # Each parameter is 32 bytes (64 hex characters)
        param_length = 64
        
        # Parse the non-indexed parameters from data
        params = []
        for i in range(0, len(data), param_length):
            if i + param_length <= len(data):
                params.append(data[i:i + param_length])
        
        if len(params) < 5:  # We need inputToken, inputAmount, outputToken, outputAmount, recipient
            return None
            
        # Extract non-indexed parameters from data
        input_token = '0x' + params[0][-40:]  # Last 20 bytes
        input_amount = int(params[1], 16)
        output_token = '0x' + params[2][-40:]
        output_amount = int(params[3], 16)
        recipient = '0x' + params[4][-40:]
        
        # Extract indexed parameters from topics
        # Topics[0] = event signature
        # Topics[1] = sender (indexed)
        # Topics[2] = broadcaster (indexed) 
        # Topics[3] = partner (indexed)
        
        sender = '0x' + topics[1][-40:]
        broadcaster = '0x' + topics[2][-40:]
        partner = '0x' + topics[3][-40:]
        
        # Get block timestamp
        block_number = int(event.get('blockNumber', '0'), 16)
        timestamp = get_block_timestamp(block_number, chain_config)
        
        return {
            'tx_hash': event.get('transactionHash', ''),
            'block_number': block_number,
            'input_token': input_token,
            'input_amount': str(input_amount),
            'output_token': output_token,
            'output_amount': str(output_amount),
            'sender': sender,
            'broadcaster': broadcaster,
            'recipient': recipient,
            'partner': partner,
            'timestamp': timestamp,
            'affiliate_token': '',  # No affiliate token in Portals event
            'affiliate_amount': ''  # No affiliate amount in Portals event
        }
        
    except Exception as e:
        logger.error(f"Error parsing Portals event: {e}")
        return None

def get_block_timestamp(block_number: int, chain_config: Dict) -> int:
    """Get block timestamp"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_number), False],
        "id": 1
    }
    
    result = make_rpc_request(chain_config['rpc_url'], payload)
    if result and 'result' in result and result['result']:
        return int(result['result']['timestamp'], 16)
    else:
        return int(time.time())

def store_portals_events(events: List[Dict]):
    """Store Portals events in the database"""
    if not events:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for event in events:
            cursor.execute('''
                INSERT OR IGNORE INTO portals_affiliate_events2 
                (tx_hash, block_number, input_token, input_amount, output_token, output_amount,
                 sender, broadcaster, recipient, partner, timestamp, affiliate_token, affiliate_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['tx_hash'],
                event['block_number'],
                event['input_token'],
                event['input_amount'],
                event['output_token'],
                event['output_amount'],
                event['sender'],
                event['broadcaster'],
                event['recipient'],
                event['partner'],
                event['timestamp'],
                event['affiliate_token'],
                event['affiliate_amount']
            ))
        
        conn.commit()
        logger.info(f"Stored {len(events)} Portals events")
        
    except Exception as e:
        logger.error(f"Error storing Portals events: {e}")
    finally:
        conn.close()

def process_chain(chain_name: str, chain_config: Dict, max_blocks: int = 5000):
    """Process a single chain for Portals events with rate limiting"""
    logger.info(f"Processing {chain_config['name']}...")
    
    # Get latest block
    latest_block = get_latest_block(chain_config)
    chain_config['latest_block'] = latest_block
    
    # Get last processed block
    last_processed = get_last_processed_block(chain_name)
    
    # Limit processing to avoid overwhelming the API
    end_block = min(last_processed + max_blocks, latest_block)
    
    if last_processed >= end_block:
        logger.info(f"{chain_config['name']}: No new blocks to process")
        return
    
    logger.info(f"{chain_config['name']}: Processing blocks {last_processed + 1} to {end_block}")
    
    # Process in chunks with rate limiting
    chunk_size = chain_config.get('chunk_size', 100)
    delay = chain_config.get('delay', 1.0)
    total_events = 0
    
    for start_block in range(last_processed + 1, end_block + 1, chunk_size):
        end_chunk = min(start_block + chunk_size - 1, end_block)
        
        logger.info(f"{chain_config['name']}: Processing blocks {start_block}-{end_chunk}")
        
        # Fetch events
        events = fetch_portals_events(chain_config, start_block, end_chunk)
        
        if events:
            # Parse events
            parsed_events = []
            for event in events:
                parsed = parse_portals_event(event, chain_config)
                if parsed:
                    parsed_events.append(parsed)
            
            # Store events
            if parsed_events:
                store_portals_events(parsed_events)
                total_events += len(parsed_events)
        
        # Rate limiting delay
        time.sleep(delay)
    
    logger.info(f"{chain_config['name']}: Processed {total_events} total events")

def get_database_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM portals_affiliate_events2")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tx_hash) FROM portals_affiliate_events2")
        unique_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(block_number), MAX(block_number) FROM portals_affiliate_events2")
        block_range = cursor.fetchone()
        min_block, max_block = block_range if block_range[0] else (0, 0)
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM portals_affiliate_events2")
        time_range = cursor.fetchone()
        min_time, max_time = time_range if time_range[0] else (0, 0)
        
        print(f"\n=== Portals Database Statistics ===")
        print(f"Total events: {total_events}")
        print(f"Unique transactions: {unique_transactions}")
        print(f"Block range: {min_block} - {max_block}")
        if min_time and max_time:
            print(f"Time range: {datetime.fromtimestamp(min_time)} - {datetime.fromtimestamp(max_time)}")
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
    finally:
        conn.close()

def main():
    """Main function"""
    logger.info("Starting Portals affiliate fee listener...")
    
    # Check if Infura API key is set
    if INFURA_API_KEY == 'your_infura_api_key_here':
        logger.error("Please set INFURA_API_KEY environment variable")
        return
    
    # Initialize database
    init_database()
    
    # Process each chain with limited blocks to avoid rate limits
    for chain_name, chain_config in CHAINS.items():
        try:
            # Process only a limited number of blocks per run to avoid rate limits
            max_blocks = 1000 if chain_name == 'ethereum' else 2000
            process_chain(chain_name, chain_config, max_blocks)
        except Exception as e:
            logger.error(f"Error processing {chain_name}: {e}")
    
    # Get database statistics
    get_database_stats()
    
    logger.info("Portals listener completed!")

if __name__ == "__main__":
    main() 