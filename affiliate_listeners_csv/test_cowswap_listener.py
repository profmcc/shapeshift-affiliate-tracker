#!/usr/bin/env python3
"""
Test CoW Swap Listener - Records ALL transactions with affiliate detection
Tracks all CoW Swap transactions and identifies any affiliate involvement
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
class TestCowSwapTransaction:
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
    # Test columns
    affiliate_detected: str
    partner_identified: str
    notes: str

class TestCowSwapListener:
    def __init__(self, config_path: str = "config/shapeshift_config.yaml"):
        self.config = self._load_config(config_path)
        self.chains = self._init_chains()
        self.csv_file = "csv_data/test_cowswap_transactions.csv"
        self.block_tracker_file = "csv_data/test_cowswap_block_tracker.csv"
        
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
        
        # Event signatures for DEX operations
        self.trade_event_sig = "0x0bcc4c97732e47d9946f229edb95f5e6320829021d42f1eec4c37c14845c8a8e"
        self.settlement_event_sig = "0xd6d4c0cd7c5c4310d8c7b8c7b2a7b7a7b7a7b7a7b7a7b7a7b7a7b7a7b7a7b7a"
        
        # Known affiliate addresses to look for
        self.known_affiliates = [
            "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # ShapeShift Safe
            "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum affiliate
            "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon affiliate
            "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism affiliate
            "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum affiliate
            "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche affiliate
            "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"   # BSC affiliate
        ]
        
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
        """Default configuration if config file not found"""
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
                    'start_block': 50000000
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
        """Initialize Web3 connections for all chains"""
        chains = {}
        logger.info(f"Available chains in config: {list(self.config.get('chains', {}).keys())}")
        
        for chain_name, chain_config in self.config.get('chains', {}).items():
            try:
                logger.info(f"Attempting to connect to {chain_name} with RPC: {chain_config['rpc_url'][:50]}...")
                w3 = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
                if not w3.is_connected():
                    logger.warning(f"Failed to connect to {chain_name}")
                    continue
                    
                # Add PoA middleware for some chains
                if chain_name in ['polygon', 'bsc']:
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                chains[chain_name] = w3
                logger.info(f"Connected to {chain_name}")
            except Exception as e:
                logger.error(f"Failed to initialize {chain_name}: {e}")
        
        logger.info(f"Successfully connected to chains: {list(chains.keys())}")
        return chains
    
    def _ensure_csv_files(self):
        """Create CSV files with headers if they don't exist"""
        os.makedirs("csv_data", exist_ok=True)
        
        headers = [
            'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
            'from_address', 'to_address', 'user_address', 'affiliate_address',
            'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
            'input_token', 'input_amount', 'input_amount_usd',
            'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
            'order_uid', 'app_data', 'status', 'created_at', 'created_date',
            'affiliate_detected', 'partner_identified', 'notes'
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
    
    def check_affiliate_involvement(self, tx_receipt: dict, tx: dict) -> tuple:
        """Check if a transaction involves any known affiliate addresses"""
        affiliate_detected = "NO"
        partner_identified = "NONE"
        notes = ""
        
        try:
            # Check transaction addresses
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            
            # Check direct involvement
            for affiliate in self.known_affiliates:
                if affiliate.lower() in [from_addr, to_addr]:
                    affiliate_detected = "YES"
                    partner_identified = "SHAPESHIFT"
                    notes = f"Known affiliate address found: {affiliate}"
                    break
            
            # Check transaction data for affiliate addresses
            if not affiliate_detected and tx.get('input'):
                tx_input = tx['input'].hex().lower()
                for affiliate in self.known_affiliates:
                    if affiliate[2:].lower() in tx_input:  # Remove 0x prefix
                        affiliate_detected = "YES"
                        partner_identified = "SHAPESHIFT"
                        notes = f"Affiliate address found in transaction data: {affiliate}"
                        break
            
            # Check logs for affiliate addresses
            if not affiliate_detected and tx_receipt.get('logs'):
                for log in tx_receipt['logs']:
                    log_data = log.get('data', '').hex().lower()
                    topics = [t.hex().lower() for t in log.get('topics', [])]
                    
                    for affiliate in self.known_affiliates:
                        if affiliate[2:].lower() in log_data or any(affiliate[2:].lower() in topic for topic in topics):
                            affiliate_detected = "YES"
                            partner_identified = "SHAPESHIFT"
                            notes = f"Affiliate address found in transaction logs: {affiliate}"
                            break
                    if affiliate_detected:
                        break
            
            # Check for CoW Swap specific patterns
            if to_addr == self.settlement_contract.lower():
                notes += " CoW Swap settlement contract interaction"
            
        except Exception as e:
            notes = f"Error checking affiliate involvement: {e}"
        
        return affiliate_detected, partner_identified, notes
    
    def scan_chain_for_settlements(self, chain_name: str, max_blocks: int = 1000) -> List[TestCowSwapTransaction]:
        """Scan a specific chain for CoW Swap settlement events"""
        if chain_name not in self.chains:
            logger.error(f"Chain {chain_name} not available")
            return []
        
        w3 = self.chains[chain_name]
        transactions = []
        
        try:
            current_block = w3.eth.block_number
            # Use recent blocks (last 24 hours worth)
            blocks_per_day = 7200  # Approximate blocks per day on Ethereum
            start_block = max(current_block - blocks_per_day, current_block - max_blocks)
            end_block = current_block
            
            logger.info(f"Scanning {chain_name} recent blocks {start_block} to {end_block}")
            
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
                    
                    # Also get ANY transactions to/from the settlement contract (broader capture)
                    try:
                        # Get recent transactions to settlement contract
                        recent_txs = w3.eth.get_block_receipts(chunk_start)
                        for tx_receipt in recent_txs:
                            if tx_receipt and tx_receipt.get('to') == self.settlement_contract.address:
                                # Create transaction from any interaction with settlement contract
                                tx = self._create_transaction_from_receipt(w3, tx_receipt, chain_name)
                                if tx:
                                    transactions.append(tx)
                    except Exception as e:
                        logger.debug(f"Could not get recent transactions for chunk {chunk_start}: {e}")
                    
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
    
    def _process_settlement_event(self, w3: Web3, log, chain_name: str) -> Optional[TestCowSwapTransaction]:
        """Process a settlement event for affiliate involvement"""
        try:
            # Get transaction details
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            tx = w3.eth.get_transaction(log['transactionHash'])
            block = w3.eth.get_block(log['blockNumber'])
            
            # Check for affiliate involvement
            affiliate_detected, partner_identified, notes = self.check_affiliate_involvement(tx_receipt, tx)
            
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
                        # Check if transfer is to any known affiliate
                        for affiliate in self.known_affiliates:
                            if affiliate[2:].lower() in to_topic:
                                fee_data = tx_log['data'].hex()
                                if len(fee_data) >= 64:
                                    affiliate_fee_amount = str(int(fee_data, 16))
                                    affiliate_detected = "YES"
                                    partner_identified = "SHAPESHIFT"
                                    notes = f"Affiliate fee transfer detected: {affiliate_fee_amount}"
                                    break
                    except Exception as e:
                        logger.debug(f"Error parsing fee transfer: {e}")
            
            return TestCowSwapTransaction(
                protocol="cowswap",
                chain=chain_name,
                block_number=log['blockNumber'],
                tx_hash=log['transactionHash'].hex(),
                block_timestamp=block['timestamp'],
                block_date=datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d'),
                from_address=tx.get('from', '').lower(),
                to_address=tx.get('to', '').lower(),
                user_address=tx.get('from', '').lower(),
                affiliate_address="",  # Will be filled if affiliate detected
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
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected=affiliate_detected,
                partner_identified=partner_identified,
                notes=notes
            )
            
        except Exception as e:
            logger.error(f"Error processing settlement event: {e}")
            return None
    
    def _create_transaction_from_receipt(self, w3: Web3, tx_receipt, chain_name: str) -> Optional[TestCowSwapTransaction]:
        """Create a transaction from any receipt that interacts with CoW Swap"""
        try:
            # Get transaction details
            tx = w3.eth.get_transaction(tx_receipt['transactionHash'])
            block = w3.eth.get_block(tx_receipt['blockNumber'])
            
            # Check for affiliate involvement
            affiliate_detected, partner_identified, notes = self.check_affiliate_involvement(tx_receipt, tx)
            
            return TestCowSwapTransaction(
                protocol="cowswap",
                chain=chain_name,
                block_number=tx_receipt['blockNumber'],
                tx_hash=tx_receipt['transactionHash'].hex(),
                block_timestamp=block['timestamp'],
                block_date=datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d'),
                from_address=tx.get('from', '').lower(),
                to_address=tx.get('to', '').lower(),
                user_address=tx.get('from', '').lower(),
                affiliate_address="",  # Will be filled if affiliate detected
                affiliate_fee_amount="0",
                affiliate_fee_token="UNKNOWN",
                affiliate_fee_usd=0.0,
                input_token="UNKNOWN",
                input_amount="0",
                input_amount_usd=0.0,
                output_token="UNKNOWN",
                output_amount="0",
                output_amount_usd=0.0,
                volume_usd=0.0,
                order_uid="",
                app_data="",
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected=affiliate_detected,
                partner_identified=partner_identified,
                notes=notes
            )
            
        except Exception as e:
            logger.debug(f"Error creating transaction from receipt: {e}")
            return None
    
    def save_transactions(self, transactions: List[TestCowSwapTransaction]):
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
                'order_uid', 'app_data', 'status', 'created_at', 'created_date',
                'affiliate_detected', 'partner_identified', 'notes'
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
                    'created_date': tx.created_date,
                    'affiliate_detected': tx.affiliate_detected,
                    'partner_identified': tx.partner_identified,
                    'notes': tx.notes
                })
        
        logger.info(f"Saved {len(transactions)} CoW Swap transactions to {self.csv_file}")
    
    def run(self, max_blocks: int = 1000, use_api: bool = True):
        """Main execution function"""
        logger.info(f"Starting Test CoW Swap listener with max_blocks={max_blocks}, use_api={use_api}")
        
        all_transactions = []
        
        # Scan chains for settlement events
        for chain_name in self.chains.keys():
            logger.info(f"Scanning {chain_name} for CoW Swap settlements...")
            transactions = self.scan_chain_for_settlements(chain_name, max_blocks)
            all_transactions.extend(transactions)
            logger.info(f"Found {len(transactions)} settlement transactions on {chain_name}")
        
        if all_transactions:
            self.save_transactions(all_transactions)
        
        logger.info(f"Test CoW Swap listener completed. Total transactions: {len(all_transactions)}")
        return all_transactions

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test CoW Swap Listener - Records ALL transactions')
    parser.add_argument('--blocks', type=int, default=1000,
                        help='Maximum blocks to scan')
    parser.add_argument('--chain', type=str,
                        help='Specific chain to scan')
    parser.add_argument('--no-api', action='store_true',
                        help='Skip API and only use blockchain scanning')
    
    args = parser.parse_args()
    
    try:
        listener = TestCowSwapListener()
        
        if args.chain:
            if args.chain in listener.chains:
                transactions = listener.scan_chain_for_settlements(args.chain, args.blocks)
                listener.save_transactions(transactions)
            else:
                logger.error(f"Chain {args.chain} not available")
        else:
            listener.run(max_blocks=args.blocks, use_api=not args.no_api)
            
    except Exception as e:
        logger.error(f"Error running Test CoW Swap listener: {e}")
        raise

if __name__ == "__main__":
    main()
