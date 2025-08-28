#!/usr/bin/env python3
"""
Debug Chainflip Database

Debug version to see what's happening with data parsing and insertion.
"""

import asyncio
from chainflip_database import ChainflipDatabase, ChainflipDatabaseUpdater


async def debug_database():
    """Debug the database update process."""
    print("🔍 DEBUGGING CHAINFLIP DATABASE")
    print("=" * 50)

    # Initialize database
    database = ChainflipDatabase()

    # Initialize updater
    updater = ChainflipDatabaseUpdater()

    # Scrape data
    print("\n1. Scraping data...")
    scraped_data = await updater.scraper.scrape_with_full_addresses()

    if not scraped_data:
        print("❌ No data scraped")
        return

    print(f"✅ Scraped {len(scraped_data)} data items")

    # Debug each row
    print("\n2. Debugging data parsing...")
    table_rows = [row for row in scraped_data if "cell_0" in row and "cell_1" in row]
    print(f"Found {len(table_rows)} table rows")

    for i, row in enumerate(table_rows[:3]):  # Debug first 3 rows
        print(f"\n--- Row {i+1} ---")
        print(f"Row data: {row}")

        # Extract full addresses
        full_addresses = row.get("full_addresses", [])
        print(f"Full addresses: {full_addresses}")

        # Try to parse transaction
        transaction = database.parse_transaction_data(row, full_addresses)
        print(f"Parsed transaction: {transaction}")

        if transaction:
            print(f"Transaction ID: {transaction.transaction_id}")
            print(f"From: {transaction.from_address}")
            print(f"To: {transaction.to_address}")
            print(f"Hash ID: {transaction.hash_id}")

            # Try to insert
            success = database.insert_transaction(transaction)
            print(f"Insert success: {success}")
        else:
            print("❌ Failed to parse transaction")


if __name__ == "__main__":
    asyncio.run(debug_database())
