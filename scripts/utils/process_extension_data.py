#!/usr/bin/env python3
"""
Process ViewBlock extension data and import into database
"""

import json
import sqlite3
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database(db_path: str = 'viewblock_extension_data.db'):
    """Initialize the database for extension data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viewblock_extension_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE,
            block_height TEXT,
            timestamp TEXT,
            from_address TEXT,
            to_address TEXT,
            affiliate_address TEXT,
            from_asset TEXT,
            to_asset TEXT,
            from_amount REAL,
            to_amount REAL,
            amount_raw TEXT,
            captured_at TEXT,
            raw_row_text TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_extension_tx_hash ON viewblock_extension_data(tx_hash)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_extension_timestamp ON viewblock_extension_data(timestamp)
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {db_path}")

def parse_block_height(block_height_str: str) -> Optional[int]:
    """Parse block height string to integer"""
    try:
        # Remove any commas and convert to int
        return int(block_height_str.replace(',', ''))
    except (ValueError, AttributeError):
        return None

def parse_timestamp(timestamp_str: str) -> Optional[str]:
    """Parse and standardize timestamp"""
    if not timestamp_str:
        return None
    
    # Try to parse common timestamp formats
    try:
        # If it's already in ISO format, return as is
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            return timestamp_str
        
        # Try to parse other formats
        # Add more parsing logic as needed based on actual timestamp format
        return timestamp_str
    except Exception:
        return timestamp_str

def process_extension_data(json_file: str, db_path: str = 'viewblock_extension_data.db'):
    """Process JSON data from extension and import into database"""
    
    # Initialize database
    init_database(db_path)
    
    # Load JSON data
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return
    
    if not isinstance(data, list):
        logger.error("JSON data should be a list of transactions")
        return
    
    logger.info(f"Processing {len(data)} transactions from extension data")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    imported_count = 0
    skipped_count = 0
    
    for tx in data:
        try:
            # Extract and clean data
            tx_hash = tx.get('tx_hash', '').strip()
            if not tx_hash:
                skipped_count += 1
                continue
            
            block_height = parse_block_height(tx.get('block_height', ''))
            timestamp = parse_timestamp(tx.get('timestamp', ''))
            from_address = tx.get('from_address', '').strip()
            to_address = tx.get('to_address', '').strip()
            affiliate_address = tx.get('affiliate_address', 'ss')
            from_asset = tx.get('from_asset', '').strip()
            to_asset = tx.get('to_asset', '').strip()
            from_amount = tx.get('from_amount')
            to_amount = tx.get('to_amount')
            amount_raw = tx.get('amount', '').strip()
            captured_at = tx.get('captured_at', '')
            raw_row_text = tx.get('raw_row_text', '').strip()
            
            # Insert into database
            cursor.execute('''
                INSERT OR IGNORE INTO viewblock_extension_data (
                    tx_hash, block_height, timestamp, from_address, to_address,
                    affiliate_address, from_asset, to_asset, from_amount, to_amount,
                    amount_raw, captured_at, raw_row_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_hash, block_height, timestamp, from_address, to_address,
                affiliate_address, from_asset, to_asset, from_amount, to_amount,
                amount_raw, captured_at, raw_row_text
            ))
            
            if cursor.rowcount > 0:
                imported_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            logger.error(f"Error processing transaction {tx.get('tx_hash', 'unknown')}: {e}")
            skipped_count += 1
            continue
    
    conn.commit()
    conn.close()
    
    logger.info(f"Import completed:")
    logger.info(f"  Imported: {imported_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"  Total processed: {len(data)}")

def get_database_stats(db_path: str = 'viewblock_extension_data.db'):
    """Get statistics about the imported data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM viewblock_extension_data")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM viewblock_extension_data WHERE timestamp IS NOT NULL")
    time_range = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT from_address) FROM viewblock_extension_data WHERE from_address IS NOT NULL")
    unique_addresses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT from_asset) FROM viewblock_extension_data WHERE from_asset IS NOT NULL")
    unique_assets = cursor.fetchone()[0]
    
    cursor.execute("SELECT from_asset, COUNT(*) FROM viewblock_extension_data WHERE from_asset IS NOT NULL GROUP BY from_asset ORDER BY COUNT(*) DESC LIMIT 5")
    top_assets = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"Database Statistics:")
    logger.info(f"  Total transactions: {total_count}")
    logger.info(f"  Time range: {time_range[0]} to {time_range[1]}")
    logger.info(f"  Unique addresses: {unique_addresses}")
    logger.info(f"  Unique assets: {unique_assets}")
    logger.info(f"  Top assets:")
    for asset, count in top_assets:
        logger.info(f"    {asset}: {count} transactions")

def export_to_csv(db_path: str = 'viewblock_extension_data.db', output_file: str = None):
    """Export database to CSV format"""
    import csv
    
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'viewblock_extension_data_{timestamp}.csv'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM viewblock_extension_data ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(viewblock_extension_data)")
    columns = [column[1] for column in cursor.fetchall()]
    
    conn.close()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        writer.writerows(rows)
    
    logger.info(f"Exported {len(rows)} transactions to {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process ViewBlock extension data')
    parser.add_argument('json_file', help='JSON file exported from extension')
    parser.add_argument('--db', default='viewblock_extension_data.db', help='Database file path')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--export', help='Export to CSV file')
    
    args = parser.parse_args()
    
    if args.stats:
        get_database_stats(args.db)
    elif args.export:
        export_to_csv(args.db, args.export)
    else:
        process_extension_data(args.json_file, args.db)
        get_database_stats(args.db)

if __name__ == "__main__":
    main() 