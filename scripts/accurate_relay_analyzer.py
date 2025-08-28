#!/usr/bin/env python3
"""
Accurate Relay Global Solver Amount Analyzer
Calculates the total global solver amounts for transactions associated with ShapeShift treasury addresses.
"""

import os
import sqlite3
import json
from datetime import datetime
import logging
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AccurateRelayAnalyzer:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        self.addresses_path = "shared/shapeshift_addresses.json"
        self.shapeshift_addresses = self._load_shapeshift_addresses()

    def _load_shapeshift_addresses(self) -> Dict:
        """Load ShapeShift treasury addresses from JSON file"""
        if not os.path.exists(self.addresses_path):
            logger.error(f"ShapeShift addresses file not found: {self.addresses_path}")
            return {}

        with open(self.addresses_path, "r") as f:
            return json.load(f)

    def analyze_global_solver_amounts(self):
        """Analyze the actual global solver amounts for ShapeShift transactions"""
        if not self.shapeshift_addresses:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all relevant transactions
        cursor.execute(
            "SELECT tx_hash, chain, timestamp, affiliate_address, amount FROM relay_affiliate_fees_conservative"
        )
        transactions = cursor.fetchall()

        # Filter transactions by ShapeShift addresses and date range
        start_ts = int(datetime(2025, 7, 1).timestamp())
        end_ts = int(datetime(2025, 7, 30).timestamp())

        filtered_transactions = []
        for tx in transactions:
            tx_hash, chain, timestamp, affiliate_address, amount = tx

            if start_ts <= timestamp <= end_ts:
                chain_addresses = self.shapeshift_addresses.get(chain, [])
                if any(
                    addr.lower() == affiliate_address.lower()
                    for addr in chain_addresses
                ):
                    filtered_transactions.append(float(amount))

        # Calculate total amount
        total_wei = sum(filtered_transactions)
        total_eth = total_wei / 1e18
        total_usd = total_eth * 3500  # ETH price ~$3500

        logger.info(f"Total Global Solver Amount (ETH): {total_eth:.6f} ETH")
        logger.info(f"Total Global Solver Amount (USD): ${total_usd:,.2f}")

        conn.close()

        return total_eth


def main():
    analyzer = AccurateRelayAnalyzer()
    analyzer.analyze_global_solver_amounts()


if __name__ == "__main__":
    main()
