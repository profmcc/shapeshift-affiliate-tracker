#!/usr/bin/env python3
"""
Test Portals Listener
Test script to verify Portals data collection and show statistics
"""

import sqlite3
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_portals_database():
    """Test Portals database and show statistics"""
    portals_db = "portals_affiliate_events.db"
    comprehensive_db = "comprehensive_affiliate_data.db"

    print("=== Portals Data Test ===")

    # Check if Portals database exists
    if os.path.exists(portals_db):
        print(f"✅ Portals database found: {portals_db}")

        conn = sqlite3.connect(portals_db)
        cursor = conn.cursor()

        # Get basic statistics
        cursor.execute("SELECT COUNT(*) FROM portals_affiliate_events2")
        total_events = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT tx_hash) FROM portals_affiliate_events2")
        unique_txs = cursor.fetchone()[0]

        cursor.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM portals_affiliate_events2"
        )
        time_range = cursor.fetchone()
        min_time, max_time = time_range if time_range[0] else (0, 0)

        print(f"📊 Portals Events: {total_events}")
        print(f"🔗 Unique Transactions: {unique_txs}")
        if min_time and max_time:
            print(
                f"⏰ Time Range: {datetime.fromtimestamp(min_time)} - {datetime.fromtimestamp(max_time)}"
            )

        # Show sample data
        cursor.execute(
            "SELECT tx_hash, input_token, output_token, affiliate_amount FROM portals_affiliate_events2 LIMIT 3"
        )
        sample_data = cursor.fetchall()

        print("\n📋 Sample Portals Events:")
        for tx_hash, input_token, output_token, affiliate_amount in sample_data:
            print(f"  TX: {tx_hash[:20]}...")
            print(f"     Input: {input_token}")
            print(f"     Output: {output_token}")
            print(f"     Affiliate Fee: {affiliate_amount}")
            print()

        conn.close()
    else:
        print(f"❌ Portals database not found: {portals_db}")

    # Check comprehensive database
    if os.path.exists(comprehensive_db):
        print(f"✅ Comprehensive database found: {comprehensive_db}")

        conn = sqlite3.connect(comprehensive_db)
        cursor = conn.cursor()

        # Get Portals statistics from comprehensive database
        cursor.execute("SELECT COUNT(*) FROM portals_fees")
        portals_count = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(affiliate_fee) FROM portals_fees")
        total_fees = cursor.fetchone()[0] or 0

        cursor.execute("SELECT chain, COUNT(*) FROM portals_fees GROUP BY chain")
        chain_stats = cursor.fetchall()

        print(f"📊 Comprehensive Portals Data:")
        print(f"  Total Events: {portals_count}")
        print(f"  Total Fees: {total_fees:.6f}")
        print(f"  Chains: {[chain for chain, _ in chain_stats]}")

        # Show summary statistics
        cursor.execute(
            "SELECT chain, protocol, total_fees_usd, transaction_count FROM summary_stats WHERE chain = 'Portals'"
        )
        summary = cursor.fetchone()
        if summary:
            chain, protocol, total_fees_usd, tx_count = summary
            print(
                f"  Summary: {chain} ({protocol}) - ${total_fees_usd:.2f} from {tx_count} transactions"
            )

        conn.close()
    else:
        print(f"❌ Comprehensive database not found: {comprehensive_db}")


def test_portals_listener_requirements():
    """Test if Portals listener requirements are met"""
    print("\n=== Portals Listener Requirements ===")

    # Check Infura API key
    infura_key = os.getenv("INFURA_API_KEY")
    if infura_key and infura_key != "your_infura_api_key_here":
        print("✅ INFURA_API_KEY is set")
    else:
        print(
            "❌ INFURA_API_KEY not set - set environment variable to run Portals listener"
        )

    # Check required packages
    try:
        import requests

        print("✅ requests package available")
    except ImportError:
        print("❌ requests package not available - install with: pip install requests")

    try:
        import sqlite3

        print("✅ sqlite3 package available")
    except ImportError:
        print("❌ sqlite3 package not available")


def show_portals_affiliate_addresses():
    """Show ShapeShift affiliate addresses for Portals"""
    print("\n=== ShapeShift Portals Affiliate Addresses ===")

    addresses = {
        "Ethereum": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
        "Polygon": "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
        "Arbitrum": "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
        "Optimism": "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
        "Base": "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
    }

    for chain, address in addresses.items():
        print(f"  {chain}: {address}")


def main():
    """Main test function"""
    print("🔍 Testing Portals Listener and Data Collection")
    print("=" * 50)

    test_portals_database()
    test_portals_listener_requirements()
    show_portals_affiliate_addresses()

    print("\n" + "=" * 50)
    print("📝 Next Steps:")
    print("1. Set INFURA_API_KEY environment variable")
    print("2. Run: python run_portals_listener.py")
    print("3. Run: python run_comprehensive_data_collection.py")
    print("4. Check comprehensive_affiliate_data.db for unified data")


if __name__ == "__main__":
    main()
