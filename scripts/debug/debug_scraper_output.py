#!/usr/bin/env python3
"""
Debug Scraper Output Script

This script helps debug what data structure we're getting from the scraper.
"""

import asyncio
import json
from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper


async def debug_scraper_output():
    """Debug the scraper output to understand the data structure."""
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"

    print(f"🔍 Debugging scraper output for: {broker_url}")

    try:
        # Create scraper
        scraper = ChainflipComprehensiveScraper(broker_url)

        # Scrape data
        scraped_data = await scraper.scrape_with_full_addresses()

        if not scraped_data:
            print("❌ No data scraped")
            return

        print(f"✅ Scraped {len(scraped_data)} rows")

        # Look at first few rows to understand structure
        for i, row in enumerate(scraped_data[:3]):
            print(f"\n📋 Row {i + 1}:")
            print(f"   Keys: {list(row.keys())}")

            # Print all key-value pairs
            for key, value in row.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")

        # Look for rows with cell_0, cell_1, etc.
        table_rows = [row for row in scraped_data if "cell_0" in row]
        print(f"\n📊 Found {len(table_rows)} table rows")

        if table_rows:
            print(f"\n📋 First table row structure:")
            first_table_row = table_rows[0]
            for key, value in first_table_row.items():
                if key.startswith("cell_"):
                    print(f"   {key}: {value}")

        # Look for USD amounts
        print(f"\n💰 Looking for USD amounts...")
        usd_found = 0
        for row in scraped_data:
            for key, value in row.items():
                if (
                    isinstance(value, str)
                    and "$" in value
                    and any(char.isdigit() for char in value)
                ):
                    print(f"   Found USD in {key}: {value}")
                    usd_found += 1
                    if usd_found >= 5:  # Limit output
                        break
            if usd_found >= 5:
                break

        print(f"\n✅ Found {usd_found} potential USD amounts")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_scraper_output())
