#!/usr/bin/env python3
"""
Test Chainflip Listener - Records ALL transactions with affiliate detection
Tracks all Chainflip transactions and identifies any affiliate involvement
"""

import json
import csv
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestChainflipTransaction:
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
    swap_id: str
    source_chain: str
    destination_chain: str
    status: str
    created_at: str
    created_date: str
    # Test columns
    affiliate_detected: str
    partner_identified: str
    notes: str

class TestChainflipListener:
    def __init__(self, config_path: str = "config/shapeshift_config.yaml"):
        self.config = self._load_config(config_path)
        self.csv_file = "csv_data/test_chainflip_transactions.csv"
        self.state_file = "csv_data/test_chainflip_state.json"
        
        # Chainflip API endpoints
        self.api_base_url = "https://api.chainflip.io"
        
        # Known affiliate addresses to look for
        self.known_affiliates = [
            "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",  # ShapeShift
            "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # ShapeShift Safe
            "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum affiliate
            "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon affiliate
            "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism affiliate
            "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum affiliate
            "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche affiliate
            "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"   # BSC affiliate
        ]
        
        self._ensure_csv_files()
        self.state = self._load_state()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'shapeshift_affiliates': {
                'chainflip': 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi'
            },
            'listeners': {
                'chainflip': {
                    'api_rate_limit': 1.0,
                    'max_swaps_per_request': 100
                }
            }
        }
    
    def _ensure_csv_files(self):
        """Create CSV files with headers if they don't exist"""
        os.makedirs("csv_data", exist_ok=True)
        
        headers = [
            'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
            'from_address', 'to_address', 'user_address', 'affiliate_address',
            'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
            'input_token', 'input_amount', 'input_amount_usd',
            'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
            'swap_id', 'source_chain', 'destination_chain', 'status',
            'created_at', 'created_date', 'affiliate_detected', 'partner_identified', 'notes'
        ]
        
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def _load_state(self) -> dict:
        """Load processing state from file"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                'last_processed_block': 0,
                'last_processed_timestamp': 0,
                'processed_swap_ids': []
            }
    
    def _save_state(self):
        """Save current processing state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_sample_data(self) -> List[dict]:
        """Get sample data for testing - in production this would be real API calls"""
        # This simulates what we'd get from the Chainflip API
        sample_swaps = [
            {
                'swapId': 'test_swap_1',
                'executedAt': int(time.time()) - 3600,  # 1 hour ago
                'sourceAsset': {'symbol': 'ETH', 'chain': 'ethereum'},
                'destinationAsset': {'symbol': 'BTC', 'chain': 'bitcoin'},
                'depositAmount': '1.0',
                'egressAmount': '0.05',
                'affiliateFee': {'amount': '0.001', 'asset': {'symbol': 'ETH'}},
                'depositAddress': '0x1234567890123456789012345678901234567890',
                'egressAddress': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
                'status': 'completed',
                'blockNumber': 19000000,
                'txHash': '0x1234567890123456789012345678901234567890123456789012345678901234'
            },
            {
                'swapId': 'test_swap_2',
                'executedAt': int(time.time()) - 7200,  # 2 hours ago
                'sourceAsset': {'symbol': 'USDC', 'chain': 'ethereum'},
                'destinationAsset': {'symbol': 'SOL', 'chain': 'solana'},
                'depositAmount': '1000.0',
                'egressAmount': '10.5',
                'affiliateFee': {'amount': '0', 'asset': {'symbol': 'USDC'}},
                'depositAddress': '0xabcdef1234567890abcdef1234567890abcdef12',
                'egressAddress': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                'status': 'completed',
                'blockNumber': 19000001,
                'txHash': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            }
        ]
        return sample_swaps
    
    def check_affiliate_involvement(self, swap: dict) -> tuple:
        """Check if a swap involves any known affiliate addresses"""
        affiliate_detected = "NO"
        partner_identified = "NONE"
        notes = ""
        
        try:
            # Check for affiliate fees
            affiliate_fee = swap.get('affiliateFee', {})
            if isinstance(affiliate_fee, dict):
                fee_amount = affiliate_fee.get('amount', '0')
                if fee_amount and fee_amount != '0':
                    affiliate_detected = "YES"
                    notes = f"Affiliate fee: {fee_amount} {affiliate_fee.get('asset', {}).get('symbol', 'UNKNOWN')}"
                    
                    # Try to identify partner
                    if fee_amount == '0.001':
                        partner_identified = "SHAPESHIFT"
                    else:
                        partner_identified = "UNKNOWN_PARTNER"
            
            # Check addresses against known affiliates
            deposit_address = swap.get('depositAddress', '')
            egress_address = swap.get('egressAddress', '')
            
            for affiliate in self.known_affiliates:
                if affiliate in str(deposit_address) or affiliate in str(egress_address):
                    affiliate_detected = "YES"
                    partner_identified = "SHAPESHIFT"
                    notes = f"Known affiliate address found: {affiliate}"
                    break
            
            # Check for ShapeShift patterns
            if 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi' in str(swap):
                affiliate_detected = "YES"
                partner_identified = "SHAPESHIFT"
                notes = "ShapeShift broker address detected"
            
        except Exception as e:
            notes = f"Error checking affiliate involvement: {e}"
        
        return affiliate_detected, partner_identified, notes
    
    def process_swap(self, swap: dict) -> Optional[TestChainflipTransaction]:
        """Process a swap into standardized transaction format"""
        try:
            swap_id = swap.get('swapId', '')
            
            # Skip if already processed
            if swap_id in self.state['processed_swap_ids']:
                return None
            
            # Check for affiliate involvement
            affiliate_detected, partner_identified, notes = self.check_affiliate_involvement(swap)
            
            # Extract basic information
            executed_at = swap.get('executedAt', 0)
            if executed_at:
                block_timestamp = executed_at
                block_date = datetime.fromtimestamp(executed_at).strftime('%Y-%m-%d')
            else:
                block_timestamp = int(time.time())
                block_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract token and amount information
            source_asset = swap.get('sourceAsset', {})
            dest_asset = swap.get('destinationAsset', {})
            
            input_token = source_asset.get('symbol', 'UNKNOWN')
            output_token = dest_asset.get('symbol', 'UNKNOWN')
            
            # Extract amounts
            deposit_amount = swap.get('depositAmount', '0')
            egress_amount = swap.get('egressAmount', '0')
            
            # Extract affiliate fee
            affiliate_fee = swap.get('affiliateFee', {})
            fee_amount = affiliate_fee.get('amount', '0')
            fee_asset = affiliate_fee.get('asset', {})
            fee_token = fee_asset.get('symbol', input_token)
            
            # Extract chain information
            source_chain = source_asset.get('chain', 'unknown')
            dest_chain = dest_asset.get('chain', 'unknown')
            
            # Extract addresses
            deposit_address = swap.get('depositAddress', '')
            egress_address = swap.get('egressAddress', '')
            
            # Calculate USD values (placeholder - would need price API)
            volume_usd = 0.0
            fee_usd = 0.0
            input_usd = 0.0
            output_usd = 0.0
            
            # Create transaction object
            transaction = TestChainflipTransaction(
                protocol="chainflip",
                chain="chainflip",  # Multi-chain protocol
                block_number=swap.get('blockNumber', 0),
                tx_hash=swap.get('txHash', swap_id),
                block_timestamp=block_timestamp,
                block_date=block_date,
                from_address=deposit_address,
                to_address=egress_address,
                user_address=deposit_address,
                affiliate_address="",  # Will be filled if affiliate detected
                affiliate_fee_amount=fee_amount,
                affiliate_fee_token=fee_token,
                affiliate_fee_usd=fee_usd,
                input_token=input_token,
                input_amount=deposit_amount,
                input_amount_usd=input_usd,
                output_token=output_token,
                output_amount=egress_amount,
                output_amount_usd=output_usd,
                volume_usd=volume_usd,
                swap_id=swap_id,
                source_chain=source_chain,
                destination_chain=dest_chain,
                status=swap.get('status', 'completed').lower(),
                created_at=datetime.now().isoformat(),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                affiliate_detected=affiliate_detected,
                partner_identified=partner_identified,
                notes=notes
            )
            
            # Mark as processed
            self.state['processed_swap_ids'].append(swap_id)
            
            # Keep only recent swap IDs in state (last 1000)
            if len(self.state['processed_swap_ids']) > 1000:
                self.state['processed_swap_ids'] = self.state['processed_swap_ids'][-1000:]
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error processing swap {swap.get('swapId', 'unknown')}: {e}")
            return None
    
    def save_transactions(self, transactions: List[TestChainflipTransaction]):
        """Save transactions to CSV file"""
        if not transactions:
            logger.info("No Chainflip transactions to save")
            return
        
        with open(self.csv_file, 'a', newline='') as f:
            fieldnames = [
                'protocol', 'chain', 'block_number', 'tx_hash', 'block_timestamp', 'block_date',
                'from_address', 'to_address', 'user_address', 'affiliate_address',
                'affiliate_fee_amount', 'affiliate_fee_token', 'affiliate_fee_usd',
                'input_token', 'input_amount', 'input_amount_usd',
                'output_token', 'output_amount', 'output_amount_usd', 'volume_usd',
                'swap_id', 'source_chain', 'destination_chain', 'status',
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
                    'swap_id': tx.swap_id,
                    'source_chain': tx.source_chain,
                    'destination_chain': tx.destination_chain,
                    'status': tx.status,
                    'created_at': tx.created_at,
                    'created_date': tx.created_date,
                    'affiliate_detected': tx.affiliate_detected,
                    'partner_identified': tx.partner_identified,
                    'notes': tx.notes
                })
        
        logger.info(f"Saved {len(transactions)} Chainflip transactions to {self.csv_file}")
        self._save_state()
    
    def run(self, hours_back: int = 24, max_swaps: int = 100):
        """Main execution function"""
        logger.info(f"Starting Test Chainflip listener for last {hours_back} hours")
        
        # Get sample data for testing
        swaps = self.get_sample_data()
        
        if not swaps:
            logger.info("No swaps found")
            return []
        
        # Process swaps
        transactions = []
        for swap in swaps:
            tx = self.process_swap(swap)
            if tx:
                transactions.append(tx)
                logger.info(f"Processed swap: {tx.swap_id} - Affiliate: {tx.affiliate_detected} - Partner: {tx.partner_identified}")
        
        # Save transactions
        if transactions:
            self.save_transactions(transactions)
        
        logger.info(f"Test Chainflip listener completed. Found {len(transactions)} transactions")
        return transactions
    
    def test_api_connection(self):
        """Test connection to Chainflip API"""
        try:
            url = f"{self.api_base_url}/health"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info("✅ Successfully connected to Chainflip API")
            logger.info(f"API Status: {data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Chainflip API: {e}")
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Chainflip Listener - Records ALL transactions')
    parser.add_argument('--hours', type=int, default=24,
                        help='Hours back to scan for swaps')
    parser.add_argument('--max-swaps', type=int, default=100,
                        help='Maximum number of swaps to process')
    parser.add_argument('--test-connection', action='store_true',
                        help='Test API connection only')
    
    args = parser.parse_args()
    
    try:
        listener = TestChainflipListener()
        
        if args.test_connection:
            listener.test_api_connection()
            return
        
        # Run the listener
        transactions = listener.run(hours_back=args.hours, max_swaps=args.max_swaps)
        
        if transactions:
            logger.info(f"Successfully processed {len(transactions)} Chainflip transactions")
        else:
            logger.info("No transactions found in the specified time period")
            
    except Exception as e:
        logger.error(f"Error running Test Chainflip listener: {e}")
        raise

if __name__ == "__main__":
    main()
