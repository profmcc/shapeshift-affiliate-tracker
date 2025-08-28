#!/usr/bin/env python3
"""
Block Tracker
Persistently stores and retrieves the last block number scanned for each protocol/chain combination.
"""

import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BlockTracker:
    def __init__(self, db_path: str = "databases/block_tracker.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the block tracker database and table."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS block_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_name TEXT NOT NULL,
                chain_name TEXT NOT NULL,
                last_scanned_block INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(protocol_name, chain_name)
            )
        """
        )

        conn.commit()
        conn.close()

    def get_last_scanned_block(
        self, protocol_name: str, chain_name: str, default_start_block: int
    ) -> int:
        """
        Get the last scanned block for a given protocol and chain.
        If no record is found, it returns the default_start_block.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT last_scanned_block FROM block_tracker WHERE protocol_name = ? AND chain_name = ?",
            (protocol_name, chain_name),
        )
        result = cursor.fetchone()

        conn.close()

        if result:
            logger.info(
                f"Resuming scan for {protocol_name} on {chain_name} from block {result[0] + 1}"
            )
            return result[0] + 1
        else:
            logger.info(
                f"No previous scan found for {protocol_name} on {chain_name}. Starting from block {default_start_block}."
            )
            return default_start_block

    def update_last_scanned_block(
        self, protocol_name: str, chain_name: str, block_number: int
    ):
        """
        Update the last scanned block for a given protocol and chain.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO block_tracker (protocol_name, chain_name, last_scanned_block, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (protocol_name, chain_name, block_number),
        )

        conn.commit()
        conn.close()
        logger.info(
            f"Updated last scanned block for {protocol_name} on {chain_name} to {block_number}"
        )


def main():
    """Example usage and testing"""
    tracker = BlockTracker()

    # Example: Relay on Base
    protocol = "relay"
    chain = "base"
    default_start = 33000000

    # Get last block (will be default first time)
    start_block = tracker.get_last_scanned_block(protocol, chain, default_start)
    print(f"Starting scan at block: {start_block}")

    # Simulate a scan
    end_block = start_block + 1000
    print(f"Simulating scan up to block: {end_block}")

    # Update the tracker
    tracker.update_last_scanned_block(protocol, chain, end_block)

    # Get the last block again
    next_start_block = tracker.get_last_scanned_block(protocol, chain, default_start)
    print(f"Next scan should start at block: {next_start_block}")
    assert next_start_block == end_block + 1


if __name__ == "__main__":
    main()
