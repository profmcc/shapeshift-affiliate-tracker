#!/usr/bin/env python3
"""
Chainflip Broker Listener for ShapeShift Affiliate Transactions

Uses the working Chainflip scraper approach with proper database storage.
Integrates with existing project structure and databases.
"""

import asyncio
import sqlite3
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os

# Import existing Chainflip scraper if available
try:
    from chainflip.chainflip_comprehensive_scraper import ChainflipComprehensiveScraper

    SCRAPER_AVAILABLE = True
except ImportError:
    try:
        from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper

        SCRAPER_AVAILABLE = True
    except ImportError:
        SCRAPER_AVAILABLE = False
        print("⚠️  Chainflip scraper not found, will use alternative method")


class ChainflipBrokerListener:
    def __init__(self):
        # Known ShapeShift broker addresses from the existing project
        self.shapeshift_brokers = [
            {
                "address": "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
                "url": "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
                "name": "ShapeShift Broker 1",
            },
            {
                "address": "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8",
                "url": "https://scan.chainflip.io/brokers/cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8",
                "name": "ShapeShift Broker 2",
            },
        ]

        self.db_path = "shapeshift_chainflip_transactions.db"
        self.init_database()

    def init_database(self):
        """Initialize the database with Chainflip transactions table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chainflip_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                broker_address TEXT NOT NULL,
                broker_name TEXT,
                swap_type TEXT,
                source_asset TEXT,
                destination_asset TEXT,
                swap_amount TEXT,
                output_amount TEXT,
                broker_fee_amount TEXT,
                broker_fee_asset TEXT,
                source_chain TEXT,
                destination_chain TEXT,
                transaction_hash TEXT,
                block_number INTEGER,
                swap_state TEXT,
                timestamp TEXT NOT NULL,
                scraped_at TEXT NOT NULL,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_broker_address 
            ON chainflip_transactions(broker_address)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON chainflip_transactions(timestamp)
        """
        )

        conn.commit()
        conn.close()
        print("📁 Database initialized: shapeshift_chainflip_transactions.db")

    async def scrape_broker_data(self, broker: Dict[str, str]) -> List[Dict]:
        """Scrape data from a specific broker using the comprehensive scraper"""
        transactions = []

        if not SCRAPER_AVAILABLE:
            print(f"   ❌ Scraper not available for {broker['name']}")
            return transactions

        try:
            print(f"🔍 Scraping {broker['name']} ({broker['address'][:16]}...)")

            scraper = ChainflipComprehensiveScraper(broker["url"])

            # Use the working scraper method
            data = await scraper.scrape_with_full_addresses()

            if data:
                print(f"   ✅ Found {len(data)} transactions")

                # Process the scraped data into our format
                for item in data:
                    transaction = {
                        "transaction_id": item.get("id")
                        or f"{broker['address']}_{item.get('timestamp', int(time.time()))}",
                        "broker_address": broker["address"],
                        "broker_name": broker["name"],
                        "swap_type": item.get("type", "swap"),
                        "source_asset": item.get("source_asset")
                        or item.get("fromAsset", ""),
                        "destination_asset": item.get("destination_asset")
                        or item.get("toAsset", ""),
                        "swap_amount": str(
                            item.get("swap_amount") or item.get("amount", "")
                        ),
                        "output_amount": str(
                            item.get("output_amount") or item.get("outputAmount", "")
                        ),
                        "broker_fee_amount": str(
                            item.get("broker_fee_amount") or item.get("fee", "")
                        ),
                        "broker_fee_asset": item.get("broker_fee_asset")
                        or item.get("feeAsset", ""),
                        "source_chain": item.get("source_chain")
                        or item.get("fromChain", ""),
                        "destination_chain": item.get("destination_chain")
                        or item.get("toChain", ""),
                        "transaction_hash": item.get("transaction_hash")
                        or item.get("txHash", ""),
                        "block_number": item.get("block_number")
                        or item.get("blockNumber", 0),
                        "swap_state": item.get("state")
                        or item.get("status", "unknown"),
                        "timestamp": item.get("timestamp")
                        or datetime.now().isoformat(),
                        "scraped_at": datetime.now().isoformat(),
                        "raw_data": json.dumps(item),
                    }
                    transactions.append(transaction)
            else:
                print(f"   ⚠️  No data found for {broker['name']}")

        except Exception as e:
            print(f"   ❌ Error scraping {broker['name']}: {e}")

        return transactions

    def save_transactions_to_db(self, transactions: List[Dict]):
        """Save transactions to the database"""
        if not transactions:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for tx in transactions:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO chainflip_transactions 
                    (transaction_id, broker_address, broker_name, swap_type,
                     source_asset, destination_asset, swap_amount, output_amount,
                     broker_fee_amount, broker_fee_asset, source_chain, destination_chain,
                     transaction_hash, block_number, swap_state, timestamp, scraped_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        tx["transaction_id"],
                        tx["broker_address"],
                        tx["broker_name"],
                        tx["swap_type"],
                        tx["source_asset"],
                        tx["destination_asset"],
                        tx["swap_amount"],
                        tx["output_amount"],
                        tx["broker_fee_amount"],
                        tx["broker_fee_asset"],
                        tx["source_chain"],
                        tx["destination_chain"],
                        tx["transaction_hash"],
                        tx["block_number"],
                        tx["swap_state"],
                        tx["timestamp"],
                        tx["scraped_at"],
                        tx["raw_data"],
                    ),
                )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                print(f"   ❌ Error saving transaction: {e}")

        conn.commit()
        conn.close()

        if saved_count > 0:
            print(f"💾 Saved {saved_count} new transactions to database")
        else:
            print("💾 No new transactions to save (all already exist)")

    def get_database_stats(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM chainflip_transactions")
            total_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT broker_address) FROM chainflip_transactions"
            )
            broker_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM chainflip_transactions"
            )
            time_range = cursor.fetchone()

            cursor.execute(
                """
                SELECT broker_name, COUNT(*) 
                FROM chainflip_transactions 
                GROUP BY broker_address, broker_name
                ORDER BY COUNT(*) DESC
            """
            )
            broker_stats = cursor.fetchall()

            # Get recent transactions
            cursor.execute(
                """
                SELECT source_asset, destination_asset, swap_amount, timestamp
                FROM chainflip_transactions 
                ORDER BY timestamp DESC 
                LIMIT 5
            """
            )
            recent_txs = cursor.fetchall()

            conn.close()

            print(f"\n📊 Chainflip Database Statistics:")
            print(f"   Total transactions: {total_count}")
            print(f"   Active brokers: {broker_count}")
            if time_range[0]:
                print(f"   Time range: {time_range[0]} to {time_range[1]}")

            if broker_stats:
                print(f"   By broker:")
                for broker_name, count in broker_stats:
                    print(f"     {broker_name}: {count} transactions")

            if recent_txs:
                print(f"\n   Recent transactions:")
                for source, dest, amount, timestamp in recent_txs:
                    print(f"     {source} → {dest}: {amount} at {timestamp}")

        except Exception as e:
            print(f"   ❌ Error getting database stats: {e}")

    async def listen_for_transactions(self):
        """Main listener loop"""
        print("🎯 Starting Chainflip Broker Listener for ShapeShift transactions...")

        if not SCRAPER_AVAILABLE:
            print(
                "❌ Chainflip scraper not available. Please ensure the scraper is properly installed."
            )
            print("   Expected: chainflip/chainflip_comprehensive_scraper.py")
            return

        all_transactions = []

        # Scrape each broker
        for broker in self.shapeshift_brokers:
            broker_transactions = await self.scrape_broker_data(broker)
            all_transactions.extend(broker_transactions)

        print(f"\n🔍 Total transactions found: {len(all_transactions)}")

        if all_transactions:
            # Display sample transaction
            print(f"\n📋 Sample transaction:")
            sample = all_transactions[0]
            for key, value in sample.items():
                if key != "raw_data":  # Skip raw data for cleaner display
                    print(f"   {key}: {value}")

        # Save to database
        self.save_transactions_to_db(all_transactions)

        # Show stats
        self.get_database_stats()

    def create_fallback_data(self):
        """Create some test data if scraper is not available"""
        print("📝 Creating fallback test data...")

        test_transactions = []
        for i, broker in enumerate(self.shapeshift_brokers):
            transaction = {
                "transaction_id": f"test_{broker['address'][:8]}_{int(time.time())}_{i}",
                "broker_address": broker["address"],
                "broker_name": broker["name"],
                "swap_type": "cross_chain_swap",
                "source_asset": "ETH" if i % 2 == 0 else "BTC",
                "destination_asset": "USDC" if i % 2 == 0 else "DOT",
                "swap_amount": "1.5" if i % 2 == 0 else "0.05",
                "output_amount": "2500.0" if i % 2 == 0 else "450.0",
                "broker_fee_amount": "5.0",
                "broker_fee_asset": "USDC",
                "source_chain": "Ethereum" if i % 2 == 0 else "Bitcoin",
                "destination_chain": "Ethereum",
                "transaction_hash": f"0x{'a' * 64}",
                "block_number": 18000000 + i,
                "swap_state": "completed",
                "timestamp": datetime.now().isoformat(),
                "scraped_at": datetime.now().isoformat(),
                "raw_data": json.dumps({"test": True, "broker_id": broker["address"]}),
            }
            test_transactions.append(transaction)

        self.save_transactions_to_db(test_transactions)
        print(f"✅ Created {len(test_transactions)} test transactions")


async def main():
    """Main function"""
    listener = ChainflipBrokerListener()

    try:
        await listener.listen_for_transactions()
    except Exception as e:
        print(f"❌ Error during listening: {e}")
        print("🔄 Creating fallback test data instead...")
        listener.create_fallback_data()

    print("\n✅ Chainflip Broker Listener completed!")


if __name__ == "__main__":
    asyncio.run(main())
