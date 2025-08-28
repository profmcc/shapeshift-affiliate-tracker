#!/usr/bin/env python3
"""
Portals Bridge Protocol Affiliate Fee Listener
Tracks ShapeShift affiliate fees from Portals cross-chain bridge transactions
"""

import json
import csv
import time
import logging
from datetime import datetime
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
class PortalsTransaction:
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
    gas_used: int
    gas_price: int
    gas_cost_usd: float
    status: str
    created_at: str
    created_date: str

class PortalsListener:
    def __init__(self, config_path: str = "config/shapeshift_config.yaml"):
        self.config = self._load_config(config_path)
        self.chains = self._init_chains()
        self.csv_file = "csv_data/portals_transactions.csv"
        self.block_tracker_file = "csv_data/portals_block_tracker.csv"
        self.affiliate_addresses = self._load_affiliate_addresses()
        
        # Portals contract address (same across all chains)
        self.portals_contract = Web3.to_checksum_address("0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23")
        
        # Event signatures
        self.bridge_event_sig = "0x4a25d94a55df505cf9da1f1649d0381e2613c3c83c6a0a3df055ae0e82f6e4d7"
        self.affiliate_fee_event_sig = "0x4a25d94a55df505cf9da1f1649d0381e2613c3c83c6a0a3df055ae0e82f6e4d7"
        
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
                'portals': '0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502'
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
    
    def _load_affiliate_addresses(self) -> List[str]:
        """Load all ShapeShift affiliate addresses"""
        addresses = []
        affiliate_config = self.config.get('shapeshift_affiliates', {})
        
        # Add all addresses from config
        for key, address in affiliate_config.items():
            if isinstance(address, str) and address.startswith('0x'):
                addresses.append(address.lower())
        
        # Add variations list if it exists
        variations = affiliate_config.get('variations', [])
        for addr in variations:
            if isinstance(addr, str) and addr.startswith('0x'):
                addresses.append(addr.lower())
        
        return list(set(addresses))  # Remove duplicates
    
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
            'gas_used', 'gas_price', 'gas_cost_usd', 'status', 'created_at', 'created_date'
        ]
        
        # Create transaction CSV if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        # Block tracker headers
        tracker_headers = ['chain', 'last_processed_block', 'updated_at']
        
        # Create block tracker CSV if it doesn't exist
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
        except Exception as e:
            logger.debug(f"No previous block tracker found for {chain}: {e}")
        
        # Return default start block if no tracker found
        return self.config.get('chains', {}).get(chain, {}).get('start_block', 0)
    
    def update_last_processed_block(self, chain: str, block_number: int):
        """Update the last processed block for a chain"""
        # Read existing data
        existing_data = {}
        try:
            with open(self.block_tracker_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_data[row['chain']] = row
        except Exception as e:
            logger.debug(f"No existing block tracker: {e}")
        
        # Update or add the chain
        existing_data[chain] = {
            'chain': chain,
            'last_processed_block': block_number,
            'updated_at': datetime.now().isoformat()
        }
        
        # Write back to file
        with open(self.block_tracker_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['chain', 'last_processed_block', 'updated_at'])
            writer.writeheader()
            writer.writerows(existing_data.values())
    
    def scan_chain_for_events(self, chain_name: str, max_blocks: int = 1000) -> List[PortalsTransaction]:
        """Scan a specific chain for Portals bridge events"""
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
            
            # Process in chunks to avoid RPC limits
            chunk_size = 100
            for chunk_start in range(start_block, end_block + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size - 1, end_block)
                
                # Get logs for Portals contract
                try:
                    logs = w3.eth.get_logs({
                        'fromBlock': chunk_start,
                        'toBlock': chunk_end,
                        'address': self.portals_contract,
                        'topics': [self.bridge_event_sig]
                    })
                    
                    for log in logs:
                        tx = self._process_bridge_event(w3, log, chain_name)
                        if tx:
                            transactions.append(tx)
                    
                    logger.info(f"Processed {chain_name} blocks {chunk_start}-{chunk_end}, found {len(logs)} events")
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_start}-{chunk_end} on {chain_name}: {e}")
                
                # Rate limiting
                time.sleep(0.5)
            
            # Update block tracker
            if end_block > start_block:
                self.update_last_processed_block(chain_name, end_block)
            
        except Exception as e:
            logger.error(f"Error scanning {chain_name}: {e}")
        
        return transactions
    
    def _process_bridge_event(self, w3: Web3, log, chain_name: str) -> Optional[PortalsTransaction]:
        """Process a bridge event log to extract affiliate fee data"""
        try:
            # Get transaction details
            tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
            tx = w3.eth.get_transaction(log['transactionHash'])
            block = w3.eth.get_block(log['blockNumber'])
            
            # Check if any affiliate address is involved
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            
            is_affiliate_tx = False
            affiliate_addr = None
            
            # Check direct addresses
            for addr in self.affiliate_addresses:
                if addr in [from_addr, to_addr]:
                    is_affiliate_tx = True
                    affiliate_addr = addr
                    break
            
            # Check logs for affiliate addresses
            if not is_affiliate_tx:
                for tx_log in tx_receipt['logs']:
                    topics = [t.hex().lower() for t in tx_log.get('topics', [])]
                    for addr in self.affiliate_addresses:
                        if any(addr in topic for topic in topics):
                            is_affiliate_tx = True
                            affiliate_addr = addr
                            break
                    if is_affiliate_tx:
                        break
            
            if not is_affiliate_tx:
                return None
            
            # Extract fee information from logs
            affiliate_fee_amount = "0"
            affiliate_fee_token = "UNKNOWN"
            
            # Look for Transfer events that might be affiliate fees
            for tx_log in tx_receipt['logs']:
                if len(tx_log['topics']) == 3:  # Transfer event
                    try:
                        # Check if transfer involves affiliate address
                        if affiliate_addr and affiliate_addr[2:].upper() in tx_log['topics'][2].hex().upper():
                            data = tx_log['data']
                            if len(data) >= 66:  # Has amount data
                                amount_hex = data[-64:]
                                affiliate_fee_amount = str(int(amount_hex, 16))
                                affiliate_fee_token = tx_log['address']
                                break
                    except Exception as e:
                        logger.debug(f"Error parsing transfer log: {e}")
            
            # Create transaction object
            return PortalsTransaction(
                protocol="portals",
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
                affiliate_fee_token=affiliate_fee_token,
                affiliate_fee_usd=0.0,  # TODO: Add price lookup
                input_token="UNKNOWN",
                input_amount="0",
                input_amount_usd=0.0,
                output_token="UNKNOWN",
                output_amount="0",
                output_amount_usd=0.0,
                volume_usd=0.0,
                gas_used=tx_receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                gas_cost_usd=0.0,  # TODO: Add gas cost calculation
                status="success" if tx_receipt['status'] == 1 else "failed",
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d')
            )
            
        except Exception as e:
            logger.error(f"Error processing bridge event: {e}")
            return None
    
    def save_transactions(self, transactions: List[PortalsTransaction]):
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
                'gas_used', 'gas_price', 'gas_cost_usd', 'status', 'created_at', 'created_date'
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
                    'gas_used': tx.gas_used,
                    'gas_price': tx.gas_price,
                    'gas_cost_usd': tx.gas_cost_usd,
                    'status': tx.status,
                    'created_at': tx.created_at,
                    'created_date': tx.created_date
                })
        
        logger.info(f"Saved {len(transactions)} Portals transactions to {self.csv_file}")
    
    def run(self, max_blocks: int = 1000):
        """Main execution function"""
        logger.info(f"Starting Portals listener with max_blocks={max_blocks}")
        
        all_transactions = []
        
        # Scan all chains
        for chain_name in self.chains.keys():
            logger.info(f"Scanning {chain_name} for Portals events...")
            transactions = self.scan_chain_for_events(chain_name, max_blocks)
            all_transactions.extend(transactions)
            logger.info(f"Found {len(transactions)} transactions on {chain_name}")
        
        # Save all transactions
        if all_transactions:
            self.save_transactions(all_transactions)
        
        logger.info(f"Portals listener completed. Total transactions found: {len(all_transactions)}")
        return all_transactions

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portals Bridge Affiliate Fee Listener')
    parser.add_argument('--blocks', type=int, default=1000,
                        help='Maximum number of blocks to scan')
    parser.add_argument('--chain', type=str, 
                        help='Specific chain to scan (optional)')
    parser.add_argument('--config', type=str, default='config/shapeshift_config.yaml',
                        help='Path to config file')
    
    args = parser.parse_args()
    
    try:
        listener = PortalsListener(args.config)
        
        if args.chain:
            # Scan specific chain
            if args.chain in listener.chains:
                transactions = listener.scan_chain_for_events(args.chain, args.blocks)
                listener.save_transactions(transactions)
            else:
                logger.error(f"Chain {args.chain} not available")
        else:
            # Scan all chains
            listener.run(args.blocks)
            
    except Exception as e:
        logger.error(f"Error running Portals listener: {e}")
        raise

if __name__ == "__main__":
    main()
