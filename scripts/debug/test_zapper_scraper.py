#!/usr/bin/env python3
"""
Test script for Zapper wallet scraper with shorter timeouts.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from zapper_wallet_scraper import ZapperWalletScraper, logger


async def test_scraper():
    """Test the scraper with a simple URL and shorter timeouts."""
    logger.info("🧪 Testing Zapper scraper...")

    # Use a shorter timeout for testing
    scraper = ZapperWalletScraper(headless=True, timeout=15000)

    # Test with a simple Zapper URL (single address)
    test_url = (
        "https://zapper.xyz/0x90a48d5cf7343b08da12e067680b4c6dbfe551be?tab=wallet"
    )

    logger.info(f"Testing with URL: {test_url}")

    try:
        result = await scraper.scrape_wallet_data(test_url, "test_data")

        if result:
            csv_file, json_file = result
            logger.info("✅ Test successful!")
            logger.info(f"Files created: {csv_file}, {json_file}")

            # Try to read and display some data
            import pandas as pd

            df = pd.read_csv(csv_file)
            logger.info(f"📊 Extracted {len(df)} tokens")

            if len(df) > 0:
                logger.info("📋 Sample data:")
                for i, row in df.head(3).iterrows():
                    logger.info(f"   {row['Token']}: {row['Value']}")

            return True
        else:
            logger.error("❌ Test failed - no data extracted")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)
