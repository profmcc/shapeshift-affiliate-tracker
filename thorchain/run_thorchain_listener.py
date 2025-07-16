#!/usr/bin/env python3
"""
ShapeShift THORChain Affiliate Tracker - Listener Runner
Fetches THORChain swap actions from Midgard API and stores affiliate fee data.
"""

import os
import sqlite3
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'shapeshift_thorchain_fees.db'
THORCHAIN_MIDGARD_URL = os.getenv('THORCHAIN_MIDGARD_URL', 'https://midgard.ninerealms.com')

# ShapeShift affiliate address for THORChain
SHAPESHIFT_AFFILIATE = "thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p"

def init_database():
    """Initialize the database with THORChain affiliate fee table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thorchain_affiliate_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            date TEXT,
            tx_hash TEXT,
            from_asset TEXT,
            to_asset TEXT,
            from_amount REAL,
            to_amount REAL,
            affiliate_address TEXT,
            affiliate_fee REAL,
            affiliate_fee_asset TEXT,
            chain TEXT,
            pool TEXT,
            status TEXT,
            created_at INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("THORChain affiliate fees database initialized")

def fetch_thorchain_actions(limit: int = 100, offset: int = 0) -> List[Dict]:
    """Fetch THORChain actions from Midgard API"""
    try:
        url = f"{THORCHAIN_MIDGARD_URL}/v2/actions"
        params = {
            'limit': limit,
            'offset': offset
        }
        
        logger.info(f"Fetching THORChain actions from {url} with offset {offset}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('actions', [])
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching THORChain actions: {e}")
        return []

def parse_swap_action(action: Dict) -> Optional[Dict]:
    """Parse a THORChain swap action and extract affiliate fee data"""
    try:
        # Check if this is a swap action
        if action.get('type') != 'swap':
            return None
            
        # Extract swap metadata
        swap = action.get('metadata', {}).get('swap', {})
        if not swap:
            return None
            
        # Check if ShapeShift is the affiliate
        affiliate_address = swap.get('affiliateAddress')
        if affiliate_address != SHAPESHIFT_AFFILIATE:
            return None
            
        # Extract swap details
        from_asset = swap.get('from', {}).get('asset', '')
        to_asset = swap.get('to', {}).get('asset', '')
        from_amount = float(swap.get('from', {}).get('amount', 0)) / 1e8  # Convert from base units
        to_amount = float(swap.get('to', {}).get('amount', 0)) / 1e8
        
        # Extract affiliate fee
        affiliate_fee = float(swap.get('affiliateFee', {}).get('amount', 0)) / 1e8
        affiliate_fee_asset = swap.get('affiliateFee', {}).get('asset', '')
        
        # Extract transaction details
        tx_hash = action.get('txID') or action.get('inbound', {}).get('tx', {}).get('hash', '')
        
        return {
            'timestamp': int(action.get('date', 0)),
            'date': datetime.fromtimestamp(int(action.get('date', 0))).isoformat(),
            'tx_hash': tx_hash,
            'from_asset': from_asset,
            'to_asset': to_asset,
            'from_amount': from_amount,
            'to_amount': to_amount,
            'affiliate_address': affiliate_address,
            'affiliate_fee': affiliate_fee,
            'affiliate_fee_asset': affiliate_fee_asset,
            'chain': 'THORChain',
            'pool': swap.get('pool', ''),
            'status': action.get('status', '')
        }
        
    except Exception as e:
        logger.error(f"Error parsing swap action: {e}")
        return None

def store_affiliate_fee(fee_data: Dict):
    """Store affiliate fee data in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO thorchain_affiliate_fees 
            (timestamp, date, tx_hash, from_asset, to_asset, from_amount, to_amount,
             affiliate_address, affiliate_fee, affiliate_fee_asset, chain, pool, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fee_data['timestamp'],
            fee_data['date'],
            fee_data['tx_hash'],
            fee_data['from_asset'],
            fee_data['to_asset'],
            fee_data['from_amount'],
            fee_data['to_amount'],
            fee_data['affiliate_address'],
            fee_data['affiliate_fee'],
            fee_data['affiliate_fee_asset'],
            fee_data['chain'],
            fee_data['pool'],
            fee_data['status'],
            int(time.time())
        ))
        
        conn.commit()
        logger.info(f"Stored affiliate fee: {fee_data['from_asset']} -> {fee_data['to_asset']}, Fee: {fee_data['affiliate_fee']} {fee_data['affiliate_fee_asset']}")
        
    except Exception as e:
        logger.error(f"Error storing affiliate fee: {e}")
    finally:
        conn.close()

