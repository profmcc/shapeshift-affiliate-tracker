#!/usr/bin/env python3
"""
Update All Brokers Script

This script scrapes and updates the database with transactions from all known
ShapeShift affiliate brokers to get the complete volume picture.
"""

import asyncio
import sys
from datetime import datetime
from chainflip_database import ChainflipDatabase, ChainflipDatabaseUpdater
from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper


# Known ShapeShift affiliate broker addresses
BROKER_URLS = [
    "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
    "https://scan.chainflip.io/brokers/cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8"
]

# Broker address mappings (extract from URLs)
BROKER_ADDRESSES = {
    "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi": "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
    "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8": "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8"
}


async def scrape_broker(broker_url: str, database: ChainflipDatabase):
    """Scrape a single broker and add transactions to database."""
    broker_address = BROKER_ADDRESSES[broker_url.split('/')[-1]]
    
    print(f"\n🔍 Scraping broker: {broker_address}")
    print(f"   URL: {broker_url}")
    
    try:
        # Create scraper for this broker
        scraper = ChainflipComprehensiveScraper(broker_url)
        
        # Scrape data
        scraped_data = await scraper.scrape_with_full_addresses()
        
        if not scraped_data:
            print(f"   ❌ No data scraped for {broker_address}")
            return 0
        
        # Process and insert transactions
        new_transactions = 0
        skipped_transactions = 0
        
        for row in scraped_data:
            # Check if this is a table row (has cell_0, cell_1, etc.)
            if 'cell_0' in row and 'cell_1' in row:
                # Extract full addresses if available
                full_addresses = row.get('full_addresses', [])
                
                # Parse transaction data
                transaction = database.parse_transaction_data(row, full_addresses)
                
                if transaction:
                    # Update broker address for this transaction
                    transaction.broker_address = broker_address
                    
                    # Try to insert transaction
                    if database.insert_transaction(transaction):
                        new_transactions += 1
                        print(f"   ✅ Added transaction #{transaction.transaction_id}")
                    else:
                        skipped_transactions += 1
                        print(f"   ⏭️ Skipped duplicate transaction #{transaction.transaction_id}")
        
        print(f"   📊 Results for {broker_address}:")
        print(f"      New transactions: {new_transactions}")
        print(f"      Skipped duplicates: {skipped_transactions}")
        
        return new_transactions
        
    except Exception as e:
        print(f"   ❌ Error scraping {broker_address}: {e}")
        return 0


async def main():
    """Main function to scrape all brokers."""
    print(f"🔄 Chainflip All Brokers Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Initialize database
        database = ChainflipDatabase()
        
        # Show current stats
        print("\n📊 CURRENT DATABASE STATS:")
        database.print_stats()
        
        # Scrape each broker
        total_new = 0
        
        for broker_url in BROKER_URLS:
            new_count = await scrape_broker(broker_url, database)
            total_new += new_count
        
        # Update metadata
        latest_id = database.get_latest_transaction_id()
        stats = database.get_database_stats()
        database.update_metadata(latest_id, stats['total_transactions'])
        
        # Show final results
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Total new transactions added: {total_new}")
        print(f"   Total transactions in database: {stats['total_transactions']:,}")
        
        # Show updated stats
        print(f"\n📊 UPDATED DATABASE STATS:")
        database.print_stats()
        
        # Show breakdown by broker
        print(f"\n🏦 BROKER BREAKDOWN:")
        try:
            import sqlite3
            with sqlite3.connect(database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        broker_address,
                        COUNT(*) as tx_count,
                        SUM(from_amount_usd) as total_volume,
                        SUM(commission_usd) as total_commissions,
                        SUM(affiliate_fee_usd) as total_affiliate_fees
                    FROM transactions 
                    WHERE status = 'Success'
                    GROUP BY broker_address
                    ORDER BY total_volume DESC
                """)
                
                rows = cursor.fetchall()
                for row in rows:
                    broker, count, volume, commissions, affiliate_fees = row
                    print(f"   {broker}:")
                    print(f"      Transactions: {count:,}")
                    print(f"      Volume: ${volume:,.2f}")
                    print(f"      Broker Fees: ${commissions:,.2f}")
                    print(f"      Affiliate Fees: ${affiliate_fees:,.2f}")
                    print()
        
        except Exception as e:
            print(f"   Error getting broker breakdown: {e}")
        
        print(f"\n✅ Update completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 