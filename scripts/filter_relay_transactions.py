#!/usr/bin/env python3
"""
Filter Relay Transactions by ShapeShift Treasury Address
Removes all transactions from the relay_affiliate_fees table that do not match the ShapeShift treasury address.
"""

import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RelayTransactionFilter:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        self.shapeshift_treasury_address = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"

    def filter_transactions(self):
        """Filter the relay_affiliate_fees table"""
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found: {self.db_path}")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get total count before filtering
            cursor.execute("SELECT COUNT(*) FROM relay_affiliate_fees")
            initial_count = cursor.fetchone()[0]
            logger.info(f"Initial transaction count: {initial_count}")

            # Delete transactions that do not match the ShapeShift treasury address
            cursor.execute(
                """
                DELETE FROM relay_affiliate_fees 
                WHERE affiliate_address != ?
            """,
                (self.shapeshift_treasury_address,),
            )

            # Get count of deleted rows
            deleted_count = conn.total_changes
            logger.info(f"Deleted {deleted_count} transactions")

            # Get final count
            cursor.execute("SELECT COUNT(*) FROM relay_affiliate_fees")
            final_count = cursor.fetchone()[0]
            logger.info(f"Final transaction count: {final_count}")

            conn.commit()

        except Exception as e:
            logger.error(f"Error filtering transactions: {e}")
            conn.rollback()
        finally:
            conn.close()


def main():
    tx_filter = RelayTransactionFilter()
    tx_filter.filter_transactions()


if __name__ == "__main__":
    main()
