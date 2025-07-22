#!/usr/bin/env python3
"""
Fixed THORChain Affiliate Fee Parser
Based on the CRM query structure to properly parse THORChain affiliate data
"""

import requests
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
THORCHAIN_MIDGARD_URL = 'https://midgard.ninerealms.com'
DB_PATH = 'thorchain_fixed_fees.db'

def init_database():
    """Initialize the THORChain database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thorchain_swaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            from_address TEXT,
            tx_id TEXT,
            affiliate_address TEXT,
            affiliate_fee_basis_points INTEGER,
            affiliate_fee_percent REAL,
            from_asset TEXT,
            to_asset TEXT,
            swap_path TEXT,
            from_amount_usd REAL,
            to_amount_usd REAL,
            affiliate_fee_usd REAL,
            block_timestamp INTEGER,
            created_at INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_thorchain_tx_id ON thorchain_swaps(tx_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_thorchain_affiliate ON thorchain_swaps(affiliate_address)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("THORChain database initialized")

def fetch_thorchain_swaps(limit: int = 1000, offset: int = 0) -> List[Dict]:
    """Fetch THORChain swaps from Midgard API"""
    logger.info(f"Fetching THORChain swaps (limit: {limit}, offset: {offset})...")
    
    try:
        # Use the swaps endpoint instead of actions
        url = f"{THORCHAIN_MIDGARD_URL}/v2/history/swaps"
        params = {
            'limit': limit,
            'offset': offset,
            'interval': '1d'  # Daily intervals
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        swaps = data.get('intervals', [])
        
        logger.info(f"Fetched {len(swaps)} THORChain swap intervals")
        return swaps
        
    except Exception as e:
        logger.error(f"Error fetching THORChain swaps: {e}")
        return []

def fetch_thorchain_actions_with_affiliate(limit: int = 1000) -> List[Dict]:
    """Fetch THORChain actions and filter for affiliate data"""
    logger.info(f"Fetching THORChain actions for affiliate analysis...")
    
    try:
        url = f"{THORCHAIN_MIDGARD_URL}/v2/actions"
        params = {
            'limit': limit,
            'offset': 0,
            'type': 'swap'  # Only swap actions
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        # Filter for actions with affiliate data
        affiliate_actions = []
        for action in actions:
            # Check if this action has affiliate information
            metadata = action.get('metadata', {})
            swap = metadata.get('swap', {})
            
            # Look for affiliate address in the swap metadata
            if 'affiliateAddress' in swap or 'affiliate' in swap:
                affiliate_actions.append(action)
        
        logger.info(f"Found {len(affiliate_actions)} actions with affiliate data out of {len(actions)} total")
        return affiliate_actions
        
    except Exception as e:
        logger.error(f"Error fetching THORChain actions: {e}")
        return []

def parse_thorchain_action_for_affiliate(action: Dict) -> Optional[Dict]:
    """Parse a THORChain action for affiliate fee data"""
    try:
        metadata = action.get('metadata', {})
        swap = metadata.get('swap', {})
        
        # Extract basic transaction info
        tx_id = action.get('txID', '')
        date_timestamp = int(action.get('date', 0))
        date_str = datetime.fromtimestamp(date_timestamp).isoformat() if date_timestamp else ''
        
        # Extract swap details
        from_asset = swap.get('from', {}).get('asset', '')
        to_asset = swap.get('to', {}).get('asset', '')
        from_amount = float(swap.get('from', {}).get('amount', 0)) / 1e8
        to_amount = float(swap.get('to', {}).get('amount', 0)) / 1e8
        
        # Extract affiliate information
        affiliate_address = swap.get('affiliateAddress', '')
        affiliate_fee_raw = swap.get('affiliateFee', {})
        affiliate_fee_amount = float(affiliate_fee_raw.get('amount', 0)) / 1e8 if affiliate_fee_raw else 0
        affiliate_fee_asset = affiliate_fee_raw.get('asset', '') if affiliate_fee_raw else ''
        
        # Only process if ShapeShift is the affiliate
        if affiliate_address != 'ss':
            return None
        
        # Extract addresses
        from_address = ''
        in_tx = action.get('in', [])
        if in_tx and len(in_tx) > 0:
            from_address = in_tx[0].get('address', '')
        
        # Calculate USD values (simplified - would need price data for accuracy)
        # For now, using the amounts as rough USD estimates
        from_amount_usd = from_amount  # Simplified
        affiliate_fee_usd = affiliate_fee_amount  # Simplified
        
        # Create swap path
        from_asset_name = from_asset.split('.')[-1] if '.' in from_asset else from_asset.split('-')[0]
        to_asset_name = to_asset.split('.')[-1] if '.' in to_asset else to_asset.split('-')[0]
        swap_path = f"{from_asset_name} -> {to_asset_name}"
        
        return {
            'day': date_str.split('T')[0] if date_str else '',
            'from_address': from_address,
            'tx_id': tx_id,
            'affiliate_address': affiliate_address,
            'affiliate_fee_basis_points': 0,  # Would need to calculate from fee amount
            'affiliate_fee_percent': 0,  # Would need to calculate
            'from_asset': from_asset,
            'to_asset': to_asset,
            'swap_path': swap_path,
            'from_amount_usd': from_amount_usd,
            'to_amount_usd': to_amount,
            'affiliate_fee_usd': affiliate_fee_usd,
            'block_timestamp': date_timestamp,
            'created_at': int(time.time())
        }
        
    except Exception as e:
        logger.error(f"Error parsing THORChain action: {e}")
        return None

def store_thorchain_swaps(swaps: List[Dict]):
    """Store THORChain swaps in the database"""
    if not swaps:
        logger.info("No THORChain swaps to store")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for swap in swaps:
            cursor.execute('''
                INSERT OR IGNORE INTO thorchain_swaps 
                (day, from_address, tx_id, affiliate_address, affiliate_fee_basis_points,
                 affiliate_fee_percent, from_asset, to_asset, swap_path, from_amount_usd,
                 to_amount_usd, affiliate_fee_usd, block_timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                swap['day'],
                swap['from_address'],
                swap['tx_id'],
                swap['affiliate_address'],
                swap['affiliate_fee_basis_points'],
                swap['affiliate_fee_percent'],
                swap['from_asset'],
                swap['to_asset'],
                swap['swap_path'],
                swap['from_amount_usd'],
                swap['to_amount_usd'],
                swap['affiliate_fee_usd'],
                swap['block_timestamp'],
                swap['created_at']
            ))
        
        conn.commit()
        logger.info(f"Stored {len(swaps)} THORChain swaps")
        
    except Exception as e:
        logger.error(f"Error storing THORChain swaps: {e}")
    finally:
        conn.close()

def get_database_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM thorchain_swaps")
        total_swaps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tx_id) FROM thorchain_swaps")
        unique_txs = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM thorchain_swaps")
        total_fees = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT MIN(block_timestamp), MAX(block_timestamp) FROM thorchain_swaps")
        time_range = cursor.fetchone()
        min_time, max_time = time_range if time_range[0] else (0, 0)
        
        print(f"\n=== THORChain Database Statistics ===")
        print(f"Total swaps: {total_swaps}")
        print(f"Unique transactions: {unique_txs}")
        print(f"Total affiliate fees: ${total_fees:.2f}")
        if min_time and max_time:
            print(f"Time range: {datetime.fromtimestamp(min_time)} - {datetime.fromtimestamp(max_time)}")
        
        # Show sample data
        cursor.execute("SELECT tx_id, affiliate_address, swap_path, affiliate_fee_usd FROM thorchain_swaps LIMIT 5")
        samples = cursor.fetchall()
        
        if samples:
            print(f"\n📋 Sample THORChain Swaps:")
            for tx_id, affiliate, path, fee in samples:
                print(f"  TX: {tx_id[:20]}...")
                print(f"     Affiliate: {affiliate}")
                print(f"     Path: {path}")
                print(f"     Fee: ${fee:.4f}")
                print()
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
    finally:
        conn.close()

def main():
    """Main function to test THORChain affiliate parsing"""
    logger.info("Starting fixed THORChain affiliate fee parser...")
    
    # Initialize database
    init_database()
    
    # Fetch and process THORChain actions with affiliate data
    actions = fetch_thorchain_actions_with_affiliate(limit=2000)
    
    parsed_swaps = []
    for action in actions:
        parsed = parse_thorchain_action_for_affiliate(action)
        if parsed:
            parsed_swaps.append(parsed)
    
    # Store the parsed swaps
    store_thorchain_swaps(parsed_swaps)
    
    # Get database statistics
    get_database_stats()
    
    logger.info("THORChain affiliate parsing completed!")

if __name__ == "__main__":
    main() 