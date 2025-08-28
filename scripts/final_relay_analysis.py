#!/usr/bin/env python3
"""
Final Relay Trading Pair Analysis
Analyzes the relay_affiliate_fees table to extract trading pairs and calculate volume and fees.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from dotenv import load_dotenv
import subprocess
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    filename="relay_analysis.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables
load_dotenv()


class FinalRelayAnalyzer:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        alchemy_url = (
            f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        )
        self.w3 = Web3(Web3.HTTPProvider(alchemy_url))
        self.token_resolver = self._get_token_resolver()
        logging.info("FinalRelayAnalyzer initialized.")

    def _run_relay_listener(self, start_block: int, end_block: int):
        """Run the original relay listener to populate the database."""
        logging.info(
            f"Running the original relay listener from block {start_block} to {end_block}..."
        )
        try:
            subprocess.run(
                [
                    "python",
                    "listeners/relay_listener.py",
                    "--chain",
                    "base",
                    "--from",
                    str(start_block),
                    "--to",
                    str(end_block),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logging.info("Relay listener completed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Relay listener failed: {e.stderr}")
            raise

    def _get_token_resolver(self):
        """Initializes and returns a TokenNameResolver instance."""
        import sys

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from shared.token_name_resolver import TokenNameResolver

        return TokenNameResolver()

    def analyze_trading_pairs(self):
        """Analyzes the relay_affiliate_fees table to find top trading pairs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tx_hash, amount, token_address, affiliate_address FROM relay_affiliate_fees"
        )
        transactions = cursor.fetchall()
        conn.close()
        logging.info(f"Found {len(transactions)} affiliate fee events to analyze.")

        trade_pairs = defaultdict(lambda: {"volume": 0, "fees": 0, "count": 0})

        for tx_hash, fee_amount, fee_token, affiliate_address in transactions:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                sender = receipt["from"]
                transfers = self._extract_transfers(receipt)

                if len(transfers) >= 2:
                    from_token, to_token = self._find_swap_tokens(transfers, sender)
                    if from_token and to_token:
                        from_token_name = self.token_resolver.get_token_name(
                            from_token, "base"
                        )
                        to_token_name = self.token_resolver.get_token_name(
                            to_token, "base"
                        )
                        pair = f"{from_token_name}/{to_token_name}"

                        fee_usd = (int(fee_amount) / 1e18) * self._get_price(fee_token)
                        volume_usd = fee_usd * 100  # Estimate volume

                        trade_pairs[pair]["volume"] += volume_usd
                        trade_pairs[pair]["fees"] += fee_usd
                        trade_pairs[pair]["count"] += 1
                        logging.info(f"Processed trade pair {pair} for tx {tx_hash}")

            except Exception as e:
                logging.error(f"Error processing transaction {tx_hash}: {e}")

        self._print_report(trade_pairs)

    def _find_swap_tokens(
        self, transfers: List[Dict], sender: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Finds the from and to tokens in a swap by analyzing token flows."""
        balances = defaultdict(int)
        for t in transfers:
            if t["from"].lower() == sender.lower():
                balances[t["token"]] -= t["amount"]
            if t["to"].lower() == sender.lower():
                balances[t["token"]] += t["amount"]

        from_token, to_token = None, None
        for token, balance in balances.items():
            if balance < 0:
                from_token = token
            elif balance > 0:
                to_token = token

        return from_token, to_token

    def _extract_transfers(self, receipt: Dict) -> List[Dict]:
        """Extracts ERC20 transfers from a transaction receipt."""
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
                transfers.append(
                    {
                        "token": log["address"],
                        "from": "0x" + log["topics"][1].hex()[-40:],
                        "to": "0x" + log["topics"][2].hex()[-40:],
                        "amount": int.from_bytes(log["data"], "big"),
                    }
                )
        return transfers

    def _get_price(self, token_address: str) -> float:
        """A simple price fetcher."""
        return (
            3500.0
            if token_address.lower() == "0x0000000000000000000000000000000000000000"
            else 1.0
        )

    def _print_report(self, trade_pairs: Dict):
        """Prints a summary of the top trading pairs."""
        logging.info("--- Top Relay Trading Pairs ---")
        sorted_pairs = sorted(
            trade_pairs.items(), key=lambda item: item[1]["volume"], reverse=True
        )
        for pair, data in sorted_pairs[:10]:
            logging.info(
                f"{pair}: Volume: ${data['volume']:,.2f}, Fees: ${data['fees']:,.2f}, Trades: {data['count']}"
            )
        logging.info("--- End of Report ---")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Final Relay Trading Pair Analysis")
    parser.add_argument(
        "--from", dest="start_block", type=int, help="Start block number"
    )
    parser.add_argument("--to", dest="end_block", type=int, help="End block number")
    args = parser.parse_args()

    analyzer = FinalRelayAnalyzer()
    if args.start_block and args.end_block:
        analyzer._run_relay_listener(args.start_block, args.end_block)
    analyzer.analyze_trading_pairs()
    logging.info("Analysis complete.")
