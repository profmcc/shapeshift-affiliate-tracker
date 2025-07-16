#!/usr/bin/env python3
"""
Chainflip Database System

Comprehensive database for tracking Chainflip broker transactions with:
- SQLite database for persistent storage
- Incremental updates without duplicates
- Full transaction history from the beginning
- Automatic deduplication and data validation
- Correct affiliate fee calculation based on swap date
"""

import sqlite3
import json
import csv
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass
class ChainflipTransaction:
    """Data class for Chainflip transaction records."""
    transaction_id: str
    from_address: str
    to_address: str
    from_currency: str
    to_currency: str
    from_amount: float
    to_amount: float
    from_amount_usd: float
    to_amount_usd: float
    status: str
    commission_usd: float
    affiliate_fee_usd: float  # New field for correct ShapeShift affiliate fee
    timestamp: datetime
    duration_minutes: Optional[int]
    broker_address: str
    hash_id: str  # For deduplication


class ChainflipDatabase:
    def __init__(self, db_path: str = "chainflip_transactions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with proper schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create transactions table with new affiliate_fee_usd field
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    from_currency TEXT NOT NULL,
                    to_currency TEXT NOT NULL,
                    from_amount REAL NOT NULL,
                    to_amount REAL NOT NULL,
                    from_amount_usd REAL NOT NULL,
                    to_amount_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    commission_usd REAL NOT NULL,
                    affiliate_fee_usd REAL NOT NULL DEFAULT 0.0,
                    timestamp DATETIME NOT NULL,
                    duration_minutes INTEGER,
                    broker_address TEXT NOT NULL,
                    hash_id TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add affiliate_fee_usd column if it doesn't exist (for existing databases)
            try:
                cursor.execute("ALTER TABLE transactions ADD COLUMN affiliate_fee_usd REAL NOT NULL DEFAULT 0.0")
                print("✅ Added affiliate_fee_usd column to existing database")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_id ON transactions(transaction_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash_id ON transactions(hash_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_from_address ON transactions(from_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_to_address ON transactions(to_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_broker_address ON transactions(broker_address)")
            
            # Create metadata table for tracking updates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize metadata
            cursor.execute("""
                INSERT OR IGNORE INTO metadata (key, value) VALUES 
                ('last_update', '1970-01-01 00:00:00'),
                ('total_transactions', '0'),
                ('last_transaction_id', ''),
                ('database_version', '1.1'),
                ('affiliate_fee_cutoff_date', '2024-05-31 00:00:00')
            """)
            
            conn.commit()
    
    def calculate_affiliate_fee(self, from_amount_usd: float, timestamp: datetime) -> float:
        """
        Calculate the correct ShapeShift affiliate fee based on swap date.
        
        Args:
            from_amount_usd: The USD amount of the swap
            timestamp: The timestamp of the swap
            
        Returns:
            The calculated affiliate fee in USD
        """
        # Cutoff date for affiliate fee change (May 31, 2024)
        cutoff_date = datetime(2024, 5, 31, 0, 0, 0)
        
        if timestamp < cutoff_date:
            # Before May 31, 2024: 0.5% (50 bps)
            return from_amount_usd * 0.005
        else:
            # On/after May 31, 2024: 0.55% (55 bps)
            return from_amount_usd * 0.0055
    
    def parse_transaction_data(self, row_data: Dict[str, Any], full_addresses: List[str]) -> Optional[ChainflipTransaction]:
        """Parse raw table data into structured transaction object."""
        try:
            # Extract transaction ID from cell_0
            cell_0 = row_data.get('cell_0', '')
            transaction_id_match = re.search(r'#(\d+)', cell_0)
            if not transaction_id_match:
                return None
            
            transaction_id = transaction_id_match.group(1)
            
            # Parse amounts and currencies from cell_0
            lines = cell_0.split('\n')
            if len(lines) < 4:
                return None
            
            # Extract from currency and amount
            from_line = lines[1]  # e.g., "0.01 BTC"
            from_match = re.search(r'([\d.]+)\s+(\w+)', from_line)
            if not from_match:
                return None
            
            from_amount = float(from_match.group(1))
            from_currency = from_match.group(2)
            
            # Extract from USD amount
            from_usd_line = lines[2]  # e.g., "$1,098.46"
            from_usd_match = re.search(r'\$([\d,]+\.?\d*)', from_usd_line)
            from_amount_usd = float(from_usd_match.group(1).replace(',', '')) if from_usd_match else 0.0
            
            # Extract to currency and amount
            to_line = lines[3]  # e.g., "1,089.88 USDC"
            to_match = re.search(r'([\d,]+\.?\d*)\s+(\w+)', to_line)
            if not to_match:
                return None
            
            to_amount = float(to_match.group(1).replace(',', ''))
            to_currency = to_match.group(2)
            
            # Extract to USD amount
            to_usd_line = lines[4] if len(lines) > 4 else lines[2]  # e.g., "$1,089.71"
            to_usd_match = re.search(r'\$([\d,]+\.?\d*)', to_usd_line)
            to_amount_usd = float(to_usd_match.group(1).replace(',', '')) if to_usd_match else 0.0
            
            # Extract status
            status = row_data.get('cell_2', 'Unknown')
            
            # Extract commission (this is the "Broker as a Service" fee, not the affiliate fee)
            commission_text = row_data.get('cell_3', '$0.00')
            commission_match = re.search(r'\$([\d.]+)', commission_text)
            commission_usd = float(commission_match.group(1)) if commission_match else 0.0
            
            # Parse timestamp and duration
            time_text = row_data.get('cell_4', '')
            timestamp, duration_minutes = self.parse_time_info(time_text)
            
            # Calculate the correct affiliate fee based on swap date
            affiliate_fee_usd = self.calculate_affiliate_fee(from_amount_usd, timestamp)
            
            # Get addresses
            if len(full_addresses) >= 2:
                from_address = full_addresses[0]
                to_address = full_addresses[1]
            else:
                # Fallback to abbreviated addresses
                address_cell = row_data.get('cell_1', '')
                addresses = re.findall(r'0x[a-fA-F0-9]{4,}', address_cell)
                from_address = addresses[0] if len(addresses) > 0 else 'unknown'
                to_address = addresses[1] if len(addresses) > 1 else 'unknown'
            
            # Create hash for deduplication
            hash_data = f"{transaction_id}_{from_address}_{to_address}_{from_amount}_{to_amount}_{timestamp}"
            hash_id = hashlib.sha256(hash_data.encode()).hexdigest()
            
            return ChainflipTransaction(
                transaction_id=transaction_id,
                from_address=from_address,
                to_address=to_address,
                from_currency=from_currency,
                to_currency=to_currency,
                from_amount=from_amount,
                to_amount=to_amount,
                from_amount_usd=from_amount_usd,
                to_amount_usd=to_amount_usd,
                status=status,
                commission_usd=commission_usd,
                affiliate_fee_usd=affiliate_fee_usd,
                timestamp=timestamp,
                duration_minutes=duration_minutes,
                broker_address="cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
                hash_id=hash_id
            )
            
        except Exception as e:
            print(f"Error parsing transaction data: {e}")
            return None
    
    def parse_time_info(self, time_text: str) -> Tuple[datetime, Optional[int]]:
        """Parse time information from text."""
        try:
            # Extract age information
            age_match = re.search(r'(\d+)\s+(hour|day|minute)s?\s+ago', time_text)
            if age_match:
                amount = int(age_match.group(1))
                unit = age_match.group(2)
                
                if unit == 'hour':
                    timestamp = datetime.now() - timedelta(hours=amount)
                elif unit == 'day':
                    timestamp = datetime.now() - timedelta(days=amount)
                elif unit == 'minute':
                    timestamp = datetime.now() - timedelta(minutes=amount)
                else:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Extract duration
            duration_match = re.search(r'Took\s+(\d+)m', time_text)
            duration_minutes = int(duration_match.group(1)) if duration_match else None
            
            return timestamp, duration_minutes
            
        except Exception as e:
            print(f"Error parsing time info: {e}")
            return datetime.now(), None
    
    def insert_transaction(self, transaction: ChainflipTransaction) -> bool:
        """Insert a transaction into the database, avoiding duplicates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if transaction already exists
                cursor.execute("SELECT id FROM transactions WHERE hash_id = ?", (transaction.hash_id,))
                if cursor.fetchone():
                    return False  # Already exists
                
                # Insert new transaction
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, from_address, to_address, from_currency, to_currency,
                        from_amount, to_amount, from_amount_usd, to_amount_usd, status,
                        commission_usd, affiliate_fee_usd, timestamp, duration_minutes, broker_address, hash_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.transaction_id, transaction.from_address, transaction.to_address,
                    transaction.from_currency, transaction.to_currency, transaction.from_amount,
                    transaction.to_amount, transaction.from_amount_usd, transaction.to_amount_usd,
                    transaction.status, transaction.commission_usd, transaction.affiliate_fee_usd,
                    transaction.timestamp, transaction.duration_minutes, transaction.broker_address,
                    transaction.hash_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            return False
    
    def update_metadata(self, last_transaction_id: str, total_count: int):
        """Update metadata with latest information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE metadata SET 
                        value = ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE key = 'last_update'
                """, (datetime.now().isoformat(),))
                
                cursor.execute("""
                    UPDATE metadata SET 
                        value = ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE key = 'total_transactions'
                """, (str(total_count),))
                
                cursor.execute("""
                    UPDATE metadata SET 
                        value = ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE key = 'last_transaction_id'
                """, (last_transaction_id,))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error updating metadata: {e}")
    
    def get_latest_transaction_id(self) -> str:
        """Get the latest transaction ID from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT transaction_id FROM transactions 
                    ORDER BY CAST(transaction_id AS INTEGER) DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                return result[0] if result else "0"
        except Exception as e:
            print(f"Error getting latest transaction ID: {e}")
            return "0"
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total transactions
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("""
                    SELECT MIN(timestamp), MAX(timestamp) FROM transactions
                """)
                date_range = cursor.fetchone()
                
                # Get total volume
                cursor.execute("""
                    SELECT SUM(from_amount_usd) FROM transactions WHERE status = 'Success'
                """)
                total_volume = cursor.fetchone()[0] or 0.0
                
                # Get total commissions (Broker as a Service fees)
                cursor.execute("""
                    SELECT SUM(commission_usd) FROM transactions WHERE status = 'Success'
                """)
                total_commissions = cursor.fetchone()[0] or 0.0
                
                # Get total affiliate fees (ShapeShift affiliate fees)
                cursor.execute("""
                    SELECT SUM(affiliate_fee_usd) FROM transactions WHERE status = 'Success'
                """)
                total_affiliate_fees = cursor.fetchone()[0] or 0.0
                
                # Get unique addresses
                cursor.execute("""
                    SELECT COUNT(DISTINCT from_address) + COUNT(DISTINCT to_address) 
                    FROM transactions
                """)
                unique_addresses = cursor.fetchone()[0] or 0
                
                return {
                    'total_transactions': total_transactions,
                    'date_range': date_range,
                    'total_volume_usd': total_volume,
                    'total_commissions_usd': total_commissions,
                    'total_affiliate_fees_usd': total_affiliate_fees,
                    'unique_addresses': unique_addresses
                }
                
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def print_stats(self):
        """Print database statistics."""
        stats = self.get_database_stats()
        
        print("\n=== CHAINFLIP DATABASE STATISTICS ===")
        print(f"Total Transactions: {stats.get('total_transactions', 0):,}")
        print(f"Total Volume: ${stats.get('total_volume_usd', 0):,.2f}")
        print(f"Broker Fees (0.05%): ${stats.get('total_commissions_usd', 0):,.2f}")
        print(f"ShapeShift Affiliate Fees: ${stats.get('total_affiliate_fees_usd', 0):,.2f}")
        print(f"Unique Addresses: {stats.get('unique_addresses', 0):,}")
        
        date_range = stats.get('date_range')
        if date_range and date_range[0] and date_range[1]:
            print(f"Date Range: {date_range[0]} to {date_range[1]}")
        
        print("=" * 40)


# Import the scraper functionality
from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper


class ChainflipDatabaseUpdater:
    """Main class for updating the Chainflip database."""
    
    def __init__(self, db_path: str = "chainflip_transactions.db"):
        self.database = ChainflipDatabase(db_path)
        self.scraper = ChainflipComprehensiveScraper(
            "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
        )
    
    async def update_database(self):
        """Update the database with new transactions."""
        print("Starting database update...")
        
        # Get current database stats
        self.database.print_stats()
        
        # Scrape new data
        print("\nScraping new transaction data...")
        scraped_data = await self.scraper.scrape_with_full_addresses()
        
        if not scraped_data:
            print("No data scraped. Exiting.")
            return
        
        # Process and insert new transactions
        new_transactions = 0
        skipped_transactions = 0
        
        for row in scraped_data:
            # Check if this is a table row (has cell_0, cell_1, etc.)
            if 'cell_0' in row and 'cell_1' in row:
                # Extract full addresses if available
                full_addresses = row.get('full_addresses', [])
                
                # Parse transaction data
                transaction = self.database.parse_transaction_data(row, full_addresses)
                
                if transaction:
                    # Try to insert transaction
                    if self.database.insert_transaction(transaction):
                        new_transactions += 1
                        print(f"✅ Added transaction #{transaction.transaction_id}")
                    else:
                        skipped_transactions += 1
                        print(f"⏭️ Skipped duplicate transaction #{transaction.transaction_id}")
        
        # Update metadata
        latest_id = self.database.get_latest_transaction_id()
        stats = self.database.get_database_stats()
        self.database.update_metadata(latest_id, stats['total_transactions'])
        
        # Print results
        print(f"\n=== UPDATE COMPLETE ===")
        print(f"New transactions added: {new_transactions}")
        print(f"Duplicate transactions skipped: {skipped_transactions}")
        print(f"Total transactions in database: {stats['total_transactions']:,}")
        
        # Show updated stats
        self.database.print_stats()


async def main():
    """Main function for running the database updater."""
    updater = ChainflipDatabaseUpdater()
    await updater.update_database()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
