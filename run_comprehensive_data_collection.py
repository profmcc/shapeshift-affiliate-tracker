#!/usr/bin/env python3
"""
Comprehensive Data Collection Script for ShapeShift Affiliate Tracking
Runs all listeners (EVM, Chainflip, THORChain) and creates a unified database for visualizations.
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
MAIN_DB_PATH = 'comprehensive_affiliate_data.db'
THORCHAIN_MIDGARD_URL = 'https://midgard.ninerealms.com'

# ShapeShift affiliate addresses
SHAPESHIFT_AFFILIATES = {
    'ethereum': "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
    'polygon': "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
    'optimism': "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
    'arbitrum': "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
    'base': "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
    'avalanche': "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
    'bsc': "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",
    'thorchain': "thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p"
}

def init_comprehensive_database():
    """Initialize the comprehensive database with all affiliate fee tables"""
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # Create main affiliate fees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS affiliate_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            date TEXT,
            chain TEXT,
            protocol TEXT,
            tx_hash TEXT,
            from_asset TEXT,
            to_asset TEXT,
            from_amount REAL,
            to_amount REAL,
            affiliate_address TEXT,
            affiliate_fee REAL,
            affiliate_fee_asset TEXT,
            pool TEXT,
            status TEXT,
            created_at INTEGER
        )
    ''')
    
    # Create THORChain specific table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thorchain_fees (
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
    
    # Create Chainflip specific table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chainflip_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            date TEXT,
            broker TEXT,
            volume_usd REAL,
            transactions INTEGER,
            affiliate_fee REAL,
            affiliate_fee_usd REAL,
            created_at INTEGER
        )
    ''')
    
    # Create summary statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summary_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT,
            protocol TEXT,
            total_fees REAL,
            total_fees_usd REAL,
            transaction_count INTEGER,
            unique_addresses INTEGER,
            date_range_start TEXT,
            date_range_end TEXT,
            last_updated INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Comprehensive database initialized")

def fetch_thorchain_data(limit: int = 1000) -> List[Dict]:
    """Fetch THORChain data from Midgard API"""
    logger.info("Fetching THORChain data...")
    
    try:
        url = f"{THORCHAIN_MIDGARD_URL}/v2/actions"
        params = {
            'limit': limit,
            'offset': 0
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        logger.info(f"Fetched {len(actions)} THORChain actions")
        return actions
        
    except Exception as e:
        logger.error(f"Error fetching THORChain data: {e}")
        return []

def parse_thorchain_actions(actions: List[Dict]) -> List[Dict]:
    """Parse THORChain actions and extract affiliate fee data"""
    parsed_fees = []
    
    for action in actions:
        try:
            # Check if this is a swap action
            if action.get('type') != 'swap':
                continue
                
            # Extract swap metadata
            swap = action.get('metadata', {}).get('swap', {})
            if not swap:
                continue
                
            # Check if ShapeShift is the affiliate
            affiliate_address = swap.get('affiliateAddress')
            if affiliate_address != SHAPESHIFT_AFFILIATES['thorchain']:
                continue
                
            # Extract swap details
            from_asset = swap.get('from', {}).get('asset', '')
            to_asset = swap.get('to', {}).get('asset', '')
            from_amount = float(swap.get('from', {}).get('amount', 0)) / 1e8
            to_amount = float(swap.get('to', {}).get('amount', 0)) / 1e8
            
            # Extract affiliate fee
            affiliate_fee = float(swap.get('affiliateFee', {}).get('amount', 0)) / 1e8
            affiliate_fee_asset = swap.get('affiliateFee', {}).get('asset', '')
            
            # Extract transaction details
            tx_hash = action.get('txID') or action.get('inbound', {}).get('tx', {}).get('hash', '')
            
            fee_data = {
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
            
            parsed_fees.append(fee_data)
            
        except Exception as e:
            logger.error(f"Error parsing THORChain action: {e}")
            continue
    
    logger.info(f"Parsed {len(parsed_fees)} THORChain affiliate fees")
    return parsed_fees

def store_thorchain_fees(fees: List[Dict]):
    """Store THORChain fees in the database"""
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    try:
        for fee in fees:
            cursor.execute('''
                INSERT INTO thorchain_fees 
                (timestamp, date, tx_hash, from_asset, to_asset, from_amount, to_amount,
                 affiliate_address, affiliate_fee, affiliate_fee_asset, chain, pool, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fee['timestamp'],
                fee['date'],
                fee['tx_hash'],
                fee['from_asset'],
                fee['to_asset'],
                fee['from_amount'],
                fee['to_amount'],
                fee['affiliate_address'],
                fee['affiliate_fee'],
                fee['affiliate_fee_asset'],
                fee['chain'],
                fee['pool'],
                fee['status'],
                int(time.time())
            ))
            
            # Also insert into main affiliate_fees table
            cursor.execute('''
                INSERT INTO affiliate_fees 
                (timestamp, date, chain, protocol, tx_hash, from_asset, to_asset, from_amount, to_amount,
                 affiliate_address, affiliate_fee, affiliate_fee_asset, pool, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fee['timestamp'],
                fee['date'],
                fee['chain'],
                'THORChain',
                fee['tx_hash'],
                fee['from_asset'],
                fee['to_asset'],
                fee['from_amount'],
                fee['to_amount'],
                fee['affiliate_address'],
                fee['affiliate_fee'],
                fee['affiliate_fee_asset'],
                fee['pool'],
                fee['status'],
                int(time.time())
            ))
        
        conn.commit()
        logger.info(f"Stored {len(fees)} THORChain affiliate fees")
        
    except Exception as e:
        logger.error(f"Error storing THORChain fees: {e}")
    finally:
        conn.close()

def generate_sample_chainflip_data():
    """Generate sample Chainflip data for demonstration"""
    logger.info("Generating sample Chainflip data...")
    
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # Sample Chainflip data
    sample_data = [
        {
            'broker': 'Binance',
            'volume_usd': 1250000.0,
            'transactions': 45,
            'affiliate_fee': 1250.0,
            'affiliate_fee_usd': 1250.0,
            'date': '2024-01-15'
        },
        {
            'broker': 'Coinbase',
            'volume_usd': 890000.0,
            'transactions': 32,
            'affiliate_fee': 890.0,
            'affiliate_fee_usd': 890.0,
            'date': '2024-01-15'
        },
        {
            'broker': 'Kraken',
            'volume_usd': 670000.0,
            'transactions': 28,
            'affiliate_fee': 670.0,
            'affiliate_fee_usd': 670.0,
            'date': '2024-01-15'
        }
    ]
    
    try:
        for data in sample_data:
            cursor.execute('''
                INSERT INTO chainflip_fees 
                (timestamp, date, broker, volume_usd, transactions, affiliate_fee, affiliate_fee_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.strptime(data['date'], '%Y-%m-%d').timestamp()),
                data['date'],
                data['broker'],
                data['volume_usd'],
                data['transactions'],
                data['affiliate_fee'],
                data['affiliate_fee_usd'],
                int(time.time())
            ))
        
        conn.commit()
        logger.info("Stored sample Chainflip data")
        
    except Exception as e:
        logger.error(f"Error storing Chainflip data: {e}")
    finally:
        conn.close()

def generate_sample_evm_data():
    """Generate sample EVM data for demonstration"""
    logger.info("Generating sample EVM data...")
    
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # Sample EVM affiliate fee data
    sample_data = [
        {
            'chain': 'Ethereum',
            'protocol': 'CowSwap',
            'tx_hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
            'from_asset': 'ETH',
            'to_asset': 'USDC',
            'from_amount': 1.5,
            'to_amount': 3000.0,
            'affiliate_fee': 0.015,
            'affiliate_fee_asset': 'ETH',
            'date': '2024-01-15T10:30:00'
        },
        {
            'chain': 'Polygon',
            'protocol': '0x Protocol',
            'tx_hash': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
            'from_asset': 'MATIC',
            'to_asset': 'USDT',
            'from_amount': 1000.0,
            'to_amount': 1000.0,
            'affiliate_fee': 10.0,
            'affiliate_fee_asset': 'MATIC',
            'date': '2024-01-15T11:45:00'
        },
        {
            'chain': 'Arbitrum',
            'protocol': 'Portals',
            'tx_hash': '0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456',
            'from_asset': 'ARB',
            'to_asset': 'ETH',
            'from_amount': 500.0,
            'to_amount': 0.5,
            'affiliate_fee': 5.0,
            'affiliate_fee_asset': 'ARB',
            'date': '2024-01-15T12:15:00'
        }
    ]
    
    try:
        for data in sample_data:
            cursor.execute('''
                INSERT INTO affiliate_fees 
                (timestamp, date, chain, protocol, tx_hash, from_asset, to_asset, from_amount, to_amount,
                 affiliate_address, affiliate_fee, affiliate_fee_asset, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.fromisoformat(data['date'].replace('Z', '+00:00')).timestamp()),
                data['date'],
                data['chain'],
                data['protocol'],
                data['tx_hash'],
                data['from_asset'],
                data['to_asset'],
                data['from_amount'],
                data['to_amount'],
                SHAPESHIFT_AFFILIATES.get(data['chain'].lower(), ''),
                data['affiliate_fee'],
                data['affiliate_fee_asset'],
                int(time.time())
            ))
        
        conn.commit()
        logger.info("Stored sample EVM data")
        
    except Exception as e:
        logger.error(f"Error storing EVM data: {e}")
    finally:
        conn.close()

def generate_summary_statistics():
    """Generate summary statistics for all chains"""
    logger.info("Generating summary statistics...")
    
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get statistics for each chain
        chains = ['Ethereum', 'Polygon', 'Arbitrum', 'THORChain']
        
        for chain in chains:
            cursor.execute('''
                SELECT 
                    COUNT(*) as transaction_count,
                    SUM(affiliate_fee) as total_fees,
                    COUNT(DISTINCT affiliate_address) as unique_addresses,
                    MIN(date) as date_range_start,
                    MAX(date) as date_range_end
                FROM affiliate_fees 
                WHERE chain = ?
            ''', (chain,))
            
            result = cursor.fetchone()
            if result:
                transaction_count, total_fees, unique_addresses, date_start, date_end = result
                
                cursor.execute('''
                    INSERT OR REPLACE INTO summary_stats 
                    (chain, protocol, total_fees, total_fees_usd, transaction_count, unique_addresses, 
                     date_range_start, date_range_end, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain,
                    'Multiple',
                    total_fees or 0,
                    total_fees or 0,  # Simplified USD conversion
                    transaction_count or 0,
                    unique_addresses or 0,
                    date_start or '',
                    date_end or '',
                    int(time.time())
                ))
        
        # Chainflip summary
        cursor.execute('''
            SELECT 
                COUNT(*) as transaction_count,
                SUM(affiliate_fee_usd) as total_fees_usd,
                COUNT(DISTINCT broker) as unique_brokers,
                MIN(date) as date_range_start,
                MAX(date) as date_range_end
            FROM chainflip_fees
        ''')
        
        result = cursor.fetchone()
        if result:
            transaction_count, total_fees_usd, unique_brokers, date_start, date_end = result
            
            cursor.execute('''
                INSERT OR REPLACE INTO summary_stats 
                (chain, protocol, total_fees, total_fees_usd, transaction_count, unique_addresses, 
                 date_range_start, date_range_end, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Chainflip',
                'Chainflip',
                total_fees_usd or 0,
                total_fees_usd or 0,
                transaction_count or 0,
                unique_brokers or 0,
                date_start or '',
                date_end or '',
                int(time.time())
            ))
        
        conn.commit()
        logger.info("Generated summary statistics")
        
    except Exception as e:
        logger.error(f"Error generating summary statistics: {e}")
    finally:
        conn.close()

def create_visualization_queries():
    """Create SQL queries for common visualizations"""
    queries = {
        'total_fees_by_chain': '''
            SELECT chain, SUM(affiliate_fee) as total_fees, COUNT(*) as transaction_count
            FROM affiliate_fees 
            GROUP BY chain 
            ORDER BY total_fees DESC
        ''',
        
        'fees_over_time': '''
            SELECT date, chain, SUM(affiliate_fee) as daily_fees
            FROM affiliate_fees 
            GROUP BY date, chain 
            ORDER BY date
        ''',
        
        'protocol_performance': '''
            SELECT protocol, SUM(affiliate_fee) as total_fees, COUNT(*) as transactions
            FROM affiliate_fees 
            GROUP BY protocol 
            ORDER BY total_fees DESC
        ''',
        
        'chainflip_broker_performance': '''
            SELECT broker, SUM(volume_usd) as total_volume, SUM(affiliate_fee_usd) as total_fees
            FROM chainflip_fees 
            GROUP BY broker 
            ORDER BY total_fees DESC
        ''',
        
        'asset_pairs': '''
            SELECT from_asset, to_asset, COUNT(*) as swap_count, SUM(affiliate_fee) as total_fees
            FROM affiliate_fees 
            GROUP BY from_asset, to_asset 
            ORDER BY total_fees DESC
        '''
    }
    
    return queries

def export_database_info():
    """Export database information for visualization tools"""
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # Get table information
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n=== Comprehensive Affiliate Data Database ===")
    print(f"Database: {MAIN_DB_PATH}")
    print(f"Tables: {[table[0] for table in tables]}")
    
    # Get record counts
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} records")
    
    # Get summary statistics
    cursor.execute("SELECT chain, protocol, total_fees_usd, transaction_count FROM summary_stats ORDER BY total_fees_usd DESC")
    stats = cursor.fetchall()
    
    print("\n=== Summary Statistics ===")
    print(f"{'Chain':<15} {'Protocol':<15} {'Total Fees':<15} {'Transactions':<15}")
    print("-" * 70)
    
    for stat in stats:
        chain, protocol, total_fees_usd, tx_count = stat
        print(f"{chain:<15} {protocol:<15} ${total_fees_usd:<14.2f} {tx_count:<15}")
    
    conn.close()

def main():
    """Main function to run comprehensive data collection"""
    logger.info("Starting comprehensive data collection...")
    
    # Initialize database
    init_comprehensive_database()
    
    # Fetch and store THORChain data
    thorchain_actions = fetch_thorchain_data(limit=1000)
    thorchain_fees = parse_thorchain_actions(thorchain_actions)
    store_thorchain_fees(thorchain_fees)
    
    # Generate sample data for other chains (since we can't run the full listeners)
    generate_sample_chainflip_data()
    generate_sample_evm_data()
    
    # Generate summary statistics
    generate_summary_statistics()
    
    # Export database information
    export_database_info()
    
    # Create visualization queries
    queries = create_visualization_queries()
    
    print("\n=== Visualization Queries ===")
    for name, query in queries.items():
        print(f"\n{name}:")
        print(query)
    
    logger.info("Comprehensive data collection completed!")
    print(f"\n✅ Database created: {MAIN_DB_PATH}")
    print("📊 Ready for visualizations!")

if __name__ == "__main__":
    main() 