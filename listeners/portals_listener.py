#!/usr/bin/env python3
"""
Portals Affiliate Fee Listener - Consolidated Version
Collects Portals affiliate fee data from EVM chains for ShapeShift affiliate tracking.
"""

import os
import sqlite3
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PortalsListener:
    def __init__(self, db_path: str = "databases/portals_transactions.db"):
        self.db_path = db_path
        self.infura_api_key = os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')
        self.init_database()
        
        # ShapeShift affiliate addresses by chain
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",      # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",     # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",      # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",   # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",    # Base
        }
        
        # Chain configurations
        self.chains = {
            'ethereum': {
                'name': 'Ethereum',
                'rpc_url': f'https://mainnet.infura.io/v3/{self.infura_api_key}',
                'chain_id': 1,
                'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
                'start_block': 22700000,
                'chunk_size': 100,
                'delay': 1.0
            },
            'polygon': {
                'name': 'Polygon', 
                'rpc_url': f'https://polygon-mainnet.infura.io/v3/{self.infura_api_key}',
                'chain_id': 137,
                'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
                'start_block': 45000000,
                'chunk_size': 200,
                'delay': 0.5
            },
            'arbitrum': {
                'name': 'Arbitrum',
                'rpc_url': f'https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}',
                'chain_id': 42161,
                'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
                'start_block': 70000000,
                'chunk_size': 200,
                'delay': 0.5
            },
            'optimism': {
                'name': 'Optimism',
                'rpc_url': f'https://optimism-mainnet.infura.io/v3/{self.infura_api_key}',
                'chain_id': 10,
                'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
                'start_block': 85000000,
                'chunk_size': 200,
                'delay': 0.5
            },
            'base': {
                'name': 'Base',
                'rpc_url': f'https://base-mainnet.infura.io/v3/{self.infura_api_key}',
                'chain_id': 8453,
                'portals_router': '0xbf5A7F3629fB325E2a8453D595AB103465F75E62',
                'start_block': 5000000,
                'chunk_size': 200,
                'delay': 0.5
            }
        }

    def init_database(self):
        """Initialize the database with portals transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portals_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_timestamp INTEGER NOT NULL,
                input_token TEXT,
                input_amount TEXT,
                output_token TEXT,
                output_amount TEXT,
                sender TEXT,
                broadcaster TEXT,
                recipient TEXT,
                partner TEXT,
                affiliate_token TEXT,
                affiliate_amount TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_web3_connection(self, chain_config: Dict) -> Optional[Web3]:
        """Get Web3 connection for a chain"""
        try:
            w3 = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
            if w3.is_connected():
                return w3
            else:
                logger.error(f"Failed to connect to {chain_config['name']}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to {chain_config['name']}: {e}")
            return None

    def fetch_portals_events(self, chain_name: str, blocks_to_scan: int = 2000) -> List[Dict]:
        """Fetch Portals events for a specific chain"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)
        
        if not w3:
            return []
            
        try:
            latest_block = w3.eth.block_number
            start_block = max(chain_config['start_block'], latest_block - blocks_to_scan)
            
            logger.info(f"🔍 Scanning {chain_config['name']} blocks {start_block} to {latest_block}")
            
            # Portal event signature
            portal_topic = "0x9f69056fe2b57cf4ad9c5cdfd096e91b7b99ce05e44f6ed446ae6a3d6b5c0a1e"
            
            events = []
            current_block = start_block
            chunk_size = chain_config['chunk_size']
            
            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)
                
                try:
                    filter_params = {
                        'fromBlock': current_block,
                        'toBlock': end_block,
                        'address': chain_config['portals_router'],
                        'topics': [portal_topic]
                    }
                    
                    logs = w3.eth.get_logs(filter_params)
                    
                    for log in logs:
                        # Check if this involves ShapeShift affiliate
                        tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
                        shapeshift_affiliate = self.shapeshift_affiliates.get(chain_config['chain_id'])
                        
                        if any(shapeshift_affiliate.lower() in str(topic).lower() for topic in log['topics']):
                            block = w3.eth.get_block(log['blockNumber'])
                            
                            event_data = {
                                'chain': chain_config['name'],
                                'tx_hash': log['transactionHash'].hex(),
                                'block_number': log['blockNumber'],
                                'block_timestamp': block['timestamp'],
                                'input_token': None,
                                'input_amount': None,
                                'output_token': None,
                                'output_amount': None,
                                'sender': None,
                                'broadcaster': None,
                                'recipient': None,
                                'partner': shapeshift_affiliate,
                                'affiliate_token': None,
                                'affiliate_amount': None,
                                'affiliate_fee_usd': 0.0,
                                'volume_usd': 0.0
                            }
                            
                            events.append(event_data)
                            logger.info(f"   ✅ Found ShapeShift affiliate event: {log['transactionHash'].hex()}")
                    
                    if current_block % 10000 == 0:
                        logger.info(f"   📊 Processed {current_block - start_block} blocks...")
                    
                    current_block = end_block + 1
                    time.sleep(chain_config['delay'])
                    
                except Exception as e:
                    logger.error(f"Error fetching logs for blocks {current_block}-{end_block}: {e}")
                    current_block = end_block + 1
                    continue
                    
            return events
            
        except Exception as e:
            logger.error(f"Error fetching Portals events for {chain_name}: {e}")
            return []

    def save_events_to_db(self, events: List[Dict]):
        """Save events to database"""
        if not events:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO portals_transactions 
                    (chain, tx_hash, block_number, block_timestamp, input_token, input_amount,
                     output_token, output_amount, sender, broadcaster, recipient, partner,
                     affiliate_token, affiliate_amount, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['chain'], event['tx_hash'], event['block_number'], 
                    event['block_timestamp'], event['input_token'], event['input_amount'],
                    event['output_token'], event['output_amount'], event['sender'],
                    event['broadcaster'], event['recipient'], event['partner'],
                    event['affiliate_token'], event['affiliate_amount'],
                    event['affiliate_fee_usd'], event['volume_usd']
                ))
            except Exception as e:
                logger.error(f"Error saving event {event['tx_hash']}: {e}")
                
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {len(events)} Portals events to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM portals_transactions")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT chain) FROM portals_transactions")
        unique_chains = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM portals_transactions")
        total_fees = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(volume_usd) FROM portals_transactions")
        total_volume = cursor.fetchone()[0] or 0
        
        conn.close()
        
        print(f"\n📊 Portals Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the Portals listener for all chains"""
        logger.info("🚀 Starting Portals affiliate fee listener")
        
        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_portals_events(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)
            
        logger.info(f"\n✅ Portals listener completed! Found {total_events} total events")
        self.get_database_stats()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portals Affiliate Fee Listener')
    parser.add_argument('--blocks', type=int, default=2000, help='Number of blocks to scan')
    args = parser.parse_args()
    
    listener = PortalsListener()
    listener.run_listener(args.blocks)

if __name__ == "__main__":
    main() 