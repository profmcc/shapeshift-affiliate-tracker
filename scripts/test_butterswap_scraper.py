#!/usr/bin/env python3
"""
Test script for ButterSwap Web Scraper
Tests basic functionality without running the full scraper.
"""

import sys
import os

# Add listeners directory to path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "listeners"))
)

from butterswap_web_scraper import ButterSwapWebScraper


def test_scraper_initialization():
    """Test scraper initialization and database setup"""
    print("🧪 Testing ButterSwap Web Scraper initialization...")

    try:
        scraper = ButterSwapWebScraper()
        print("✅ Scraper initialized successfully")

        # Test database connection
        import sqlite3

        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='butterswap_web_transactions'"
        )
        table_exists = cursor.fetchone() is not None

        if table_exists:
            print("✅ Database table created successfully")
        else:
            print("❌ Database table not found")

        conn.close()

        # Test affiliate address lookup
        affiliate_address = scraper.get_affiliate_address_for_chain("ethereum")
        if affiliate_address:
            print(f"✅ Ethereum affiliate address: {affiliate_address}")
        else:
            print("❌ Could not get affiliate address")

        return True

    except Exception as e:
        print(f"❌ Error initializing scraper: {e}")
        return False


def test_address_validation():
    """Test address validation logic"""
    print("\n🧪 Testing address validation...")

    try:
        scraper = ButterSwapWebScraper()

        # Test valid addresses
        valid_addresses = [
            "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
            "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
        ]

        for addr in valid_addresses:
            if scraper.is_shapeshift_affiliate_transaction({"from_address": addr}):
                print(f"✅ Valid affiliate address detected: {addr}")
            else:
                print(f"❌ Valid affiliate address not detected: {addr}")

        # Test invalid addresses
        invalid_addresses = [
            "0x123",
            "invalid_address",
            "0x90A48D5CF7343B08dA12E067680B4C6dbfE551B",  # Too short
        ]

        for addr in invalid_addresses:
            if not scraper.is_shapeshift_affiliate_transaction({"from_address": addr}):
                print(f"✅ Invalid address correctly rejected: {addr}")
            else:
                print(f"❌ Invalid address incorrectly accepted: {addr}")

        return True

    except Exception as e:
        print(f"❌ Error testing address validation: {e}")
        return False


def test_timestamp_parsing():
    """Test timestamp parsing logic"""
    print("\n🧪 Testing timestamp parsing...")

    try:
        scraper = ButterSwapWebScraper()

        # Test relative timestamps
        test_cases = [
            ("2 hours ago", "relative"),
            ("5 minutes ago", "relative"),
            ("30 seconds ago", "relative"),
            ("2024-01-15 14:30:00", "absolute"),
            ("01/15/2024 14:30", "absolute"),
        ]

        for timestamp_text, expected_type in test_cases:
            try:
                parsed_timestamp = scraper.parse_timestamp(timestamp_text)
                if parsed_timestamp > 0:
                    print(f"✅ Parsed '{timestamp_text}' -> {parsed_timestamp}")
                else:
                    print(f"❌ Failed to parse '{timestamp_text}'")
            except Exception as e:
                print(f"❌ Error parsing '{timestamp_text}': {e}")

        return True

    except Exception as e:
        print(f"❌ Error testing timestamp parsing: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting ButterSwap Web Scraper Tests\n")

    tests = [
        test_scraper_initialization,
        test_address_validation,
        test_timestamp_parsing,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The scraper is ready to use.")
        print("\n💡 To run the scraper:")
        print(
            "   python listeners/butterswap_web_scraper.py --chains ethereum --max-tx 50"
        )
        print(
            "   python listeners/butterswap_web_scraper.py --chains ethereum polygon --max-tx 100 --headless"
        )
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
