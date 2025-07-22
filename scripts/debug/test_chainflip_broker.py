#!/usr/bin/env python3
"""
Test Chainflip Broker Data Collection
Verifies that we can scrape affiliate fee data from the ShapeShift broker
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from chainflip.chainflip_comprehensive_scraper import ChainflipComprehensiveScraper

async def test_chainflip_broker():
    """Test Chainflip broker data collection"""
    print("=== TESTING CHAINFLIP BROKER ===")
    
    # ShapeShift broker URL
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    print(f"Testing broker URL: {broker_url}")
    print(f"Expected broker address: cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi")
    
    try:
        # Create scraper
        scraper = ChainflipComprehensiveScraper(broker_url)
        
        print("\n1. Testing scraper initialization...")
        print("✅ Scraper created successfully")
        
        print("\n2. Testing data collection...")
        data = await scraper.scrape_with_full_addresses()
        
        print(f"✅ Data collection completed")
        print(f"📊 Records collected: {len(data) if data else 0}")
        
        if data:
            print("\n3. Sample data:")
            for i, record in enumerate(data[:3]):
                print(f"   Record {i+1}: {record}")
        
        # Save to database
        print("\n4. Saving to database...")
        conn = sqlite3.connect('test_chainflip.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_chainflip_fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                broker_address TEXT,
                swap_data TEXT,
                affiliate_fee REAL,
                affiliate_fee_asset TEXT,
                created_at INTEGER
            )
        ''')
        
        if data:
            for record in data:
                cursor.execute('''
                    INSERT INTO test_chainflip_fees 
                    (timestamp, broker_address, swap_data, affiliate_fee, affiliate_fee_asset, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    int(datetime.now().timestamp()),
                    "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
                    json.dumps(record),
                    0.0,  # Will need to extract from record
                    "FLIP",
                    int(datetime.now().timestamp())
                ))
            
            conn.commit()
            print(f"✅ Saved {len(data)} records to database")
        else:
            print("⚠️ No data collected")
        
        conn.close()
        
        return len(data) if data else 0
        
    except Exception as e:
        print(f"❌ Error testing Chainflip broker: {e}")
        return 0

if __name__ == "__main__":
    result = asyncio.run(test_chainflip_broker())
    print(f"\n=== CHAINFLIP TEST RESULT: {result} records ===") 