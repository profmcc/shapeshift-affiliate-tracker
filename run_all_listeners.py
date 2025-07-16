#!/usr/bin/env python3
"""
Comprehensive ShapeShift Affiliate Fee Tracker
Runs all three data collection systems: EVM, Chainflip, and THORChain
"""

import os
import sqlite3
import json
import time
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MAIN_DB_PATH = 'shapeshift_affiliate_fees_comprehensive.db'

# Global progress tracking
progress_stats = {
    'evm_blocks_total': 0,
    'evm_blocks_processed': 0,
    'chainflip_pages_total': 0,
    'chainflip_pages_processed': 0,
    'thorchain_batches_total': 0,
    'thorchain_batches_processed': 0,
    'start_time': time.time(),
    'current_system': 'none'
}

def print_progress():
    """Print current progress for all systems"""
    elapsed = time.time() - progress_stats['start_time']
    
    # Clear line and print progress
    sys.stdout.write('\r')
    sys.stdout.write(f"System: {progress_stats['current_system']} | ")
    
    if progress_stats['current_system'] == 'EVM':
        if progress_stats['evm_blocks_total'] > 0:
            percent = (progress_stats['evm_blocks_processed'] / progress_stats['evm_blocks_total']) * 100
            sys.stdout.write(f"EVM: {progress_stats['evm_blocks_processed']}/{progress_stats['evm_blocks_total']} blocks ({percent:.1f}%) | ")
    
    elif progress_stats['current_system'] == 'Chainflip':
        if progress_stats['chainflip_pages_total'] > 0:
            percent = (progress_stats['chainflip_pages_processed'] / progress_stats['chainflip_pages_total']) * 100
            sys.stdout.write(f"Chainflip: {progress_stats['chainflip_pages_processed']}/{progress_stats['chainflip_pages_total']} pages ({percent:.1f}%) | ")
    
    elif progress_stats['current_system'] == 'THORChain':
        if progress_stats['thorchain_batches_total'] > 0:
            percent = (progress_stats['thorchain_batches_processed'] / progress_stats['thorchain_batches_total']) * 100
            sys.stdout.write(f"THORChain: {progress_stats['thorchain_batches_processed']}/{progress_stats['thorchain_batches_total']} batches ({percent:.1f}%) | ")
    
    sys.stdout.write(f"Elapsed: {elapsed:.0f}s")
    sys.stdout.flush()

def setup_comprehensive_database():
    """Create the comprehensive database with all tables"""
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # EVM events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evm_cowswap_events (
            tx_hash TEXT,
            block_number INTEGER,
            event_type TEXT,
            event_data TEXT,
            timestamp INTEGER,
            chain_id INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evm_zerox_events (
            tx_hash TEXT,
            block_number INTEGER,
            event_type TEXT,
            event_data TEXT,
            timestamp INTEGER,
            chain_id INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evm_affiliate_transfers (
            tx_hash TEXT,
            block_number INTEGER,
            token_address TEXT,
            from_address TEXT,
            to_address TEXT,
            amount TEXT,
            timestamp INTEGER,
            chain_id INTEGER
        )
    ''')
    
    # Chainflip data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chainflip_affiliate_fees (
            broker_name TEXT,
            volume_usd REAL,
            affiliate_fee_usd REAL,
            transaction_count INTEGER,
            date TEXT,
            timestamp INTEGER
        )
    ''')
    
    # THORChain data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thorchain_affiliate_fees (
            tx_hash TEXT,
            block_height INTEGER,
            affiliate_fee REAL,
            asset TEXT,
            pool TEXT,
            timestamp INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Comprehensive affiliate fee database setup complete")

