#!/usr/bin/env python3
"""
ButterSwap Affiliate Transaction Listener
Tracks affiliate transactions for ShapeShift on Base blockchain
"""

import os
import sys
import csv
import json
import argparse
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    from web3 import Web3
    import requests
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Install with: pip install web3 requests")
    sys.exit(1)

# Configuration
BUTTERSWAP_AFFILIATE_ADDRESS = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
BASE_RPC_URL = "https://base-mainnet.g.alchemy.com/v2/demo"
CSV_FILENAME = "butterswap_affiliate_transactions.csv"
PROGRESS_FILENAME = "butterswap_scan_progress.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ButterSwapListener:
    """Listener for ButterSwap affiliate transactions on Base blockchain"""
    
    def __init__(self, rpc_url: str = None):
        """Initialize the listener with RPC connection"""
        self.rpc_url = rpc_url or self._get_rpc_url()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.affiliate_address = Web3.to_checksum_address(BUTTERSWAP_AFFILIATE_ADDRESS)
        
        # Check connection
        if not self.w3.is_connected():
            raise ConnectionError(f"❌ Cannot connect to Base RPC: {self.rpc_url}")
        
        logger.info(f"✅ Connected to Base blockchain")
        logger.info(f"🎯 Tracking affiliate: {self.affiliate_address}")
    
    def _get_rpc_url(self) -> str:
        """Get RPC URL from environment or use default"""
        # Try .env file first
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("BASE_RPC_URL="):
                            return line.split("=", 1)[1].strip()
            except Exception as e:
                logger.warning(f"Could not read .env file: {e}")
        
        # Try environment variable
        if os.getenv("BASE_RPC_URL"):
            return os.getenv("BASE_RPC_URL")
        
        # Try Alchemy API key
        if os.getenv("ALCHEMY_API_KEY"):
            api_key = os.getenv("ALCHEMY_API_KEY")
            return f"https://base-mainnet.g.alchemy.com/v2/{api_key}"
        
        # Fallback to demo URL
        logger.warning("⚠️ Using demo RPC URL (rate limited). Set BASE_RPC_URL in .env for better performance")
        return BASE_RPC_URL
    
    def test_connection(self) -> bool:
        """Test blockchain connection and get basic info"""
        try:
            latest_block = self.w3.eth.block_number
            chain_id = self.w3.eth.chain_id
            gas_price = self.w3.eth.gas_price
            
            print(f"✅ Connection successful!")
            print(f"📡 Latest block: {latest_block:,}")
            print(f"🔗 Chain ID: {chain_id}")
            print(f"⛽ Gas price: {self.w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
            
            # Check affiliate address balance
            balance = self.w3.eth.get_balance(self.affiliate_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            print(f"💰 Affiliate balance: {balance_eth:.6f} ETH")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def check_affiliate_address(self) -> Dict:
        """Get detailed info about the affiliate address"""
        try:
            balance = self.w3.eth.get_balance(self.affiliate_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            
            # Get transaction count
            nonce = self.w3.eth.get_transaction_count(self.affiliate_address)
            
            # Get recent transactions (last 10)
            latest_block = self.w3.eth.block_number
            recent_txs = []
            
            for block_num in range(latest_block, max(latest_block - 100, 0), -1):
                try:
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                    for tx in block.transactions:
                        if (tx['from'] == self.affiliate_address or 
                            tx['to'] == self.affiliate_address):
                            recent_txs.append({
                                'hash': tx['hash'].hex(),
                                'block': block_num,
                                'from': tx['from'],
                                'to': tx['to'],
                                'value': self.w3.from_wei(tx['value'], 'ether')
                            })
                            if len(recent_txs) >= 10:
                                break
                    if len(recent_txs) >= 10:
                        break
                except Exception:
                    continue
            
            print(f"📊 Affiliate Address Analysis:")
            print(f"📍 Address: {self.affiliate_address}")
            print(f"💰 Balance: {balance_eth:.6f} ETH")
            print(f"🔢 Transaction count: {nonce}")
            print(f"📝 Recent transactions: {len(recent_txs)}")
            
            if recent_txs:
                print(f"\n🔄 Last few transactions:")
                for i, tx in enumerate(recent_txs[:5], 1):
                    print(f"   {i}. Block {tx['block']}: {tx['hash'][:10]}...")
                    print(f"      {tx['from'][:10]}... → {tx['to'][:10]}...")
                    print(f"      Value: {tx['value']:.6f} ETH")
            
            return {
                'address': self.affiliate_address,
                'balance': balance_eth,
                'nonce': nonce,
                'recent_transactions': recent_txs
            }
            
        except Exception as e:
            print(f"❌ Error checking affiliate address: {e}")
            return {}
    
    def scan_blocks(self, start_block: int, max_blocks: int = 100) -> List[Dict]:
        """Scan blocks for affiliate transactions"""
        transactions = []
        end_block = min(start_block + max_blocks, self.w3.eth.block_number)
        
        print(f"🔍 Scanning blocks {start_block:,} to {end_block:,} ({max_blocks:,} blocks)")
        
        for block_num in range(start_block, end_block + 1):
            try:
                if block_num % 100 == 0:
                    print(f"   📍 Scanning block {block_num:,}...")
                
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block.transactions:
                    tx_hash = tx['hash'].hex()
                    tx_data = {
                        'block_number': block_num,
                        'hash': tx_hash,
                        'from': tx['from'],
                        'to': tx['to'],
                        'value': self.w3.from_wei(tx['value'], 'ether'),
                        'gas_price': self.w3.from_wei(tx['gasPrice'], 'gwei'),
                        'timestamp': block.timestamp,
                        'detection_method': []
                    }
                    
                    # Method 1: Direct involvement
                    if (tx['from'] == self.affiliate_address or 
                        tx['to'] == self.affiliate_address):
                        tx_data['detection_method'].append('direct_involvement')
                        transactions.append(tx_data)
                        continue
                    
                    # Method 2: Check transaction data (calldata)
                    if tx['input'] and tx['input'] != '0x':
                        if self.affiliate_address[2:].lower() in tx['input'].lower():
                            tx_data['detection_method'].append('in_calldata')
                            transactions.append(tx_data)
                            continue
                    
                    # Method 3: Check transaction receipt for events
                    try:
                        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                        if receipt and receipt.logs:
                            for log in receipt.logs:
                                # Check if affiliate address appears in log data
                                log_data = log.hex()
                                if self.affiliate_address[2:].lower() in log_data.lower():
                                    tx_data['detection_method'].append('in_logs')
                                    transactions.append(tx_data)
                                    break
                    except Exception:
                        pass
                
            except Exception as e:
                logger.warning(f"Error scanning block {block_num}: {e}")
                continue
        
        print(f"✅ Scan complete! Found {len(transactions)} transactions")
        return transactions
    
    def save_transactions(self, transactions: List[Dict], filename: str = None) -> str:
        """Save transactions to CSV file"""
        if not transactions:
            print("⚠️ No transactions to save")
            return ""
        
        filename = filename or CSV_FILENAME
        filepath = Path(filename)
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'block_number', 'hash', 'from', 'to', 'value', 
                'gas_price', 'timestamp', 'detection_method'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for tx in transactions:
                # Convert detection_method list to string
                tx_copy = tx.copy()
                tx_copy['detection_method'] = ', '.join(tx['detection_method'])
                writer.writerow(tx_copy)
        
        print(f"💾 Saved {len(transactions)} transactions to: {filepath}")
        return str(filepath)
    
    def save_progress(self, last_scanned_block: int):
        """Save scan progress to resume later"""
        progress = {
            'last_scanned_block': last_scanned_block,
            'timestamp': datetime.now().isoformat(),
            'affiliate_address': self.affiliate_address
        }
        
        with open(PROGRESS_FILENAME, 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(f"📝 Progress saved: last scanned block {last_scanned_block:,}")
    
    def load_progress(self) -> int:
        """Load last scanned block from progress file"""
        try:
            if Path(PROGRESS_FILENAME).exists():
                with open(PROGRESS_FILENAME, 'r') as f:
                    progress = json.load(f)
                    last_block = progress.get('last_scanned_block', 0)
                    print(f"📖 Resuming from block {last_block:,}")
                    return last_block
        except Exception as e:
            logger.warning(f"Could not load progress: {e}")
        
        # Start from recent block if no progress
        latest_block = self.w3.eth.block_number
        start_block = max(0, latest_block - 1000)  # Start from 1000 blocks ago
        print(f"🚀 Starting fresh from block {start_block:,}")
        return start_block

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="ButterSwap Affiliate Transaction Listener")
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test blockchain connection')
    parser.add_argument('--check-address', action='store_true',
                       help='Check affiliate address info')
    parser.add_argument('--max-blocks', type=int, default=100,
                       help='Maximum blocks to scan (default: 100)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last scanned block')
    parser.add_argument('--start-block', type=int,
                       help='Start scanning from specific block number')
    
    args = parser.parse_args()
    
    try:
        # Initialize listener
        listener = ButterSwapListener()
        
        # Test connection if requested
        if args.test_connection:
            listener.test_connection()
            return
        
        # Check address if requested
        if args.check_address:
            listener.check_affiliate_address()
            return
        
        # Determine start block
        if args.start_block is not None:
            start_block = args.start_block
        elif args.resume:
            start_block = listener.load_progress()
        else:
            start_block = listener.load_progress()
        
        # Scan for transactions
        print(f"🎯 Starting ButterSwap affiliate transaction scan...")
        transactions = listener.scan_blocks(start_block, args.max_blocks)
        
        if transactions:
            # Save results
            csv_file = listener.save_transactions(transactions)
            
            # Show summary
            print(f"\n✅ SUCCESS: Found {len(transactions)} affiliate transactions!")
            print(f"📁 Data saved to: {csv_file}")
            
            print(f"\n📊 Sample transactions:")
            for i, tx in enumerate(transactions[:5], 1):
                method = ', '.join(tx['detection_method'])
                print(f"   {i}. Block {tx['block_number']:,}: {method} - {tx['hash'][:10]}...")
            
            # Save progress
            end_block = start_block + args.max_blocks
            listener.save_progress(end_block)
            
        else:
            print(f"\n⚠️ No transactions found in the scanned range.")
            print(f"💡 Try: python butterswap_listener.py --max-blocks 1000")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Scan interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Unexpected error")
        sys.exit(1)

if __name__ == "__main__":
    main()
