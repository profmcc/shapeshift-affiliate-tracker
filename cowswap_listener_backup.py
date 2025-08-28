#!/usr/bin/env python3
"""
CoW Swap Protocol Affiliate Fee Listener (Improved)
Tracks ShapeShift affiliate fees from CoW Swap order settlements
"""

import json
import csv
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CowSwapTransaction:
    protocol: str
    chain: str
    block_number: int
    tx_hash: str
    block_timestamp: int
    block_date: str
    from_address: str
    to_address: str
    user_address: str
    affiliate_address: str
    affiliate_fee_amount: str
    affiliate_fee_token: str
    affiliate_fee_usd: float
    input_token: str
    input_amount: str
    input_amount_usd: float
    output_token: str
    output_amount: str
    output_amount_usd: float
    volume_usd: float
    order_uid: str
    app_data: str
    status: str
    created_at: str
    created_date: str

class CowSwapListener:
    def __init__(self, config_path: str = "config/shapeshift_config.yaml"):
        self.config = self._load_config(config_path)
        self.chains = self._init_chains()
        self.csv_file = "csv_data/cowswap_transactions.csv"
        self.block_tracker_file = "csv_data/cowswap_block_tracker.csv"
        self.affiliate_addresses = self._load_affiliate_addresses()
        
        # CoW Swap settlement contract (same across chains)
        self.settlement_contract = Web3.to_checksum_address("0x9008d19f58aabd9ed0d60971565aa8510560ab41")
        
        # CoW Swap API endpoints
        self.api_endpoints = {
            'ethereum': 'https://api.cow.fi/mainnet/api/v1',
            'polygon': 'https://api.cow.fi/polygon/api/v1',
            'arbitrum': 'https://api.cow.fi/arbitrum/api/v1',
            'optimism': 'https://api.cow.fi/optimism/api/v1',
            'base': 'https://api.cow.fi/base/api/v1'
        }
        
        # Event signatures
        self.trade_event_sig = "0x0bcc4c97732e47d9946f229edb95f5e6320829021d42f1eec4c37c14845c8a8e"
        self.settlement_event_sig = "0xd6d4c0cd7c5c4310d8c7b8c7b2a7b7a7b7a7b7a7b7a7b7a7b7a7b7a7b7a7b7a"
        
        self._ensure_csv_files()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check if environment variables are properly expanded
            if config and 'chains' in config:
                for chain_name, chain_config in config['chains'].items():
                    if 'rpc_url' in chain_config and '${ALCHEMY_API_KEY}' in chain_config['rpc_url']:
                        logger.warning(f"Environment variables not expanded in YAML config for {chain_name}, using default config")
                        return self._default_config()
            
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration"""
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        if not alchemy_key:
            logger.warning("ALCHEMY_API_KEY not found in environment variables")
            alchemy_key = "demo"  # Fallback for testing
        
        return {
            'chains': {
                'ethereum': {
                    'chain_id': 1,
                    'rpc_url': f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 19000000
                },
                'polygon': {
                    'chain_id': 137,
                    'rpc_url': f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 50000000
                },
                'arbitrum': {
                    'chain_id': 42161,
                    'rpc_url': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 100000000
                },
                'optimism': {
                    'chain_id': 10,
                    'rpc_url': f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 10000000
                },
                'base': {
                    'chain_id': 8453,
                    'rpc_url': f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 32900000
                },
                'avalanche': {
                    'chain_id': 43114,
                    'rpc_url': "https://api.avax.network/ext/bc/C/rpc",
                    'start_block': 30000000
                },
                'bsc': {
                    'chain_id': 56,
                    'rpc_url': "https://bsc-dataseed.binance.org/",
                    'start_block': 30000000
                },
                'gnosis': {
                    'chain_id': 100,
                    'rpc_url': "https://rpc.gnosischain.com/",
                    'start_block': 30000000
                }
            },
            'shapeshift_affiliates': {
                'cowswap': '0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502'
            }
        }
    
    def _init_chains(self) -> Dict[str, Web3]:
        """Initialize Web3 connections"""
        chains = {}
        logger.info(f"Available chains in config: {list(self.config.get('chains', {}).keys())}")
        
        for chain_name, chain_config in self.config.get('chains', {}).items():
            try:
                logger.info(f"Attempting to connect to {chain_name} with RPC: {chain_config['rpc_url'][:50]}...")
                w3 = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
                if not w3.is_connected():
                    logger.warning(f"Failed to connect to {chain_name}")
                    continue
                
                if chain_name == 'polygon':
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                chains[chain_name] = w3
                logger.info(f"Connected to {chain_name}")
            except Exception as e:
                logger.error(f"Failed to initialize {chain_name}: {e}")
        
        logger.info(f"Successfully connected to chains: {list(chains.keys())}")
        return chains
    
    def _load_affiliate_addresses(self) -> List[str]:
        """Load ShapeShift affiliate addresses"""
        addresses = []
        affiliate_config = self.config.get('shapeshift_affiliates', {})
        
        for key, address in affiliate_config.items():
            if isinstance(address, str) and address.startswith('0x'):
                addresses.append(address.lower())
        
        variations = affiliate_config.get('variations', [])
        for addr in variations:
            if isinstance(addr, str) and addr.startswith('0x'):
                addresses.append(addr.lower())
        
        return list(set(addresses))
    
    def _ensure_csv_files(self):
        """Create CSV files with headers"""
        os.makedirs("csv_data", exist_ok=True)
        
        headers = [
            'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
            'from_address', 'to_address', 'user_address', 'affiliate_address',
            'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
            'input_token', 'input_amount', 'input_amount_usd',
            'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
            'order_uid', 'app_data', 'status', 'created_at', 'created_date'
        ]
        
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        tracker_headers = ['chain', 'last_processed_block', 'updated_at']
        if not os.path.exists(self.block_tracker_file):
            with open(self.block_tracker_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(tracker_headers)
    
    def get_last_processed_block(self, chain: str) -> int:
        """Get last processed block for a chain"""
        try:
            with open(self.block_tracker_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['chain'] == chain:
                        return int(row['last_processed_block'])
        except Exception:
            pass
        
        return self.config.get('chains', {}).get(chain, {}).get('start_block', 0)
    
    def update_last_processed_block(self, chain: str, block_number: int):
        """Update last processed block"""
        existing_data = {}
        try:
            with open(self.block_tracker_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_data[row['chain']] = row
        except Exception:
            pass
        
        existing_data[chain] = {
            'chain': chain,
            'last_processed_block': block_number,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.block_tracker_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['chain', 'last_processed_block', 'updated_at'])
            writer.writeheader()
            writer.writerows(existing_data.values())
    
    def get_recent_orders_from_api(self, chain_name: str, hours_back: int = 24) -> List[dict]:
        """Get recent orders from CoW Swap API"""
        if chain_name not in self.api_endpoints:
            logger.warning(f"No API endpoint for {chain_name}")
            return []
        
        try:
            api_url = self.api_endpoints[chain_name]
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Get orders endpoint
            url = f"{api_url}/orders"
            params = {
                'limit': 100,
                'offset': 0,
                'owner': '',  # We'll filter after
            }
            
            logger.info(f"Fetching orders from CoW Swap API: {url}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            orders = response.json()
            logger.info(f"Retrieved {len(orders)} orders from CoW Swap API")
            
            # Filter for recent orders and affiliate involvement
            affiliate_orders = []
            for order in orders:
                # Check if order involves affiliate addresses
                if self._check_order_for_affiliate(order):
                    affiliate_orders.append(order)
            
            logger.info(f"Found {len(affiliate_orders)} orders with affiliate involvement")
            return affiliate_orders
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch orders from CoW Swap API: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing CoW Swap API response: {e}")
            return []
    
    def _check_order_for_affiliate(self, order: dict) -> bool:
        """Check if order involves affiliate addresses"""
        try:
            # Check owner address
            owner = order.get('owner', '').lower()
            if owner in self.affiliate_addresses:
                return True
            
            # Check receiver address
            receiver = order.get('receiver', '').lower()
            if receiver in self.affiliate_addresses:
                return True
            
            # Check app data for affiliate references
            app_data = order.get('appData', '')
            if app_data:
                try:
                    # App data might contain affiliate information
                    app_data_lower = app_data.lower()
                    for addr in self.affiliate_addresses:
                        if addr[2:] in app_data_lower:  # Remove 0x prefix
                            return True
                except Exception:
                    pass
            
            # Check for fee recipient
            fee_amount = order.get('feeAmount', '0')
            if fee_amount and fee_amount != '0':
                # This could be an affiliate fee
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking order for affiliate: {e}")
            return False
    
    def scan_chain_for_settlements(self, chain_name: str, max_blocks: int = 1000) -> List[CowSwapTransaction]:
        """Scan chain for CoW Swap settlement events"""
        if chain_name not in self.chains:
            logger.error(f"Chain {chain_name} not available")
            return []
        
        w3 = self.chains[chain_name]
        transactions = []
        
        try:
            current_block = w3.eth.block_number
            start_block = self.get_last_processed_block(chain_name)
            end_block = min(start_block + max_blocks, current_block)
            
            logger.info(f"Scanning {chain_name} blocks {start_block} to {end_block}")
            
            # Process in smaller chunks for stability
            chunk_size = 50
            for chunk_start in range(start_block, end_block + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size - 1, end_block)
                
                try:
                    # Get settlement events
                    logs = w3.eth.get_logs({
                        'fromBlock': chunk_start,
                        'toBlock': chunk_end,
                        'address': self.settlement_contract,
                        'topics': [self.trade_event_sig]
                    })
                    
                    for log in logs:
                        tx = self._process_settlement_event(w3, log, chain_name)
                        if tx:
                            transactions.append(tx)
                    
                    logger.info(f"Processed {chain_name} blocks {chunk_start}-{chunk_end}, found {len(logs)} settlements")
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_start}-{chunk_end} on {chain_name}: {e}")
                
                # Rate limiting
                time.sleep(0.3)
            
            if end_block > start_block:
                self.update_last_processed_block(chain_name, end_block)
            
        except Exception as e:
            logger.error(f"Error scanning {chain_name}: {e}")
        
        return transactions
    
    def _process_settlement_event(self, w3: Web3, log, chain_name: str) -> Optional[CowSwapTransaction]:
        """Process a settlement event for affiliate involvement"""
        try:
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            tx = w3.eth.get_transaction(log['transactionHash'])
            block = w3.eth.get_block(log['blockNumber'])
            
            # Check for affiliate involvement
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            
            is_affiliate_tx = False
            affiliate_addr = None
            
            # Check transaction addresses
            for addr in self.affiliate_addresses:
                if addr in [from_addr, to_addr]:
                    is_affiliate_tx = True
                    affiliate_addr = addr
                    break
            
            # Check all transaction logs for affiliate addresses
            if not is_affiliate_tx:
                for tx_log in tx_receipt['logs']:
                    log_data = tx_log.get('data', '').hex().lower()
                    topics = [t.hex().lower() for t in tx_log.get('topics', [])]
                    
                    for addr in self.affiliate_addresses:
                        if addr[2:] in log_data or any(addr[2:] in topic for topic in topics):
                            is_affiliate_tx = True
                            affiliate_addr = addr
                            break
                    if is_affiliate_tx:
                        break
            
            if not is_affiliate_tx:
                return None
            
            # Extract settlement details
            order_uid = ""
            app_data = ""
            input_token = "UNKNOWN"
            output_token = "UNKNOWN"
            input_amount = "0"
            output_amount = "0"
            affiliate_fee_amount = "0"
            
            # Parse settlement event data
            if len(log['data']) >= 64:
                try:
                    # Extract basic amounts from settlement event
                    data_hex = log['data'].hex()
                    input_amount = str(int(data_hex[0:64], 16))
                    
                    # Look for order UID in topics
                    if len(log['topics']) > 1:
                        order_uid = log['topics'][1].hex()
                        
                except Exception as e:
                    logger.debug(f"Error parsing settlement data: {e}")
            
            # Look for Transfer events that might be affiliate fees
            for tx_log in tx_receipt['logs']:
                if (len(tx_log['topics']) == 3 and 
                    tx_log['topics'][0].hex().lower() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"):
                    try:
                        to_topic = tx_log['topics'][2].hex().lower()
                        if affiliate_addr and affiliate_addr[2:] in to_topic:
                            fee_data = tx_log['data'].hex()
                            if len(fee_data) >= 64:
                                affiliate_fee_amount = str(int(fee_data, 16))
                                break
                    except Exception as e:
                        logger.debug(f"Error parsing fee transfer: {e}")
            
            return CowSwapTransaction(
                protocol="cowswap",
                chain=chain_name,
                block_number=log['blockNumber'],
                tx_hash=log['transactionHash'].hex(),
                block_timestamp=block['timestamp'],
                block_date=datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d'),
                from_address=from_addr,
                to_address=to_addr,
                user_address=from_addr,
                affiliate_address=affiliate_addr or "",
                affiliate_fee_amount=affiliate_fee_amount,
                affiliate_fee_token="UNKNOWN",
                affiliate_fee_usd=0.0,
                input_token=input_token,
                input_amount=input_amount,
                input_amount_usd=0.0,
                output_token=output_token,
                output_amount=output_amount,
                output_amount_usd=0.0,
                volume_usd=0.0,
                order_uid=order_uid,
                app_data=app_data,
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d')
            )
            
        except Exception as e:
            logger.error(f"Error processing settlement event: {e}")
            return None
    
    def save_transactions(self, transactions: List[CowSwapTransaction]):
        """Save transactions to CSV"""
        if not transactions:
            logger.info("No CoW Swap transactions to save")
            return
        
        with open(self.csv_file, 'a', newline='') as f:
            fieldnames = [
                'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
                'from_address', 'to_address', 'user_address', 'affiliate_address',
                'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
                'input_token', 'input_amount', 'input_amount_usd',
                'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
                'order_uid', 'app_data', 'status', 'created_at', 'created_date'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            for tx in transactions:
                writer.writerow({
                    'protocol': tx.protocol,
                    'chain': tx.chain,
                    'block_number': tx.block_number,
                    'tx_hash': tx.tx_hash,
                    'block_timestamp': tx.block_timestamp,
                    'block_date': tx.block_date,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'user_address': tx.user_address,
                    'affiliate_address': tx.affiliate_address,
                    'affiliate_fee_amount': tx.affiliate_fee_amount,
                    'affiliate_fee_token': tx.affiliate_fee_token,
                    'affiliate_fee_usd': tx.affiliate_fee_usd,
                    'input_token': tx.input_token,
                    'input_amount': tx.input_amount,
                    'input_amount_usd': tx.input_amount_usd,
                    'output_token': tx.output_token,
                    'output_amount': tx.output_amount,
                    'output_amount_usd': tx.output_amount_usd,
                    'volume_usd': tx.volume_usd,
                    'order_uid': tx.order_uid,
                    'app_data': tx.app_data,
                    'status': tx.status,
                    'created_at': tx.created_at,
                    'created_date': tx.created_date
                })
        
        logger.info(f"Saved {len(transactions)} CoW Swap transactions to {self.csv_file}")
    
    def run(self, max_blocks: int = 1000, use_api: bool = True):
        """Main execution function"""
        logger.info(f"Starting CoW Swap listener with max_blocks={max_blocks}, use_api={use_api}")
        
        all_transactions = []
        
        # Try API approach first (more efficient for affiliate detection)
        if use_api:
            for chain_name in self.api_endpoints.keys():
                if chain_name in self.chains:
                    logger.info(f"Fetching recent orders from {chain_name} API...")
                    api_orders = self.get_recent_orders_from_api(chain_name, hours_back=24)
                    # Convert API orders to transactions (simplified for now)
                    logger.info(f"Found {len(api_orders)} potential affiliate orders on {chain_name}")
        
        # Scan chains for settlement events
        for chain_name in self.chains.keys():
            logger.info(f"Scanning {chain_name} for CoW Swap settlements...")
            transactions = self.scan_chain_for_settlements(chain_name, max_blocks)
            all_transactions.extend(transactions)
            logger.info(f"Found {len(transactions)} settlement transactions on {chain_name}")
        
        if all_transactions:
            self.save_transactions(all_transactions)
        
        logger.info(f"CoW Swap listener completed. Total transactions: {len(all_transactions)}")
        return all_transactions

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CoW Swap Protocol Affiliate Fee Listener')
    parser.add_argument('--blocks', type=int, default=1000,
                        help='Maximum blocks to scan')
    parser.add_argument('--chain', type=str,
                        help='Specific chain to scan')
    parser.add_argument('--no-api', action='store_true',
                        help='Skip API and only use blockchain scanning')
    
    args = parser.parse_args()
    
    try:
        listener = CowSwapListener()
        
        if args.chain:
            if args.chain in listener.chains:
                transactions = listener.scan_chain_for_settlements(args.chain, args.blocks)
                listener.save_transactions(transactions)
            else:
                logger.error(f"Chain {args.chain} not available")
        else:
            listener.run(max_blocks=args.blocks, use_api=not args.no_api)
            
    except Exception as e:
        logger.error(f"Error running CoW Swap listener: {e}")
        raise

if __name__ == "__main__":
    main()
