#!/usr/bin/env python3
"""
Complete ShapeShift Affiliate Fee Scraper
Captures data from Chainflip broker webpage and integrates with existing system
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime
from chainflip.chainflip_comprehensive_scraper import ChainflipComprehensiveScraper

async def scrape_chainflip_broker_data():
    """Scrape all affiliate fee data from the Chainflip broker webpage"""
    print("=== SCRAPING CHAINFLIP BROKER DATA ===")
    
    # ShapeShift broker URL
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    print(f"Target URL: {broker_url}")
    print(f"Expected broker: cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi")
    
    try:
        # Create scraper
        scraper = ChainflipComprehensiveScraper(broker_url)
        
        print("\n1. Initializing scraper...")
        print("✅ Scraper ready")
        
        print("\n2. Scraping affiliate fee data...")
        start_time = time.time()
        
        data = await scraper.scrape_with_full_addresses()
        
        elapsed_time = time.time() - start_time
        print(f"✅ Scraping completed in {elapsed_time:.1f} seconds")
        print(f"📊 Total records: {len(data) if data else 0}")
        
        if data:
            print(f"\n3. Sample records:")
            for i, record in enumerate(data[:5]):
                print(f"   Record {i+1}: {record}")
        
        # Save to comprehensive database
        print(f"\n4. Saving to comprehensive database...")
        conn = sqlite3.connect('shapeshift_affiliate_fees_comprehensive.db')
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chainflip_affiliate_fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                swap_data TEXT,
                affiliate_fee REAL,
                affiliate_fee_asset TEXT,
                full_addresses TEXT,
                created_at INTEGER
            )
        ''')
        
        total_fees = 0.0
        saved_count = 0
        
        if data:
            for record in data:
                # Extract affiliate fee from cell_3
                fee_text = record.get('cell_3', '$0.00')
                fee_amount = 0.0
                
                try:
                    # Remove $ and convert to float
                    fee_clean = fee_text.replace('$', '').replace(',', '')
                    fee_amount = float(fee_clean)
                    total_fees += fee_amount
                except:
                    pass
                
                # Extract full addresses
                full_addresses = record.get('full_addresses', [])
                addresses_json = json.dumps(full_addresses)
                
                cursor.execute('''
                    INSERT INTO chainflip_affiliate_fees 
                    (timestamp, swap_data, affiliate_fee, affiliate_fee_asset, full_addresses, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    int(datetime.now().timestamp()),
                    json.dumps(record),
                    fee_amount,
                    "USD",
                    addresses_json,
                    int(datetime.now().timestamp())
                ))
                saved_count += 1
            
            conn.commit()
            print(f"✅ Saved {saved_count} records to database")
            print(f"💰 Total affiliate fees: ${total_fees:.2f}")
        else:
            print("⚠️ No data collected")
        
        conn.close()
        
        return {
            'records': len(data) if data else 0,
            'total_fees': total_fees,
            'elapsed_time': elapsed_time
        }
        
    except Exception as e:
        print(f"❌ Error scraping Chainflip broker: {e}")
        return {
            'records': 0,
            'total_fees': 0.0,
            'elapsed_time': 0,
            'error': str(e)
        }

def generate_summary_report():
    """Generate a summary report of all collected data"""
    print("\n=== COMPREHENSIVE AFFILIATE FEE REPORT ===")
    
    conn = sqlite3.connect('shapeshift_affiliate_fees_comprehensive.db')
    cursor = conn.cursor()
    
    # Check all tables
    tables = ['evm_cowswap_events', 'evm_zerox_events', 'evm_affiliate_transfers', 
              'chainflip_affiliate_fees', 'thorchain_affiliate_fees']
    
    total_records = 0
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table}: {count} records")
            total_records += count
        except:
            print(f"📊 {table}: 0 records (table not found)")
    
    # Calculate total fees from Chainflip
    try:
        cursor.execute("SELECT SUM(affiliate_fee) FROM chainflip_affiliate_fees")
        total_fees = cursor.fetchone()[0] or 0
        print(f"💰 Total Chainflip affiliate fees: ${total_fees:.2f}")
    except:
        print("💰 Total Chainflip affiliate fees: $0.00")
    
    conn.close()
    
    print(f"\n🎯 GRAND TOTAL: {total_records} records across all platforms")
    print("=" * 60)

async def main():
    """Main function to run the complete scraper"""
    print("🚀 Starting Complete ShapeShift Affiliate Fee Scraper")
    print("=" * 60)
    
    # Scrape Chainflip data
    result = await scrape_chainflip_broker_data()
    
    print(f"\n=== SCRAPING RESULTS ===")
    print(f"Records collected: {result['records']}")
    print(f"Total fees: ${result['total_fees']:.2f}")
    print(f"Time taken: {result['elapsed_time']:.1f} seconds")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    
    # Generate summary report
    generate_summary_report()
    
    print("\n✅ Complete scraper finished!")

if __name__ == "__main__":
    asyncio.run(main()) 