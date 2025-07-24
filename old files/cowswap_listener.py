#!/usr/bin/env python3
"""
CowSwap Affiliate Fee Listener - Consolidated Version
Tracks ShapeShift affiliate fees from CowSwap trades across EVM chains.
"""

import os
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from web3 import Web3
from eth_abi.abi import decode as decode_abi
from web3.middleware import ExtraDataToPOAMiddleware
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BATCH_MODE = True  # Set to True to use batch log fetching

class CowSwapListener:
    def __init__(self, db_path: str = "databases/cowswap_transactions.db"):
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
                'chain_id': 1,
                'rpc_url': f'https://mainnet.infura.io/v3/{self.infura_api_key}',
                'cowswap_contract': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                'chunk_size': 1000,
                'delay': 1.0
            },
            'polygon': {
                'name': 'Polygon',
                'chain_id': 137,
                'rpc_url': f'https://polygon-mainnet.infura.io/v3/{self.infura_api_key}',
                'cowswap_contract': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'optimism': {
                'name': 'Optimism',
                'chain_id': 10,
                'rpc_url': f'https://optimism-mainnet.infura.io/v3/{self.infura_api_key}',
                'cowswap_contract': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'arbitrum': {
                'name': 'Arbitrum',
                'chain_id': 42161,
                'rpc_url': f'https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}',
                'cowswap_contract': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                'chunk_size': 2000,
                'delay': 0.5
            },
            'base': {
                'name': 'Base',
                'chain_id': 8453,
                'rpc_url': f'https://base-mainnet.infura.io/v3/{self.infura_api_key}',
                'cowswap_contract': '0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                'chunk_size': 2000,
                'delay': 0.5
            }
        }
        
        # CowSwap event signatures
        self.event_signatures = {
            'trade': '0xa07a543ab8a018198e99ca0184c93fe9050a79400a0a723441f84de1d972cc17',
            'order': '0xed99827efb37016f2275f98c4bcf71c7551c75d59e9b450f79fa32e60be672c2',
            'invalidation': '0x40338ce1a7c49204f0099533b1e9a7ee0a3d261f84974ab7af36105b8c4e9db4',
            'erc20_transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
        }

    def init_database(self):
        """Initialize the database with CowSwap transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cowswap_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                owner TEXT,
                sell_token TEXT,
                buy_token TEXT,
                sell_amount TEXT,
                buy_amount TEXT,
                fee_amount TEXT,
                order_uid TEXT,
                app_data TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain, event_type)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ CowSwap database initialized: {self.db_path}")

    def get_web3_connection(self, chain_config: Dict) -> Optional[Web3]:
        """Get Web3 connection for a chain"""
        try:
            w3 = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
            # Add POA middleware for Polygon, Arbitrum, and Base
            if chain_config['chain_id'] in [137, 42161, 8453]:
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            if w3.is_connected():
                return w3
            else:
                logger.error(f"Failed to connect to {chain_config['name']}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to {chain_config['name']}: {e}")
            return None

    def get_block_timestamp(self, w3, block_number):
        try:
            block = w3.eth.get_block(block_number)
            return block['timestamp']
        except Exception:
            return None

    def fetch_cowswap_events(self, chain_name: str, blocks_to_scan: int = 2000, start_block: int = None, end_block: int = None) -> List[Dict]:
        """Fetch CowSwap events for a specific chain (batch mode if enabled)"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)
        if not w3:
            return []
        latest_block = w3.eth.block_number
        if start_block is not None and end_block is not None:
            scan_start = start_block
            scan_end = end_block
        else:
            scan_end = latest_block
            scan_start = max(latest_block - blocks_to_scan, 0)
        # Fetch block timestamps for range
        start_ts = self.get_block_timestamp(w3, scan_start)
        end_ts = self.get_block_timestamp(w3, scan_end)
        from datetime import datetime
        start_dt = datetime.utcfromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S') if start_ts else 'N/A'
        end_dt = datetime.utcfromtimestamp(end_ts).strftime('%Y-%m-%d %H:%M:%S') if end_ts else 'N/A'
        print(f'🔍 Scanning {chain_name.capitalize()} CowSwap blocks {scan_start} to {scan_end} ({start_dt} UTC to {end_dt} UTC)')
        try:
            latest_block = w3.eth.block_number
            start_block = latest_block - blocks_to_scan
            logger.info(f"🔍 Scanning {chain_config['name']} CowSwap blocks {start_block} to {latest_block}")
            events = []
            if BATCH_MODE:
                # Batch fetch only relevant logs (trade event)
                try:
                    logs = w3.eth.get_logs({
                        'fromBlock': start_block,
                        'toBlock': latest_block,
                        'address': chain_config['cowswap_contract'],
                        'topics': [self.event_signatures['trade']]
                    })
                    logger.info(f"   📦 Fetched {len(logs)} trade logs in batch mode.")
                    logs_by_tx = {}
                    for log in logs:
                        tx_hash = log['transactionHash'].hex()
                        logs_by_tx.setdefault(tx_hash, []).append(log)
                    logger.info(f"   📦 {len(logs_by_tx)} unique transactions found.")
                    for tx_hash, tx_logs in logs_by_tx.items():
                        try:
                            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
                            block = w3.eth.get_block(tx_receipt['blockNumber'])
                            # Only process if affiliate is involved
                            affiliate_address = self.shapeshift_affiliates.get(chain_config['chain_id'])
                            has_affiliate_transfer = False
                            for receipt_log in tx_receipt['logs']:
                                if (len(receipt_log['topics']) >= 3 and 
                                    receipt_log['topics'][0].hex() == self.event_signatures['erc20_transfer']):
                                    to_address = '0x' + receipt_log['topics'][2][-40:].hex()
                                    if to_address.lower() == affiliate_address.lower():
                                        has_affiliate_transfer = True
                                        break
                            if not has_affiliate_transfer:
                                continue
                            # Parse event
                            for log in tx_logs:
                                event_data = self.parse_cowswap_event(log, w3, chain_config)
                                if event_data:
                                    event_data['chain'] = chain_config['name']
                                    event_data['block_timestamp'] = block['timestamp']
                                    events.append(event_data)
                        except Exception as e:
                            logger.error(f"Error processing tx {tx_hash}: {e}")
                    return events
                except Exception as e:
                    logger.error(f"Error in batch log fetching: {e}")
                    return []
            else:
                # Legacy chunked mode
                current_block = start_block
                chunk_size = chain_config['chunk_size']
                while current_block <= latest_block:
                    end_block = min(current_block + chunk_size - 1, latest_block)
                    try:
                        filter_params = {
                            'fromBlock': current_block,
                            'toBlock': end_block,
                            'address': chain_config['cowswap_contract']
                        }
                        logs = w3.eth.get_logs(filter_params)
                        for log in logs:
                            if not log['topics']:
                                continue
                            event_sig = log['topics'][0].hex()
                            if event_sig in self.event_signatures.values():
                                block = w3.eth.get_block(log['blockNumber'])
                                event_data = self.parse_cowswap_event(log, w3, chain_config)
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
            logger.error(f"Error fetching CowSwap events for {chain_name}: {e}")
            return []

    def parse_cowswap_event(self, log, w3: Web3, chain_config: Dict) -> Optional[Dict]:
        """Parse a CowSwap Trade event and extract affiliate fee info"""
        try:
            event_sig = log['topics'][0].hex()
            if event_sig != self.event_signatures['trade']:
                return None
            # Trade event ABI
            trade_event_types = [
                'address',    # owner (indexed)
                'address',    # sellToken
                'address',    # buyToken
                'uint256',    # sellAmount
                'uint256',    # buyAmount
                'uint256',    # feeAmount
                'bytes32'     # orderUid
            ]
            # Decode data (skip topic0, topic1 is owner)
            data_bytes = bytes.fromhex(log['data'][2:]) if log['data'].startswith('0x') else bytes.fromhex(log['data'])
            decoded = decode_abi(trade_event_types[1:], data_bytes)
            sell_token = decoded[0]
            buy_token = decoded[1]
            sell_amount = decoded[2]
            buy_amount = decoded[3]
            fee_amount = decoded[4]
            order_uid = decoded[5]
            # Extract affiliate address from last 20 bytes of orderUid
            affiliate_address = '0x' + order_uid.hex()[-40:]
            ss_affiliate = self.shapeshift_affiliates.get(chain_config['chain_id']).lower()
            if affiliate_address.lower() != ss_affiliate:
                logger.debug(f"Skipping tx {log['transactionHash'].hex()} - affiliate address {affiliate_address} does not match ShapeShift {ss_affiliate}")
                return None
            # Owner is in topic1
            owner = '0x' + log['topics'][1].hex()[-40:]
            event_data = {
                'tx_hash': log['transactionHash'].hex(),
                'block_number': log['blockNumber'],
                'event_type': 'trade',
                'owner': owner,
                'sell_token': sell_token,
                'buy_token': buy_token,
                'sell_amount': str(sell_amount),
                'buy_amount': str(buy_amount),
                'fee_amount': str(fee_amount),
                'order_uid': order_uid.hex(),
                'app_data': None,  # Can be extracted if needed
                'affiliate_fee_usd': 0.0,  # To be calculated with price data
                'volume_usd': 0.0
            }
            logger.info(f"   ✅ Found ShapeShift CowSwap trade: {log['transactionHash'].hex()} | Affiliate: {affiliate_address} | Fee: {fee_amount}")
            return event_data
        except Exception as e:
            logger.error(f"Error parsing CowSwap Trade event: {e}")
            return None

    def save_events_to_db(self, events: List[Dict]):
        """Save events to database"""
        if not events:
            logger.info("No events to save to database.")
            return
        logger.info(f"Attempting to save {len(events)} events to database.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO cowswap_transactions 
                    (chain, tx_hash, block_number, block_timestamp, event_type, owner,
                     sell_token, buy_token, sell_amount, buy_amount, fee_amount,
                     order_uid, app_data, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['chain'], event['tx_hash'], event['block_number'],
                    event['block_timestamp'], event['event_type'], event['owner'],
                    event['sell_token'], event['buy_token'], event['sell_amount'],
                    event['buy_amount'], event['fee_amount'], event['order_uid'],
                    event['app_data'], event['affiliate_fee_usd'], event['volume_usd']
                ))
            except Exception as e:
                logger.error(f"Error saving event {event.get('tx_hash', 'UNKNOWN')}: {e}")
                
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {len(events)} CowSwap events to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cowswap_transactions")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT chain) FROM cowswap_transactions")
        unique_chains = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM cowswap_transactions")
        total_fees = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(volume_usd) FROM cowswap_transactions")
        total_volume = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM cowswap_transactions WHERE event_type = 'trade'")
        trade_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 CowSwap Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Trade events: {trade_count}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the CowSwap listener for all chains"""
        logger.info("🚀 Starting CowSwap affiliate fee listener")
        
        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_cowswap_events(chain_name, blocks_to_scan)
            logger.info(f"Fetched {len(events)} events for {chain_name}.")
            self.save_events_to_db(events)
            total_events += len(events)
            
        logger.info(f"\n✅ CowSwap listener completed! Found {total_events} total events")
        self.get_database_stats()

    def process_shapeshift_affiliate_trades(self, affiliate_trades):
        """After finding ShapeShift affiliate trades, decode and print enriched trade details for each tx."""
        decoder_script = os.path.join(os.path.dirname(__file__), '../scripts/debug/decode_cowswap_settlement_log.py')
        for trade in affiliate_trades:
            tx_hash = trade.get('tx_hash')
            if tx_hash:
                print(f'\n=== Decoding enriched CowSwap trade for tx {tx_hash} ===')
                try:
                    subprocess.run(['python', decoder_script, tx_hash], check=True)
                except Exception as e:
                    print(f'Error running decoder for {tx_hash}: {e}')

    def print_log_topics(self, chain_name: str, tx_hash: str):
        """Print all log topics and their hex values for a transaction hash"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)
        if not w3:
            print(f"Could not connect to {chain_name}")
            return
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            print(f"\nAll log topics for tx {tx_hash}:")
            for i, log in enumerate(receipt['logs']):
                print(f"Log #{i}: address={log['address']}")
                for j, topic in enumerate(log['topics']):
                    print(f"  Topic {j}: {topic.hex()}")
        except Exception as e:
            print(f"Error fetching transaction {tx_hash}: {e}")

    def scan_specific_tx(self, chain_name: str, tx_hash: str):
        """Scan and decode a specific transaction hash for a CowSwap affiliate trade"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)
        if not w3:
            print(f"Could not connect to {chain_name}")
            return
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            found_trade = False
            for log in receipt['logs']:
                if log['topics'] and log['topics'][0].hex() == self.event_signatures['trade']:
                    found_trade = True
                    print(f"\n--- Decoding Trade event in tx {tx_hash} ---")
                    try:
                        # Decode as in parse_cowswap_event
                        trade_event_types = [
                            'address',    # owner (indexed)
                            'address',    # sellToken
                            'address',    # buyToken
                            'uint256',    # sellAmount
                            'uint256',    # buyAmount
                            'uint256',    # feeAmount
                            'bytes32'     # orderUid
                        ]
                        data_bytes = bytes.fromhex(log['data'][2:]) if log['data'].startswith('0x') else bytes.fromhex(log['data'])
                        decoded = decode_abi(trade_event_types[1:], data_bytes)
                        sell_token = decoded[0]
                        buy_token = decoded[1]
                        sell_amount = decoded[2]
                        buy_amount = decoded[3]
                        fee_amount = decoded[4]
                        order_uid = decoded[5]
                        affiliate_address = '0x' + order_uid.hex()[-40:]
                        ss_affiliate = self.shapeshift_affiliates.get(chain_config['chain_id']).lower()
                        owner = '0x' + log['topics'][1].hex()[-40:]
                        event_data = {
                            'tx_hash': log['transactionHash'].hex(),
                            'block_number': log['blockNumber'],
                            'event_type': 'trade',
                            'owner': owner,
                            'sell_token': sell_token,
                            'buy_token': buy_token,
                            'sell_amount': str(sell_amount),
                            'buy_amount': str(buy_amount),
                            'fee_amount': str(fee_amount),
                            'order_uid': order_uid.hex(),
                            'affiliate_address': affiliate_address,
                            'app_data': None,
                            'affiliate_fee_usd': 0.0,
                            'volume_usd': 0.0
                        }
                        print(json.dumps(event_data, indent=2))
                        if affiliate_address.lower() == ss_affiliate:
                            print(f"✅ ShapeShift affiliate match: {affiliate_address}")
                        else:
                            print(f"❌ Not a ShapeShift affiliate: {affiliate_address}")
                    except Exception as e:
                        print(f"Error decoding trade event: {e}")
            if not found_trade:
                print(f"No Trade event found in tx {tx_hash}")
                self.print_log_topics(chain_name, tx_hash)
        except Exception as e:
            print(f"Error fetching transaction {tx_hash}: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CowSwap Affiliate Fee Listener')
    parser.add_argument('--blocks', type=int, default=2000, help='Number of blocks to scan')
    parser.add_argument('--start-block', type=int, help='Start block number (overrides --blocks)')
    parser.add_argument('--end-block', type=int, help='End block number (overrides --blocks)')
    parser.add_argument('--scan-tx', nargs=2, metavar=('CHAIN', 'TX_HASH'), help='Scan a specific tx for affiliate trade (chain, tx_hash)')
    args = parser.parse_args()
    
    listener = CowSwapListener()
    if args.scan_tx:
        chain, tx_hash = args.scan_tx
        listener.scan_specific_tx(chain, tx_hash)
    else:
        # Pass start/end block if provided
        for chain_name in listener.chains:
            listener.fetch_cowswap_events(chain_name, blocks_to_scan=args.blocks, start_block=args.start_block, end_block=args.end_block)
        listener.get_database_stats()

if __name__ == "__main__":
    main() 