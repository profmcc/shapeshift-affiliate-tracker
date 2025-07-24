#!/usr/bin/env python3
"""
0x Protocol Affiliate Fee Listener - Consolidated Version
Tracks ShapeShift affiliate fees from 0x Protocol swaps across EVM chains.
"""

import os
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from web3 import Web3
from eth_abi import decode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZeroXListener:
    def __init__(self, db_path: str = "databases/zerox_transactions.db"):
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
            43114: "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche
            56: "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"       # BSC
        }
        
        # Chain configurations
        self.chains = {
            'ethereum': {
                'name': 'Ethereum',
                'chain_id': 1,
                'rpc_url': f'https://mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 1000,
                'delay': 1.0
            },
            'polygon': {
                'name': 'Polygon',
                'chain_id': 137,
                'rpc_url': f'https://polygon-mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'optimism': {
                'name': 'Optimism',
                'chain_id': 10,
                'rpc_url': f'https://optimism-mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'arbitrum': {
                'name': 'Arbitrum',
                'chain_id': 42161,
                'rpc_url': f'https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'base': {
                'name': 'Base',
                'chain_id': 8453,
                'rpc_url': f'https://base-mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'avalanche': {
                'name': 'Avalanche',
                'chain_id': 43114,
                'rpc_url': f'https://avalanche-mainnet.infura.io/v3/{self.infura_api_key}',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'bsc': {
                'name': 'BSC',
                'chain_id': 56,
                'rpc_url': 'https://bsc-dataseed.binance.org',
                'zerox_contract': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
                'chunk_size': 2000,
                'delay': 0.5
            }
        }
        
        # 0x Protocol event signatures
        self.event_signatures = {
            'fill': '0x50273fa02273cceea9cf085b42de5c8af60624140168bd71357db833535877af',
            'cancel': '0xa015ad2dc32f266993958a0fd9884c746b971b254206f3478bc43e2f125c7b9e',
            'transform_erc20': '0x68c6fa61',  # Function signature for transformERC20
            'erc20_transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
        }

    def init_database(self):
        """Initialize the database with 0x transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zerox_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                maker TEXT,
                taker TEXT,
                input_token TEXT,
                output_token TEXT,
                input_amount TEXT,
                output_amount TEXT,
                protocol_fee TEXT,
                affiliate_fee_amount TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain, event_type)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ 0x Protocol database initialized: {self.db_path}")

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

    def fetch_zerox_events(self, chain_name: str, blocks_to_scan: int = 2000) -> List[Dict]:
        """Fetch 0x Protocol events for a specific chain"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)
        
        if not w3:
            return []
            
        try:
            latest_block = w3.eth.block_number
            start_block = latest_block - blocks_to_scan
            
            logger.info(f"🔍 Scanning {chain_config['name']} 0x Protocol blocks {start_block} to {latest_block}")
            
            events = []
            current_block = start_block
            chunk_size = chain_config['chunk_size']
            
            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)
                
                try:
                    # Fetch all 0x Protocol events
                    filter_params = {
                        'fromBlock': current_block,
                        'toBlock': end_block,
                        'address': chain_config['zerox_contract']
                    }
                    
                    logs = w3.eth.get_logs(filter_params)
                    
                    for log in logs:
                        if not log['topics']:
                            continue
                            
                        event_sig = log['topics'][0].hex()
                        
                        # Process different 0x events
                        if event_sig in self.event_signatures.values():
                            block = w3.eth.get_block(log['blockNumber'])
                            
                            event_data = self.parse_zerox_event(log, w3, chain_config)
                            if event_data:
                                event_data['chain'] = chain_config['name']
                                event_data['block_timestamp'] = block['timestamp']
                                events.append(event_data)
                    
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
            logger.error(f"Error fetching 0x Protocol events for {chain_name}: {e}")
            return []

    def parse_zerox_event(self, log, w3: Web3, chain_config: Dict) -> Optional[Dict]:
        """Parse a 0x Protocol event"""
        try:
            event_sig = log['topics'][0].hex()
            affiliate_address = self.shapeshift_affiliates.get(chain_config['chain_id'])
            
            # Check if ShapeShift is involved
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            
            # Look for transfers to ShapeShift affiliate address
            has_affiliate_transfer = False
            affiliate_amount = 0
            
            for receipt_log in tx_receipt['logs']:
                if (len(receipt_log['topics']) >= 3 and 
                    receipt_log['topics'][0].hex() == self.event_signatures['erc20_transfer']):
                    
                    to_address = '0x' + receipt_log['topics'][2][-40:].hex()
                    if to_address.lower() == affiliate_address.lower():
                        has_affiliate_transfer = True
                        # Extract affiliate fee amount
                        try:
                            affiliate_amount = int(receipt_log['data'], 16)
                        except:
                            affiliate_amount = 0
                        break
            
            if not has_affiliate_transfer:
                return None
                
            # Determine event type
            event_type = 'unknown'
            if event_sig == self.event_signatures['fill']:
                event_type = 'fill'
            elif event_sig == self.event_signatures['cancel']:
                event_type = 'cancel'
            
            # Basic event data structure
            event_data = {
                'tx_hash': log['transactionHash'].hex(),
                'block_number': log['blockNumber'],
                'event_type': event_type,
                'maker': None,
                'taker': None,
                'input_token': None,
                'output_token': None,
                'input_amount': None,
                'output_amount': None,
                'protocol_fee': None,
                'affiliate_fee_amount': str(affiliate_amount),
                'affiliate_fee_usd': 0.0,
                'volume_usd': 0.0
            }
            
            # Try to decode event data (simplified)
            if len(log['topics']) > 1:
                try:
                    # Basic decoding for Fill events
                    if event_type == 'fill' and len(log['data']) > 0:
                        data = log['data']
                        # Simplified data extraction - would need proper ABI for full decoding
                        if len(data) > 130:
                            event_data['input_amount'] = str(int(data[2:66], 16))
                            event_data['output_amount'] = str(int(data[66:130], 16))
                            
                    # Extract maker/taker from topics if available
                    if len(log['topics']) >= 3:
                        event_data['maker'] = '0x' + log['topics'][1][-40:].hex()
                        event_data['taker'] = '0x' + log['topics'][2][-40:].hex()
                        
                except Exception as e:
                    logger.debug(f"Error decoding event data: {e}")
            
            logger.info(f"   ✅ Found ShapeShift 0x {event_type}: {log['transactionHash'].hex()} (${affiliate_amount/1e18:.4f} fee)")
            return event_data
            
        except Exception as e:
            logger.error(f"Error parsing 0x Protocol event: {e}")
            return None

    def save_events_to_db(self, events: List[Dict]):
        """Save events to database"""
        if not events:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO zerox_transactions 
                    (chain, tx_hash, block_number, block_timestamp, event_type, maker, taker,
                     input_token, output_token, input_amount, output_amount, protocol_fee,
                     affiliate_fee_amount, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['chain'], event['tx_hash'], event['block_number'],
                    event['block_timestamp'], event['event_type'], event['maker'], event['taker'],
                    event['input_token'], event['output_token'], event['input_amount'],
                    event['output_amount'], event['protocol_fee'], event['affiliate_fee_amount'],
                    event['affiliate_fee_usd'], event['volume_usd']
                ))
            except Exception as e:
                logger.error(f"Error saving event {event['tx_hash']}: {e}")
                
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {len(events)} 0x Protocol events to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM zerox_transactions")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT chain) FROM zerox_transactions")
        unique_chains = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM zerox_transactions")
        total_fees = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(volume_usd) FROM zerox_transactions")
        total_volume = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM zerox_transactions WHERE event_type = 'fill'")
        fill_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 0x Protocol Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Fill events: {fill_count}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the 0x Protocol listener for all chains"""
        logger.info("🚀 Starting 0x Protocol affiliate fee listener")
        
        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_zerox_events(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)
            
        logger.info(f"\n✅ 0x Protocol listener completed! Found {total_events} total events")
        self.get_database_stats()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='0x Protocol Affiliate Fee Listener')
    parser.add_argument('--blocks', type=int, default=2000, help='Number of blocks to scan')
    args = parser.parse_args()
    
    listener = ZeroXListener()
    listener.run_listener(args.blocks)

if __name__ == "__main__":
    main() 