def run_evm_listener():
    """Run EVM listener with progress tracking"""
    logger.info("Starting EVM listener...")
    progress_stats['current_system'] = 'EVM'
    
    try:
        # Import and run the EVM listener
        from evm_listeners.run_affiliate_listener_progress import main as evm_main
        
        # Set up progress tracking
        progress_stats['evm_blocks_total'] = 576  # Based on previous run
        progress_stats['evm_blocks_processed'] = 0
        
        # Run EVM listener
        evm_main()
        
        logger.info("EVM listener completed successfully")
        
    except Exception as e:
        logger.error(f"Error running EVM listener: {e}")

def run_chainflip_scraper():
    """Run Chainflip scraper with progress tracking"""
    logger.info("Starting Chainflip scraper...")
    progress_stats['current_system'] = 'Chainflip'
    
    try:
        # Check if chainflip scraper exists
        scraper_path = 'chainflip/chainflip_comprehensive_scraper.py'
        if os.path.exists(scraper_path):
            # Run chainflip scraper
            result = subprocess.run(['python', scraper_path], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Chainflip scraper completed successfully")
            else:
                logger.error(f"Chainflip scraper failed: {result.stderr}")
        else:
            logger.warning("Chainflip scraper not found, skipping")
            
    except Exception as e:
        logger.error(f"Error running Chainflip scraper: {e}")

def run_thorchain_listener():
    """Run THORChain listener with progress tracking"""
    logger.info("Starting THORChain listener...")
    progress_stats['current_system'] = 'THORChain'
    
    try:
        # Check if THORChain listener exists
        listener_path = 'thorchain/run_thorchain_listener.py'
        if os.path.exists(listener_path):
            # Run THORChain listener
            result = subprocess.run(['python', listener_path], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("THORChain listener completed successfully")
            else:
                logger.error(f"THORChain listener failed: {result.stderr}")
        else:
            logger.warning("THORChain listener not found, skipping")
            
    except Exception as e:
        logger.error(f"Error running THORChain listener: {e}")

def merge_databases():
    """Merge data from all individual databases into the comprehensive database"""
    logger.info("Merging data from all databases...")
    
    try:
        # Connect to comprehensive database
        main_conn = sqlite3.connect(MAIN_DB_PATH)
        main_cursor = main_conn.cursor()
        
        # Merge EVM data
        evm_db_path = 'shapeshift_affiliate_fees_progress.db'
        if os.path.exists(evm_db_path):
            evm_conn = sqlite3.connect(evm_db_path)
            evm_cursor = evm_conn.cursor()
            
            # Copy CowSwap events
            evm_cursor.execute("SELECT * FROM cowswap_events")
            cowswap_events = evm_cursor.fetchall()
            for event in cowswap_events:
                main_cursor.execute('''
                    INSERT INTO evm_cowswap_events 
                    (tx_hash, block_number, event_type, event_data, timestamp, chain_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (*event, 137))  # Assuming Polygon for now
            
            # Copy 0x events
            evm_cursor.execute("SELECT * FROM zerox_events")
            zerox_events = evm_cursor.fetchall()
            for event in zerox_events:
                main_cursor.execute('''
                    INSERT INTO evm_zerox_events 
                    (tx_hash, block_number, event_type, event_data, timestamp, chain_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (*event, 137))
            
            # Copy affiliate transfers
            evm_cursor.execute("SELECT * FROM affiliate_transfers")
            affiliate_transfers = evm_cursor.fetchall()
            for transfer in affiliate_transfers:
                main_cursor.execute('''
                    INSERT INTO evm_affiliate_transfers 
                    (tx_hash, block_number, token_address, from_address, to_address, amount, timestamp, chain_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (*transfer, 137))
            
            evm_conn.close()
            logger.info(f"Merged {len(cowswap_events)} CowSwap events, {len(zerox_events)} 0x events, {len(affiliate_transfers)} affiliate transfers")
        
        # Merge Chainflip data
        chainflip_db_path = 'chainflip_affiliate_fees.db'
        if os.path.exists(chainflip_db_path):
            chainflip_conn = sqlite3.connect(chainflip_db_path)
            chainflip_cursor = chainflip_conn.cursor()
            
            chainflip_cursor.execute("SELECT * FROM affiliate_fees")
            chainflip_data = chainflip_cursor.fetchall()
            for row in chainflip_data:
                main_cursor.execute('''
                    INSERT INTO chainflip_affiliate_fees 
                    (broker_name, volume_usd, affiliate_fee_usd, transaction_count, date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', row)
            
            chainflip_conn.close()
            logger.info(f"Merged {len(chainflip_data)} Chainflip records")
        
        # Merge THORChain data
        thorchain_db_path = 'thorchain_affiliate_fees.db'
        if os.path.exists(thorchain_db_path):
            thorchain_conn = sqlite3.connect(thorchain_db_path)
            thorchain_cursor = thorchain_conn.cursor()
            
            thorchain_cursor.execute("SELECT * FROM affiliate_fees")
            thorchain_data = thorchain_cursor.fetchall()
            for row in thorchain_data:
                main_cursor.execute('''
                    INSERT INTO thorchain_affiliate_fees 
                    (tx_hash, block_height, affiliate_fee, asset, pool, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', row)
            
            thorchain_conn.close()
            logger.info(f"Merged {len(thorchain_data)} THORChain records")
        
        main_conn.commit()
        main_conn.close()
        logger.info("Database merge completed successfully")
        
    except Exception as e:
        logger.error(f"Error merging databases: {e}")

def print_final_summary():
    """Print comprehensive summary of all collected data"""
    logger.info("Generating comprehensive summary...")
    
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    
    # EVM Summary
    cursor.execute("SELECT COUNT(*) FROM evm_cowswap_events")
    cowswap_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM evm_zerox_events")
    zerox_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM evm_affiliate_transfers")
    affiliate_count = cursor.fetchone()[0]
    
    # Chainflip Summary
    cursor.execute("SELECT COUNT(*) FROM chainflip_affiliate_fees")
    chainflip_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(affiliate_fee_usd) FROM chainflip_affiliate_fees")
    chainflip_total = cursor.fetchone()[0] or 0
    
    # THORChain Summary
    cursor.execute("SELECT COUNT(*) FROM thorchain_affiliate_fees")
    thorchain_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(affiliate_fee) FROM thorchain_affiliate_fees")
    thorchain_total = cursor.fetchone()[0] or 0
    
    conn.close()
    
    total_time = time.time() - progress_stats['start_time']
    
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE AFFILIATE FEE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total collection time: {total_time:.1f} seconds")
    logger.info("")
    logger.info("EVM Data (Ethereum/Polygon):")
    logger.info(f"  CowSwap events: {cowswap_count}")
    logger.info(f"  0x Protocol events: {zerox_count}")
    logger.info(f"  Affiliate transfers: {affiliate_count}")
    logger.info("")
    logger.info("Chainflip Data:")
    logger.info(f"  Total records: {chainflip_count}")
    logger.info(f"  Total affiliate fees: ${chainflip_total:.2f}")
    logger.info("")
    logger.info("THORChain Data:")
    logger.info(f"  Total records: {thorchain_count}")
    logger.info(f"  Total affiliate fees: {thorchain_total:.6f}")
    logger.info("")
    logger.info(f"GRAND TOTAL: {cowswap_count + zerox_count + affiliate_count + chainflip_count + thorchain_count} records")
    logger.info("=" * 60)

def main():
    """Main function to run all data collection systems"""
    logger.info("Starting comprehensive ShapeShift affiliate fee tracker")
    logger.info("This will collect data from EVM, Chainflip, and THORChain")
    
    # Setup comprehensive database
    setup_comprehensive_database()
    
    # Run each system
    run_evm_listener()
    run_chainflip_scraper()
    run_thorchain_listener()
    
    # Merge all databases
    merge_databases()
    
    # Print final summary
    print_final_summary()
    
    logger.info("Comprehensive affiliate fee collection complete!")

if __name__ == "__main__":
    main() 