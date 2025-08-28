#!/usr/bin/env python3
"""
THORChain Data Consolidator
Consolidates CSV and JSON files of Thorchain transactions into a unified database.
Handles deduplication and incremental updates automatically.
"""

import os
import json
import csv
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class THORChainDataConsolidator:
    def __init__(self, downloads_dir: str, database_dir: str):
        """
        Initialize the consolidator.

        Args:
            downloads_dir: Path to Downloads directory containing viewblock data files
            database_dir: Path to databases directory where consolidated DB will be stored
        """
        self.downloads_dir = Path(downloads_dir)
        self.database_dir = Path(database_dir)

        # Ensure we use absolute paths
        if not self.database_dir.is_absolute():
            # If relative path, make it relative to the project root
            project_root = Path(__file__).parent.parent
            self.database_dir = project_root / database_dir

        self.database_path = self.database_dir / "thorchain_consolidated.db"

        # Ensure directories exist
        self.database_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.init_database()

    def init_database(self):
        """Initialize the consolidated THORChain database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Create main transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS thorchain_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT,
                block_height TEXT,
                timestamp TEXT,
                from_address TEXT,
                to_address TEXT,
                affiliate_address TEXT,
                from_asset TEXT,
                to_asset TEXT,
                from_amount REAL,
                to_amount REAL,
                status TEXT,
                type TEXT,
                raw_row_text TEXT,
                source_file TEXT,
                file_timestamp TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """
        )

        # Create indexes for performance and deduplication
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_hash ON thorchain_transactions(tx_hash)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_block_height ON thorchain_transactions(block_height)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON thorchain_transactions(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_source_file ON thorchain_transactions(source_file)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_timestamp ON thorchain_transactions(file_timestamp)"
        )

        # Note: We handle deduplication in application logic rather than database constraints
        # to avoid issues with null tx_hash values

        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized: {self.database_path}")

    def find_viewblock_files(self) -> List[Path]:
        """Find all viewblock THORChain data files in Downloads directory"""
        pattern = "viewblock_thorchain_data_*"
        files = list(self.downloads_dir.glob(pattern))

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        logger.info(f"📁 Found {len(files)} viewblock data files")
        return files

    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None

        # Handle various timestamp formats
        formats = [
            "%b %d %Y %I:%M:%S %p (GMT-7)",
            "%b %d %Y %I:%M:%S %p (GMT-8)",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]

        # Clean up timestamp string - remove "Time" prefix if present
        clean_timestamp = timestamp_str.replace("Time", "").strip()

        for fmt in formats:
            try:
                return datetime.strptime(clean_timestamp, fmt)
            except ValueError:
                continue

        logger.warning(f"⚠️ Could not parse timestamp: {timestamp_str}")
        return None

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """Normalize amount string to float, handling commas and formatting"""
        if not amount_str:
            return None

        try:
            # Remove commas and convert to float
            cleaned = str(amount_str).replace(",", "")
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Could not parse amount: {amount_str}")
            return None

    def parse_csv_file(self, file_path: Path) -> List[Dict]:
        """Parse CSV file and return list of transaction dictionaries"""
        transactions = []
        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)

        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row_num, row in enumerate(reader, 1):
                    try:
                        # Parse timestamp
                        parsed_timestamp = self.parse_timestamp(
                            row.get("timestamp", "")
                        )

                        # Normalize amounts
                        from_amount = self.normalize_amount(row.get("from_amount"))
                        to_amount = self.normalize_amount(row.get("to_amount"))

                        transaction = {
                            "tx_hash": row.get("tx_hash"),
                            "block_height": row.get("block_height"),
                            "timestamp": row.get("timestamp"),
                            "from_address": row.get("from_address"),
                            "to_address": row.get("to_address"),
                            "affiliate_address": row.get("affiliate_address"),
                            "from_asset": row.get("from_asset"),
                            "to_asset": row.get("to_asset"),
                            "from_amount": from_amount,
                            "to_amount": to_amount,
                            "status": row.get("status"),
                            "type": row.get("type"),
                            "raw_row_text": row.get("raw_row_text"),
                            "source_file": file_path.name,
                            "file_timestamp": file_timestamp.isoformat(),
                        }

                        transactions.append(transaction)

                    except Exception as e:
                        logger.error(
                            f"❌ Error parsing CSV row {row_num} in {file_path.name}: {e}"
                        )
                        continue

        except Exception as e:
            logger.error(f"❌ Error reading CSV file {file_path}: {e}")

        logger.info(
            f"📊 Parsed {len(transactions)} transactions from CSV: {file_path.name}"
        )
        return transactions

    def parse_json_file(self, file_path: Path) -> List[Dict]:
        """Parse JSON file and return list of transaction dictionaries"""
        transactions = []
        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)

        try:
            with open(file_path, "r", encoding="utf-8") as jsonfile:
                data = json.load(jsonfile)

                for row_num, row in enumerate(data, 1):
                    try:
                        # Parse timestamp
                        parsed_timestamp = self.parse_timestamp(
                            row.get("timestamp", "")
                        )

                        # Normalize amounts
                        from_amount = self.normalize_amount(row.get("from_amount"))
                        to_amount = self.normalize_amount(row.get("to_amount"))

                        transaction = {
                            "tx_hash": row.get("tx_hash"),
                            "block_height": row.get("block_height"),
                            "timestamp": row.get("timestamp"),
                            "from_address": row.get("from_address"),
                            "to_address": row.get("to_address"),
                            "affiliate_address": row.get("affiliate_address"),
                            "from_asset": row.get("from_asset"),
                            "to_asset": row.get("to_asset"),
                            "from_amount": from_amount,
                            "to_amount": to_amount,
                            "status": row.get("status"),
                            "type": row.get("type"),
                            "raw_row_text": row.get("raw_row_text"),
                            "source_file": file_path.name,
                            "file_timestamp": file_timestamp.isoformat(),
                        }

                        transactions.append(transaction)

                    except Exception as e:
                        logger.error(
                            f"❌ Error parsing JSON row {row_num} in {file_path.name}: {e}"
                        )
                        continue

        except Exception as e:
            logger.error(f"❌ Error reading JSON file {file_path}: {e}")

        logger.info(
            f"📊 Parsed {len(transactions)} transactions from JSON: {file_path.name}"
        )
        return transactions

    def get_existing_transactions(self) -> Set[Tuple[str, str, str]]:
        """Get set of existing transaction identifiers for deduplication"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT tx_hash, timestamp, block_height, from_address
            FROM thorchain_transactions
        """
        )

        existing = set()
        for row in cursor.fetchall():
            tx_hash, timestamp, block_height, from_address = row
            # Create unique identifier: (tx_hash, timestamp) or (block_height, timestamp, from_address)
            if tx_hash:
                existing.add((tx_hash, timestamp))
            else:
                existing.add((block_height, timestamp, from_address))

        conn.close()
        return existing

    def insert_transactions(self, transactions: List[Dict]) -> Tuple[int, int]:
        """Insert new transactions into database, skipping duplicates"""
        if not transactions:
            return 0, 0

        existing = self.get_existing_transactions()
        new_transactions = []
        skipped = 0

        for tx in transactions:
            # Create unique identifier for deduplication
            tx_hash = tx.get("tx_hash")
            timestamp = tx.get("timestamp")
            block_height = tx.get("block_height")
            from_address = tx.get("from_address")

            if tx_hash:
                tx_id = (tx_hash, timestamp)
            else:
                tx_id = (block_height, timestamp, from_address)

            if tx_id in existing:
                skipped += 1
                continue

            new_transactions.append(tx)
            existing.add(tx_id)

        if not new_transactions:
            logger.info(
                f"⏭️ All {len(transactions)} transactions already exist in database"
            )
            return 0, len(transactions)

        # Insert new transactions
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        try:
            cursor.executemany(
                """
                INSERT INTO thorchain_transactions (
                    tx_hash, block_height, timestamp, from_address, to_address,
                    affiliate_address, from_asset, to_asset, from_amount, to_amount,
                    status, type, raw_row_text, source_file, file_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        tx["tx_hash"],
                        tx["block_height"],
                        tx["timestamp"],
                        tx["from_address"],
                        tx["to_address"],
                        tx["affiliate_address"],
                        tx["from_asset"],
                        tx["to_asset"],
                        tx["from_amount"],
                        tx["to_amount"],
                        tx["status"],
                        tx["type"],
                        tx["raw_row_text"],
                        tx["source_file"],
                        tx["file_timestamp"],
                    )
                    for tx in new_transactions
                ],
            )

            conn.commit()
            logger.info(f"💾 Inserted {len(new_transactions)} new transactions")

        except Exception as e:
            logger.error(f"❌ Error inserting transactions: {e}")
            conn.rollback()
            return 0, 0
        finally:
            conn.close()

        return len(new_transactions), skipped

    def process_file(self, file_path: Path) -> Tuple[int, int]:
        """Process a single file and return (inserted, skipped) counts"""
        logger.info(f"🔄 Processing: {file_path.name}")

        if file_path.suffix.lower() == ".csv":
            transactions = self.parse_csv_file(file_path)
        elif file_path.suffix.lower() == ".json":
            transactions = self.parse_json_file(file_path)
        else:
            logger.warning(f"⚠️ Unsupported file type: {file_path.suffix}")
            return 0, 0

        if not transactions:
            return 0, 0

        inserted, skipped = self.insert_transactions(transactions)
        return inserted, skipped

    def consolidate_all_files(self, force_reprocess: bool = False) -> Dict[str, int]:
        """Consolidate all viewblock data files"""
        files = self.find_viewblock_files()

        if not files:
            logger.warning("⚠️ No viewblock data files found")
            return {}

        total_inserted = 0
        total_skipped = 0
        processed_files = 0

        for file_path in files:
            try:
                inserted, skipped = self.process_file(file_path)
                total_inserted += inserted
                total_skipped += skipped
                processed_files += 1

                logger.info(
                    f"📈 File {file_path.name}: {inserted} new, {skipped} skipped"
                )

            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
                continue

        logger.info(f"🎯 Consolidation complete: {processed_files} files processed")
        logger.info(
            f"📊 Total: {total_inserted} new transactions, {total_skipped} skipped"
        )

        return {
            "files_processed": processed_files,
            "transactions_inserted": total_inserted,
            "transactions_skipped": total_skipped,
        }

    def get_database_stats(self) -> Dict[str, any]:
        """Get statistics about the consolidated database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM thorchain_transactions")
        total_transactions = cursor.fetchone()[0]

        # Transactions by source file
        cursor.execute(
            """
            SELECT source_file, COUNT(*) as count, 
                   MIN(file_timestamp) as earliest, 
                   MAX(file_timestamp) as latest
            FROM thorchain_transactions 
            GROUP BY source_file 
            ORDER BY latest DESC
        """
        )
        file_stats = cursor.fetchall()

        # Date range
        cursor.execute(
            """
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
            FROM thorchain_transactions
        """
        )
        date_range = cursor.fetchone()

        # Asset distribution
        cursor.execute(
            """
            SELECT from_asset, COUNT(*) as count
            FROM thorchain_transactions 
            WHERE from_asset IS NOT NULL
            GROUP BY from_asset 
            ORDER BY count DESC 
            LIMIT 10
        """
        )
        top_assets = cursor.fetchall()

        conn.close()

        return {
            "total_transactions": total_transactions,
            "file_stats": file_stats,
            "date_range": date_range,
            "top_assets": top_assets,
        }

    def print_database_stats(self):
        """Print formatted database statistics"""
        stats = self.get_database_stats()

        print("\n" + "=" * 60)
        print("📊 THORCHAIN CONSOLIDATED DATABASE STATISTICS")
        print("=" * 60)

        print(f"Total Transactions: {stats['total_transactions']:,}")

        if stats["date_range"][0] and stats["date_range"][1]:
            print(f"Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")

        print(f"\n📁 Source Files ({len(stats['file_stats'])}):")
        for file_name, count, earliest, latest in stats["file_stats"]:
            print(f"  • {file_name}: {count:,} transactions ({earliest} to {latest})")

        print(f"\n🪙 Top Assets:")
        for asset, count in stats["top_assets"]:
            print(f"  • {asset}: {count:,} transactions")

        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate THORChain viewblock data files"
    )
    parser.add_argument(
        "--downloads",
        default="/Users/chrismccarthy/Downloads",
        help="Path to Downloads directory (default: /Users/chrismccarthy/Downloads)",
    )
    parser.add_argument(
        "--database",
        default="databases",
        help="Path to databases directory (default: databases)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show database statistics only"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force reprocessing of all files"
    )

    args = parser.parse_args()

    # Initialize consolidator
    consolidator = THORChainDataConsolidator(args.downloads, args.database)

    if args.stats:
        consolidator.print_database_stats()
    else:
        # Run consolidation
        logger.info("🚀 Starting THORChain data consolidation...")
        results = consolidator.consolidate_all_files(force_reprocess=args.force)

        # Show final statistics
        consolidator.print_database_stats()


if __name__ == "__main__":
    main()
