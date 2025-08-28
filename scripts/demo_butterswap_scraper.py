#!/usr/bin/env python3
"""
Demo script for ButterSwap Web Scraper
Demonstrates how to use the scraper to find and copy addresses.
"""

import sys
import os

# Add listeners directory to path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "listeners"))
)

from butterswap_web_scraper import ButterSwapWebScraper


def demo_scraper_functionality():
    """Demonstrate the scraper's key functionality"""
    print("🚀 ButterSwap Web Scraper Demo")
    print("=" * 50)

    # Initialize scraper
    scraper = ButterSwapWebScraper()

    print("\n1. ✅ Scraper initialized successfully")
    print(f"   Database: {scraper.db_path}")
    print(f"   Explorer URL: {scraper.explorer_url}")

    print("\n2. 🔗 Supported chains:")
    for chain in scraper.supported_chains:
        affiliate_addr = scraper.shapeshift_affiliates[chain]
        print(f"   {chain.title():12} -> {affiliate_addr}")

    print("\n3. 🎯 ShapeShift affiliate detection:")
    test_addresses = [
        "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum affiliate
        "0x1234567890123456789012345678901234567890",  # Random address
        "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon affiliate
    ]

    for addr in test_addresses:
        is_affiliate = scraper.is_shapeshift_affiliate_transaction(
            {"from_address": addr}
        )
        status = "✅ AFFILIATE" if is_affiliate else "❌ Not affiliate"
        print(f"   {addr} -> {status}")

    print("\n4. 📊 Database statistics:")
    scraper.get_database_stats()

    print("\n5. 💡 Usage examples:")
    print("   # Basic scraping (Ethereum, 50 transactions)")
    print("   python listeners/butterswap_web_scraper.py --chains ethereum --max-tx 50")
    print("   ")
    print("   # Multi-chain scraping (headless mode)")
    print(
        "   python listeners/butterswap_web_scraper.py --chains ethereum polygon --max-tx 100 --headless"
    )
    print("   ")
    print("   # All supported chains")
    print(
        "   python listeners/butterswap_web_scraper.py --chains ethereum polygon optimism arbitrum base avalanche bsc --max-tx 50"
    )

    print("\n6. 🔍 How address copying works:")
    print("   - Scraper navigates to Butterswap explorer")
    print("   - Finds transaction elements on the page")
    print("   - Clicks on address elements to select them")
    print("   - Uses Cmd+C to copy full addresses to clipboard")
    print("   - Retrieves addresses from clipboard for accurate data")
    print("   - Falls back to direct text extraction if needed")

    print("\n7. 🎯 Affiliate transaction detection:")
    print("   - Scans for transactions involving ShapeShift addresses")
    print("   - Identifies fee transfers and affiliate patterns")
    print("   - Stores transaction details with full address information")
    print("   - Calculates affiliate fees and trading volumes")

    print("\n" + "=" * 50)
    print("🎉 Demo completed! The scraper is ready to use.")
    print("   Run with --headless flag for production use.")


def main():
    """Run the demo"""
    try:
        demo_scraper_functionality()
        return True
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
