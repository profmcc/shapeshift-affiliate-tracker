#!/usr/bin/env python3
"""
Detailed Relay Transaction Analyzer
Enriches existing Relay data with trading pair information by analyzing ERC20Transfer events.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()


class DetailedRelayAnalyzer:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        alchemy_url = (
            f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        )
        self.w3 = Web3(Web3.HTTPProvider(alchemy_url))
        self._init_database()

    def _run_relay_listener(self):
        """Run the original relay listener to populate the database."""
        print("Running the original relay listener to populate the database...")
        subprocess.run(
            [
                "python",
                "listeners/relay_listener.py",
                "--chain",
                "base",
                "--from",
                "32900000",
                "--to",
                "32900100",
            ],
            check=True,
        )

    def _connect_db(self):
        """Connect to the SQLite database with retry logic."""
        for i in range(5):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(1)
                else:
                    raise
        raise Exception("Could not connect to the database after several retries.")

    def _init_database(self):
        """Initialize the database and create a new table for detailed transactions."""
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relay_detailed_transactions (
                tx_hash TEXT PRIMARY KEY,
                chain TEXT,
                block_number INTEGER,
                timestamp INTEGER,
                from_token TEXT,
                to_token TEXT,
                from_amount TEXT,
                to_amount TEXT,
                affiliate_fee_amount TEXT,
                affiliate_fee_token TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def analyze_and_enrich_transactions(self):
        """Fetch transactions, analyze them for trading pairs, and store the enriched data."""
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT tx_hash, chain, block_number, timestamp, amount, token_address FROM relay_affiliate_fees"
        )
        transactions = cursor.fetchall()
        conn.close()

        enriched_data = []
        for (
            tx_hash,
            chain,
            block_number,
            timestamp,
            fee_amount,
            fee_token,
        ) in transactions:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                transfers = self._extract_transfers(receipt)
                if len(transfers) >= 2:
                    from_token = transfers[0]["token"]
                    to_token = transfers[-1]["token"]
                    from_amount = str(transfers[0]["amount"])
                    to_amount = str(transfers[-1]["amount"])

                    enriched_data.append(
                        (
                            tx_hash,
                            chain,
                            block_number,
                            timestamp,
                            from_token,
                            to_token,
                            from_amount,
                            to_amount,
                            fee_amount,
                            fee_token,
                        )
                    )
            except Exception as e:
                print(f"Error processing transaction {tx_hash}: {e}")

        self._save_enriched_data(enriched_data)

    def _extract_transfers(self, receipt: Dict) -> List[Dict]:
        """Extract all ERC20 transfers from a transaction receipt."""
        transfers = []
        transfer_topic = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )
        for log in receipt["logs"]:
            if (
                log["topics"]
                and log["topics"][0].hex() == transfer_topic
                and len(log["topics"]) == 3
            ):
                amount = int.from_bytes(log["data"], "big")
                if amount > 0:
                    transfers.append(
                        {
                            "token": log["address"],
                            "from": "0x" + log["topics"][1].hex()[-40:],
                            "to": "0x" + log["topics"][2].hex()[-40:],
                            "amount": amount,
                        }
                    )
        return transfers

    def _save_enriched_data(self, data: List[Tuple]):
        """Save the enriched transaction data to the new table."""
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO relay_detailed_transactions 
            (tx_hash, chain, block_number, timestamp, from_token, to_token, from_amount, to_amount, affiliate_fee_amount, affiliate_fee_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            data,
        )
        conn.commit()
        conn.close()
        print(f"Successfully enriched and saved {len(data)} Relay transactions.")


if __name__ == "__main__":
    analyzer = DetailedRelayAnalyzer()
    analyzer._run_relay_listener()
    analyzer.analyze_and_enrich_transactions()
