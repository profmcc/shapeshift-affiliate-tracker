#!/usr/bin/env python3
"""
Chainflip Database Update Script

Simple script to update the Chainflip transaction database.
Run this script regularly to capture new transactions.
"""

import asyncio
import sys
from datetime import datetime
from chainflip_database import ChainflipDatabaseUpdater
from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper


async def main():
    """Main update function."""
    print(f"🔄 Chainflip Database Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Scrape the new broker URL
        updater = ChainflipDatabaseUpdater()
        updater.scraper = ChainflipComprehensiveScraper(
            "https://scan.chainflip.io/brokers/cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8"
        )
        await updater.update_database()
        
        print(f"\n✅ Update completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 