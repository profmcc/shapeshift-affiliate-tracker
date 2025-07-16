#!/usr/bin/env python3
"""
Fix Broker Attribution Script

This script fixes the broker attribution issue by re-scraping both brokers
and properly attributing transactions to the correct broker addresses.
"""

import asyncio
import sys
import sqlite3
from datetime import datetime
from chainflip_database import ChainflipDatabase
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


def get_existing_transaction_ids(database: ChainflipDatabase) -> set:
    """Get all existing transaction IDs from the database."""
    try:
        with sqlite3.connect(database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT transaction_id FROM transactions")
            return {row[0] for row in cursor.fetchall()}
    except Exception as e:
        print(f"Error getting existing transaction IDs: {e}")
        return set()


def update_broker_address(database: ChainflipDatabase, transaction_id: str, broker_address: str):
    """Update the broker address for a specific transaction."""
    try:
        with sqlite3.connect(database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transactions SET broker_address = ? WHERE transaction_id = ?",
                (broker_address, transaction_id)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating broker address for transaction {transaction_id}: {e}")
        return False


async def scrape_and_fix_broker(broker_url: str, database: ChainflipDatabase):
    """Scrape a broker and fix the attribution for its transactions."""
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
        
        # Get existing transaction IDs
        existing_ids = get_existing_transaction_ids(database)
        
        # Process scraped data
        updated_count = 0
        new_count = 0
        
        for row in scraped_data:
            # Check if this is a table row (has cell_0, cell_1, etc.)
            if 'cell_0' in row and 'cell_1' in row:
                transaction_id = row.get('cell_0', '').strip()
                
                if transaction_id in existing_ids:
                    # Update broker address for existing transaction
                    if update_broker_address(database, transaction_id, broker_address):
                        updated_count += 1
                        print(f"   🔄 Updated broker for transaction #{transaction_id}")
                else:
                    # This is a new transaction
                    full_addresses = row.get('full_addresses', [])
                    transaction = database.parse_transaction_data(row, full_addresses)
                    
                    if transaction:
                        transaction.broker_address = broker_address
                        if database.insert_transaction(transaction):
                            new_count += 1
                            print(f"   ✅ Added new transaction #{transaction_id}")
        
        print(f"   📊 Results for {broker_address}:")
        print(f"      Updated broker attribution: {updated_count}")
        print(f"      New transactions: {new_count}")
        
        return updated_count + new_count
        
    except Exception as e:
        print(f"   ❌ Error scraping {broker_address}: {e}")
        return 0


async def main():
    """Main function to fix broker attribution."""
    print(f"🔄 Fixing Broker Attribution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Initialize database
        database = ChainflipDatabase()
        
        # Show current stats
        print("\n📊 CURRENT DATABASE STATS:")
        database.print_stats()
        
        # Show current broker breakdown
        print(f"\n🏦 CURRENT BROKER BREAKDOWN:")
        try:
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
        
        # Fix broker attribution for each broker
        total_updated = 0
        
        for broker_url in BROKER_URLS:
            updated_count = await scrape_and_fix_broker(broker_url, database)
            total_updated += updated_count
        
        # Show final results
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Total transactions updated: {total_updated}")
        
        # Show updated stats
        print(f"\n📊 UPDATED DATABASE STATS:")
        database.print_stats()
        
        # Show updated broker breakdown
        print(f"\n🏦 UPDATED BROKER BREAKDOWN:")
        try:
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
        
        print(f"\n✅ Broker attribution fix completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during broker attribution fix: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 