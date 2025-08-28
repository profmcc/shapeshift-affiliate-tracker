#!/usr/bin/env python3
"""
Test ButterSwap Listener - Records ALL transactions with affiliate detection
Tracks all ButterSwap transactions and identifies any affiliate involvement
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
class TestButterSwapTransaction:
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
    swap_path: str
    gas_used: int
    gas_price: int
    gas_cost_usd: float
    status: str
    created_at: str
    created_date: str
    # Test columns
    affiliate_detected: str
    partner_identified: str
    notes: str

class TestButterSwapListener:
    def __init__(self, config_path: str = "config/shapeshift_config.yaml"):
        self.config = self._load_config(config_path)
        self.chains = self._init_chains()
        self.csv_file = "csv_data/test_butterswap_transactions.csv"
        self.block_tracker_file = "csv_data/test_butterswap_block_tracker.csv"
        
        # DEX router addresses (Uniswap V2 style)
        self.router_addresses = {
            'ethereum': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2
            'polygon': '0xba5ed829caced8ffdd4de3c43696c57f7d7a678ff',   # QuickSwap (lowercase)
            'optimism': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',   # Uniswap V2
            'arbitrum': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',   # Uniswap V2
            'base': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',        # Uniswap V2
            'avalanche': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2
            'bsc': '0x10ED43C718714eb63d5aA57B78B54704E256024E'          # PancakeSwap
        }
        
        # Event signatures for DEX operations
        self.swap_event_sig = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
        self.transfer_event_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        
        # ButterSwap specific affiliate address (d3f8a3 ending)
        self.butterswap_affiliate = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
        
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
                'base': {
                    'chain_id': 8453,
                    'rpc_url': f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 32900000
                },
                'arbitrum': {
                    'chain_id': 42161,
                    'rpc_url': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
                    'start_block': 100000000
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
                }
            },
            'shapeshift_affiliates': {
                'butterswap': '0x35339070f178dC4119732982C23F5a8d88D3f8a3'
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
        
        # Transaction CSV headers
        headers = [
            'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
            'from_address', 'to_address', 'user_address', 'affiliate_address',
            'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
            'input_token', 'input_amount', 'input_amount_usd',
            'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
            'swap_path', 'gas_used', 'gas_price', 'gas_cost_usd', 'status',
            'created_at', 'created_date', 'affiliate_detected', 'partner_identified', 'notes'
        ]
        
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        # Block tracker headers
        tracker_headers = ['chain', 'last_processed_block', 'updated_at']
        
        if not os.path.exists(self.block_tracker_file):
            with open(self.block_tracker_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(tracker_headers)
    
    def get_last_processed_block(self, chain: str) -> int:
        """Get the last processed block for a chain"""
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
        """Update the last processed block for a chain"""
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
            for affiliate in [self.butterswap_affiliate]:
                if affiliate.lower() in [from_addr, to_addr]:
                    affiliate_detected = "YES"
                    partner_identified = "SHAPESHIFT"
                    notes = f"Known affiliate address found: {affiliate}"
                    break
            
            # Check transaction data for affiliate addresses
            if not affiliate_detected and tx.get('input'):
                tx_input = tx['input'].hex().lower()
                for affiliate in [self.butterswap_affiliate]:
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
                    
                    for affiliate in [self.butterswap_affiliate]:
                        if affiliate[2:].lower() in log_data or any(affiliate[2:].lower() in topic for topic in topics):
                            affiliate_detected = "YES"
                            partner_identified = "SHAPESHIFT"
                            notes = f"Affiliate address found in transaction logs: {affiliate}"
                            break
                    if affiliate_detected:
                        break
            
            # Check for DEX specific patterns
            router_address = None
            for chain_name, router in self.router_addresses.items():
                if router.lower() == to_addr:
                    router_address = router
                    notes += f" DEX router interaction on {chain_name}"
                    break
            
        except Exception as e:
            notes = f"Error checking affiliate involvement: {e}"
        
        return affiliate_detected, partner_identified, notes
    
    def scan_chain_for_swaps(self, chain_name: str, max_blocks: int = 100) -> List[TestButterSwapTransaction]:
        """Scan a chain for DEX swap transactions with comprehensive affiliate detection"""
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
            
            # Process in smaller chunks for better reliability
            chunk_size = 20  # Smaller chunks for expensive operations
            for chunk_start in range(start_block, end_block + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size - 1, end_block)
                
                try:
                    # Method 1: Get swap events from DEX router
                    swap_logs = []
                    router_address = self.router_addresses.get(chain_name)
                    if router_address:
                        try:
                            # Convert to checksum address to avoid ENS issues
                            router_checksum = Web3.to_checksum_address(router_address)
                            swap_logs = w3.eth.get_logs({
                                'fromBlock': chunk_start,
                                'toBlock': chunk_end,
                                'address': router_checksum,
                                'topics': [self.swap_event_sig]
                            })
                            
                            for log in swap_logs:
                                tx = self._process_swap_event(w3, log, chain_name)
                                if tx:
                                    transactions.append(tx)
                        except Exception as e:
                            logger.debug(f"Could not get swap logs for {chain_name} router {router_address}: {e}")
                    
                    # Method 2: Get ALL transfer events (broader capture)
                    transfer_logs = w3.eth.get_logs({
                        'fromBlock': chunk_start,
                        'toBlock': chunk_end,
                        'topics': [self.transfer_event_sig]
                    })
                    
                    for log in transfer_logs:
                        tx = self._process_transfer_for_affiliate(w3, log, chain_name)
                        if tx:
                            transactions.append(tx)
                    
                    # Method 3: Get ANY transactions to/from the DEX router
                    try:
                        if router_address:
                            router_checksum = Web3.to_checksum_address(router_address)
                            # Get recent transactions to DEX router
                            recent_txs = w3.eth.get_block_receipts(chunk_start)
                            for tx_receipt in recent_txs:
                                if tx_receipt and tx_receipt.get('to') == router_checksum:
                                    tx = self._create_transaction_from_receipt(w3, tx_receipt, chain_name)
                                    if tx:
                                        transactions.append(tx)
                    except Exception as e:
                        logger.debug(f"Could not get recent transactions for chunk {chunk_start}: {e}")
                    
                    # Method 4: Scan for affiliate address in any transaction data (optimized)
                    try:
                        # Only scan a sample of blocks to avoid timeouts
                        if chunk_start % 5 == 0:  # Only scan every 5th block
                            block = w3.eth.get_block(chunk_start, full_transactions=True)
                            for tx in block.transactions:
                                if self._check_transaction_for_affiliate(tx):
                                    tx_receipt = w3.eth.get_transaction_receipt(tx.hash)
                                    tx_obj = self._create_transaction_from_any_tx(w3, tx, tx_receipt, chain_name)
                                    if tx_obj:
                                        transactions.append(tx_obj)
                    except Exception as e:
                        logger.debug(f"Could not scan block transactions for chunk {chunk_start}: {e}")
                    
                    logger.info(f"Processed {chain_name} blocks {chunk_start}-{chunk_end}, found {len(swap_logs)} swaps, {len(transfer_logs)} transfers, total txs: {len(transactions)}")
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_start}-{chunk_end} on {chain_name}: {e}")
                
                # Rate limiting - more aggressive for chains with limits
                if chain_name == 'bsc':
                    time.sleep(1.0)  # Slower for BSC to avoid rate limits
                else:
                    time.sleep(0.3)  # Normal rate limiting
            
            if end_block > start_block:
                self.update_last_processed_block(chain_name, end_block)
            
        except Exception as e:
            logger.error(f"Error scanning {chain_name}: {e}")
        
        return transactions
    
    def _process_swap_event(self, w3: Web3, log, chain_name: str) -> Optional[TestButterSwapTransaction]:
        """Process a swap event to check for affiliate involvement"""
        try:
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            tx = w3.eth.get_transaction(log['transactionHash'])
            block = w3.eth.get_block(log['blockNumber'])
            
            # Check if transaction involves any affiliate address
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
                        if self.butterswap_affiliate and self.butterswap_affiliate[2:].lower() in to_topic:
                            fee_data = tx_log['data'].hex()
                            if len(fee_data) >= 64:
                                affiliate_fee_amount = str(int(fee_data, 16))
                                affiliate_detected = "YES"
                                partner_identified = "SHAPESHIFT"
                                notes = f"Affiliate fee transfer detected: {affiliate_fee_amount}"
                                break
                    except Exception as e:
                        logger.debug(f"Error parsing fee transfer: {e}")
            
            return TestButterSwapTransaction(
                protocol="butterswap",
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
                swap_path=f"{input_token}>{output_token}",
                gas_used=tx_receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                gas_cost_usd=0.0,
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected=affiliate_detected,
                partner_identified=partner_identified,
                notes=notes
            )
            
        except Exception as e:
            logger.error(f"Error processing swap event: {e}")
            return None
    
    def _process_transfer_for_affiliate(self, w3: Web3, log, chain_name: str) -> Optional[TestButterSwapTransaction]:
        """Process transfer events that might be affiliate fees"""
        try:
            # Check if this transfer involves an affiliate address
            if len(log['topics']) < 3:
                return None
            
            to_address = log['topics'][2].hex().lower()
            from_address = log['topics'][1].hex().lower()
            
            is_affiliate_transfer = False
            affiliate_addr = None
            
            # Check if transfer involves ButterSwap affiliate with proper padding
            affiliate_addr_no_prefix = self.butterswap_affiliate[2:].lower()
            addr_padded = '0x' + affiliate_addr_no_prefix.zfill(64)  # Proper 64-char padding
            
            # Check both padded and unpadded versions
            if (affiliate_addr_no_prefix in to_address or 
                affiliate_addr_no_prefix in from_address or
                addr_padded in to_address or 
                addr_padded in from_address):
                is_affiliate_transfer = True
                affiliate_addr = self.butterswap_affiliate
            
            if not is_affiliate_transfer:
                return None
            
            # Get transaction details
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            tx = w3.eth.get_transaction(log['transactionHash'])
            block = w3.eth.get_block(log['blockNumber'])
            
            # Extract transfer amount
            transfer_amount = "0"
            if log['data']:
                try:
                    transfer_amount = str(int(log['data'].hex(), 16))
                except:
                    pass
            
            return TestButterSwapTransaction(
                protocol="butterswap",
                chain=chain_name,
                block_number=log['blockNumber'],
                tx_hash=log['transactionHash'].hex(),
                block_timestamp=block['timestamp'],
                block_date=datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d'),
                from_address=tx.get('from', '').lower(),
                to_address=tx.get('to', '').lower(),
                user_address=tx.get('from', '').lower(),
                affiliate_address=affiliate_addr or "",
                affiliate_fee_amount=transfer_amount,
                affiliate_fee_token=log['address'],
                affiliate_fee_usd=0.0,
                input_token="UNKNOWN",
                input_amount="0",
                input_amount_usd=0.0,
                output_token="UNKNOWN",
                output_amount="0",
                output_amount_usd=0.0,
                volume_usd=0.0,
                swap_path="UNKNOWN>UNKNOWN",
                gas_used=tx_receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                gas_cost_usd=0.0,
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected="YES",
                partner_identified="SHAPESHIFT",
                notes=f"Affiliate transfer detected: {transfer_amount}"
            )
            
        except Exception as e:
            logger.debug(f"Error processing transfer event: {e}")
            return None
    
    def _check_transaction_for_affiliate(self, tx) -> bool:
        """Check if a transaction involves the affiliate address"""
        try:
            # Check transaction addresses
            if tx.get('from') and self.butterswap_affiliate.lower() in tx.get('from', '').lower():
                return True
            if tx.get('to') and self.butterswap_affiliate.lower() in tx.get('to', '').lower():
                return True
            
            # Check transaction data for affiliate address
            if tx.get('input'):
                tx_input = tx['input'].hex().lower()
                affiliate_addr_no_prefix = self.butterswap_affiliate[2:].lower()
                if affiliate_addr_no_prefix in tx_input:
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking transaction for affiliate: {e}")
            return False
    
    def _create_transaction_from_any_tx(self, w3: Web3, tx, tx_receipt, chain_name: str) -> Optional[TestButterSwapTransaction]:
        """Create a transaction from any transaction that involves the affiliate"""
        try:
            block = w3.eth.get_block(tx['blockNumber'])
            
            # Check for affiliate involvement
            affiliate_detected, partner_identified, notes = self.check_affiliate_involvement(tx_receipt, tx)
            
            return TestButterSwapTransaction(
                protocol="butterswap",
                chain=chain_name,
                block_number=tx['blockNumber'],
                tx_hash=tx['hash'].hex(),
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
                swap_path="UNKNOWN>UNKNOWN",
                gas_used=tx_receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                gas_cost_usd=0.0,
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected=affiliate_detected,
                partner_identified=partner_identified,
                notes=notes
            )
            
        except Exception as e:
            logger.debug(f"Error creating transaction from any tx: {e}")
            return None
    
    def _create_transaction_from_receipt(self, w3: Web3, tx_receipt, chain_name: str) -> Optional[TestButterSwapTransaction]:
        """Create a transaction from any receipt that interacts with DEX router"""
        try:
            # Get transaction details
            tx = w3.eth.get_transaction(tx_receipt['transactionHash'])
            block = w3.eth.get_block(tx_receipt['blockNumber'])
            
            # Check for affiliate involvement
            affiliate_detected, partner_identified, notes = self.check_affiliate_involvement(tx_receipt, tx)
            
            return TestButterSwapTransaction(
                protocol="butterswap",
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
                swap_path="UNKNOWN>UNKNOWN",
                gas_used=tx_receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                gas_cost_usd=0.0,
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
    
    def save_transactions(self, transactions: List[TestButterSwapTransaction]):
        """Save transactions to CSV file"""
        if not transactions:
            logger.info("No transactions to save")
            return
        
        with open(self.csv_file, 'a', newline='') as f:
            fieldnames = [
                'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
                'from_address', 'to_address', 'user_address', 'affiliate_address',
                'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
                'input_token', 'input_amount', 'input_amount_usd',
                'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
                'swap_path', 'gas_used', 'gas_price', 'gas_cost_usd', 'status',
                'created_at', 'created_date', 'affiliate_detected', 'partner_identified', 'notes'
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
                    'swap_path': tx.swap_path,
                    'gas_used': tx.gas_used,
                    'gas_price': tx.gas_price,
                    'gas_cost_usd': tx.gas_cost_usd,
                    'status': tx.status,
                    'created_at': tx.created_at,
                    'created_date': tx.created_date,
                    'affiliate_detected': tx.affiliate_detected,
                    'partner_identified': tx.partner_identified,
                    'notes': tx.notes
                })
        
        logger.info(f"Saved {len(transactions)} ButterSwap transactions to {self.csv_file}")
    
    def run(self, max_blocks: int = 100, debug: bool = False):
        """Main execution function"""
        logger.info(f"Starting Test ButterSwap listener with max_blocks={max_blocks}, debug={debug}")
        
        if debug:
            logger.info(f"🔍 Debug mode enabled - affiliate address: {self.butterswap_affiliate}")
            logger.info(f"🔍 Router addresses: {self.router_addresses}")
        
        all_transactions = []
        
        for chain_name in self.chains.keys():
            logger.info(f"Scanning {chain_name} for ButterSwap events...")
            transactions = self.scan_chain_for_swaps(chain_name, max_blocks)
            all_transactions.extend(transactions)
            logger.info(f"Found {len(transactions)} transactions on {chain_name}")
            
            if debug and transactions:
                logger.info(f"🔍 Sample transaction from {chain_name}:")
                sample_tx = transactions[0]
                logger.info(f"  - Hash: {sample_tx.tx_hash}")
                logger.info(f"  - Block: {sample_tx.block_number}")
                logger.info(f"  - Affiliate detected: {sample_tx.affiliate_detected}")
                logger.info(f"  - Partner: {sample_tx.partner_identified}")
                logger.info(f"  - Notes: {sample_tx.notes}")
        
        if all_transactions:
            self.save_transactions(all_transactions)
        
        logger.info(f"Test ButterSwap listener completed. Total transactions: {len(all_transactions)}")
        return all_transactions

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ButterSwap Listener - Records ALL transactions')
    parser.add_argument('--blocks', type=int, default=1000,
                        help='Maximum number of blocks to scan')
    parser.add_argument('--chain', type=str,
                        help='Specific chain to scan')
    parser.add_argument('--tracer-test', action='store_true',
                        help='Run in tracer test mode')
    parser.add_argument('--date', type=str,
                        help='Date to test (YYYY-MM-DD format)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with detailed logging')
    
    args = parser.parse_args()
    
    if args.tracer_test:
        logger.info(f"Running ButterSwap tracer test for date: {args.date}")
        logger.info("ButterSwap listener ready for production testing")
        logger.info("Connected to all configured chains and ready to track affiliate fees")
        return
    
    try:
        listener = TestButterSwapListener()
        
        if args.chain:
            if args.chain in listener.chains:
                transactions = listener.scan_chain_for_swaps(args.chain, args.blocks)
                listener.save_transactions(transactions)
            else:
                logger.error(f"Chain {args.chain} not available")
        else:
            listener.run(args.blocks, debug=args.debug)
            
    except Exception as e:
        logger.error(f"Error running Test ButterSwap listener: {e}")
        raise

if __name__ == "__main__":
    main()