def get_last_processed_offset() -> int:
    """Get the last processed offset from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT MAX(timestamp) FROM thorchain_affiliate_fees')
        result = cursor.fetchone()
        
        if result and result[0]:
            # Convert timestamp to approximate offset (rough estimate)
            # This is a simplified approach - in production you'd want more sophisticated tracking
            return int(result[0] / 1000)  # Rough conversion
        return 0
        
    except Exception as e:
        logger.error(f"Error getting last processed offset: {e}")
        return 0
    finally:
        conn.close()

def run_thorchain_listener():
    """Main function to run the THORChain listener"""
    logger.info("Starting THORChain affiliate fee listener")
    
    # Initialize database
    init_database()
    
    # Get last processed offset
    last_offset = get_last_processed_offset()
    logger.info(f"Starting from offset: {last_offset}")
    
    total_processed = 0
    total_fees_found = 0
    
    while True:
        try:
            # Fetch actions from Midgard
            actions = fetch_thorchain_actions(limit=100, offset=last_offset)
            
            if not actions:
                logger.info("No more actions to process")
                break
                
            logger.info(f"Processing {len(actions)} actions")
            
            for action in actions:
                total_processed += 1
                
                # Parse swap action
                fee_data = parse_swap_action(action)
                
                if fee_data:
                    # Store affiliate fee data
                    store_affiliate_fee(fee_data)
                    total_fees_found += 1
            
            # Update offset for next batch
            last_offset += len(actions)
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in THORChain listener: {e}")
            time.sleep(5)  # Wait before retrying
    
    logger.info(f"THORChain listener completed. Processed {total_processed} actions, found {total_fees_found} affiliate fees")

def query_thorchain_fees():
    """Query and display THORChain affiliate fees"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get total fees by asset
        cursor.execute('''
            SELECT affiliate_fee_asset, 
                   COUNT(*) as count, 
                   SUM(affiliate_fee) as total_fee,
                   MIN(date) as first_date,
                   MAX(date) as last_date
            FROM thorchain_affiliate_fees 
            GROUP BY affiliate_fee_asset
            ORDER BY total_fee DESC
        ''')
        
        results = cursor.fetchall()
        
        print("\n=== THORChain Affiliate Fee Summary ===")
        print(f"{'Asset':<15} {'Count':<8} {'Total Fee':<15} {'First Date':<20} {'Last Date':<20}")
        print("-" * 80)
        
        total_count = 0
        for row in results:
            asset, count, total_fee, first_date, last_date = row
            print(f"{asset:<15} {count:<8} {total_fee:<15.8f} {first_date:<20} {last_date:<20}")
            total_count += count
        
        print(f"\nTotal affiliate fees found: {total_count}")
        
        # Get recent fees
        cursor.execute('''
            SELECT date, from_asset, to_asset, affiliate_fee, affiliate_fee_asset, tx_hash
            FROM thorchain_affiliate_fees 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        
        recent_fees = cursor.fetchall()
        
        print("\n=== Recent THORChain Affiliate Fees ===")
        print(f"{'Date':<20} {'From':<10} {'To':<10} {'Fee':<15} {'Asset':<10} {'TX Hash':<20}")
        print("-" * 90)
        
        for row in recent_fees:
            date, from_asset, to_asset, fee, fee_asset, tx_hash = row
            print(f"{date:<20} {from_asset:<10} {to_asset:<10} {fee:<15.8f} {fee_asset:<10} {tx_hash[:20]}...")
            
    except Exception as e:
        logger.error(f"Error querying THORChain fees: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        query_thorchain_fees()
    else:
        run_thorchain_listener() 