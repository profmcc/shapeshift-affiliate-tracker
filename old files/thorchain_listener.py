#!/usr/bin/env python3
"""
THORChain Affiliate Fee Listener - Consolidated Version
Tracks ShapeShift affiliate fees from THORChain swaps using Midgard API.
"""

import requests
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class THORChainListener:
    def __init__(self, db_path: str = "databases/thorchain_transactions.db"):
        self.db_path = db_path
        self.midgard_url = 'https://midgard.ninerealms.com'
        self.shapeshift_affiliate_ids = ['ss', 'thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p']
        self.init_database()

    def init_database(self):
        """Initialize the THORChain affiliate fees database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS thorchain_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_id TEXT UNIQUE,
                date TEXT,
                height INTEGER,
                from_address TEXT,
                to_address TEXT,
                affiliate_address TEXT,
                affiliate_fee_basis_points INTEGER,
                affiliate_fee_amount REAL,
                affiliate_fee_usd REAL,
                from_asset TEXT,
                to_asset TEXT,
                from_amount REAL,
                to_amount REAL,
                from_amount_usd REAL,
                to_amount_usd REAL,
                volume_usd REAL,
                swap_path TEXT,
                is_streaming_swap BOOLEAN,
                liquidity_fee REAL,
                swap_slip INTEGER,
                timestamp INTEGER,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ THORChain database initialized: {self.db_path}")

    def fetch_thorchain_actions(self, limit: int = 50) -> List[Dict]:
        """Fetch THORChain actions from Midgard API"""
        try:
            url = f"{self.midgard_url}/v2/actions"
            params = {
                'limit': limit,
                'type': 'swap'
            }
            
            logger.info(f"🔍 Fetching THORChain actions from Midgard API...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                actions = data.get('actions', [])
                logger.info(f"   ✅ Retrieved {len(actions)} swap actions")
                return actions
            else:
                logger.error(f"❌ Midgard API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching THORChain actions: {e}")
            return []

    def process_thorchain_action(self, action: Dict) -> Optional[Dict]:
        """Process a THORChain action and extract affiliate fee data"""
        try:
            # Check if this is a ShapeShift affiliate swap
            affiliate_address = action.get('metadata', {}).get('swap', {}).get('affiliateAddress', '')
            
            if not any(affiliate_id in affiliate_address.lower() for affiliate_id in self.shapeshift_affiliate_ids):
                return None
                
            # Extract swap data
            swap_data = action.get('metadata', {}).get('swap', {})
            pools = action.get('pools', [])
            
            # Get basic transaction info
            tx_id = action.get('txID', '')
            height = action.get('height', 0)
            date = action.get('date', '')
            timestamp = int(datetime.fromisoformat(date.replace('Z', '+00:00')).timestamp()) if date else 0
            
            # Extract asset information
            from_asset = None
            to_asset = None
            from_amount = 0.0
            to_amount = 0.0
            
            # Get first and last pools to determine from/to assets
            if pools:
                from_asset = pools[0].get('asset', '')
                to_asset = pools[-1].get('asset', '')
                
            # Extract amounts from inputs/outputs
            inputs = action.get('in', [])
            outputs = action.get('out', [])
            
            if inputs:
                from_amount = float(inputs[0].get('coins', [{}])[0].get('amount', 0)) / 1e8
                
            if outputs:
                to_amount = float(outputs[0].get('coins', [{}])[0].get('amount', 0)) / 1e8
            
            # Extract affiliate fee data
            affiliate_fee_basis_points = swap_data.get('affiliateFeeBasisPoints', 0)
            liquidity_fee = float(swap_data.get('liquidityFee', 0)) / 1e8
            swap_slip = swap_data.get('swapSlip', 0)
            
            # Calculate affiliate fee amount (basis points to decimal)
            affiliate_fee_amount = from_amount * (affiliate_fee_basis_points / 10000.0) if affiliate_fee_basis_points else 0
            
            # Get addresses
            from_address = inputs[0].get('address', '') if inputs else ''
            to_address = outputs[0].get('address', '') if outputs else ''
            
            transaction = {
                'tx_id': tx_id,
                'date': date,
                'height': height,
                'timestamp': timestamp,
                'from_address': from_address,
                'to_address': to_address,
                'affiliate_address': affiliate_address,
                'affiliate_fee_basis_points': affiliate_fee_basis_points,
                'affiliate_fee_amount': affiliate_fee_amount,
                'affiliate_fee_usd': 0.0,  # Will be calculated with price data
                'from_asset': from_asset,
                'to_asset': to_asset,
                'from_amount': from_amount,
                'to_amount': to_amount,
                'from_amount_usd': 0.0,  # Will be calculated with price data
                'to_amount_usd': 0.0,    # Will be calculated with price data
                'volume_usd': 0.0,       # Will be calculated as max(from_usd, to_usd)
                'swap_path': ' -> '.join([pool.get('asset', '') for pool in pools]),
                'is_streaming_swap': swap_data.get('streamingSwap', {}).get('quantity', 0) > 1,
                'liquidity_fee': liquidity_fee,
                'swap_slip': swap_slip
            }
            
            logger.info(f"   ✅ Found ShapeShift affiliate swap: {tx_id} ({from_asset} -> {to_asset})")
            return transaction
            
        except Exception as e:
            logger.error(f"❌ Error processing THORChain action: {e}")
            return None

    def save_transactions_to_db(self, transactions: List[Dict]):
        """Save transactions to database"""
        if not transactions:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for tx in transactions:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO thorchain_transactions 
                    (tx_id, date, height, from_address, to_address, affiliate_address,
                     affiliate_fee_basis_points, affiliate_fee_amount, affiliate_fee_usd,
                     from_asset, to_asset, from_amount, to_amount, from_amount_usd, 
                     to_amount_usd, volume_usd, swap_path, is_streaming_swap, 
                     liquidity_fee, swap_slip, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx['tx_id'], tx['date'], tx['height'], tx['from_address'], 
                    tx['to_address'], tx['affiliate_address'], tx['affiliate_fee_basis_points'],
                    tx['affiliate_fee_amount'], tx['affiliate_fee_usd'], tx['from_asset'],
                    tx['to_asset'], tx['from_amount'], tx['to_amount'], tx['from_amount_usd'],
                    tx['to_amount_usd'], tx['volume_usd'], tx['swap_path'],
                    tx['is_streaming_swap'], tx['liquidity_fee'], tx['swap_slip'], tx['timestamp']
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"❌ Error saving transaction {tx['tx_id']}: {e}")
                
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {saved_count} THORChain transactions to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM thorchain_transactions")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(affiliate_fee_amount) FROM thorchain_transactions")
        total_affiliate_fees = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(volume_usd) FROM thorchain_transactions")
        total_volume = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT from_asset) FROM thorchain_transactions")
        unique_assets = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 THORChain Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Total affiliate fees: {total_affiliate_fees:.6f}")
        print(f"   Total volume: ${total_volume:.2f}")
        print(f"   Unique assets: {unique_assets}")

    def run_listener(self, limit: int = 100):
        """Run the THORChain listener"""
        logger.info("🚀 Starting THORChain affiliate fee listener")
        
        # Fetch actions from Midgard API
        actions = self.fetch_thorchain_actions(limit)
        
        if not actions:
            logger.warning("⚠️ No actions retrieved from THORChain")
            return
            
        # Process actions to find ShapeShift affiliate swaps
        affiliate_transactions = []
        for action in actions:
            processed_tx = self.process_thorchain_action(action)
            if processed_tx:
                affiliate_transactions.append(processed_tx)
                
        # Save to database
        self.save_transactions_to_db(affiliate_transactions)
        
        logger.info(f"✅ THORChain listener completed! Found {len(affiliate_transactions)} affiliate transactions")
        self.get_database_stats()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='THORChain Affiliate Fee Listener')
    parser.add_argument('--limit', type=int, default=100, help='Number of actions to fetch')
    args = parser.parse_args()
    
    listener = THORChainListener()
    listener.run_listener(args.limit)

if __name__ == "__main__":
    main() 