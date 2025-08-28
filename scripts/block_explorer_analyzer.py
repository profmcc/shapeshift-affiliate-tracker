#!/usr/bin/env python3
"""
Final Relay Trading Pair Analysis with Block Explorer
Analyzes the relay_affiliate_fees table to extract trading pairs and calculate volume and fees using a block explorer.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()


class BlockExplorerAnalyzer:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        self.base_scan_api_key = os.getenv("BASESCAN_API_KEY")
        self.token_resolver = self._get_token_resolver()

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
            "SELECT tx_hash, amount, token_address FROM relay_affiliate_fees"
        )
        transactions = cursor.fetchall()
        conn.close()

        trade_pairs = defaultdict(lambda: {"volume": 0, "fees": 0, "count": 0})

        for tx_hash, fee_amount, fee_token in transactions:
            try:
                transfers = self._get_transfers_from_block_explorer(tx_hash)

                if len(transfers) >= 2:
                    from_token, to_token = self._find_swap_tokens(transfers)
                    if from_token and to_token:
                        pair = f"{from_token}/{to_token}"
                        fee_usd = (int(fee_amount) / 1e18) * self._get_price(fee_token)
                        volume_usd = fee_usd * 100  # Estimate volume

                        trade_pairs[pair]["volume"] += volume_usd
                        trade_pairs[pair]["fees"] += fee_usd
                        trade_pairs[pair]["count"] += 1
            except Exception as e:
                print(f"Error processing {tx_hash}: {e}")

        self._print_report(trade_pairs)

    def _get_transfers_from_block_explorer(self, tx_hash: str) -> List[Dict]:
        """Gets ERC20 transfers for a transaction from the BaseScan API."""
        url = f"https://api.basescan.org/api?module=account&action=tokentx&txhash={tx_hash}&apikey={self.base_scan_api_key}"
        response = requests.get(url)
        data = response.json()
        if isinstance(data.get("result"), list):
            return data.get("result", [])
        else:
            print(f"Error from BaseScan API for {tx_hash}: {data.get('result')}")
            return []

    def _find_swap_tokens(
        self, transfers: List[Dict]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Finds the from and to tokens in a swap by analyzing token flows."""
        if not transfers:
            return None, None

        # Simple assumption: first token is 'from', last is 'to'
        from_token = transfers[0].get("tokenSymbol")
        to_token = transfers[-1].get("tokenSymbol")

        return from_token, to_token

    def _get_price(self, token_address: str) -> float:
        """A simple price fetcher."""
        return (
            3500.0
            if token_address.lower() == "0x0000000000000000000000000000000000000000"
            else 1.0
        )

    def _print_report(self, trade_pairs: Dict):
        """Prints a summary of the top trading pairs."""
        print("\n--- Top Relay Trading Pairs (from Block Explorer) ---")
        sorted_pairs = sorted(
            trade_pairs.items(), key=lambda item: item[1]["volume"], reverse=True
        )
        for pair, data in sorted_pairs[:10]:
            print(
                f"{pair}: Volume: ${data['volume']:,.2f}, Fees: ${data['fees']:,.2f}, Trades: {data['count']}"
            )


if __name__ == "__main__":
    analyzer = BlockExplorerAnalyzer()
    analyzer.analyze_trading_pairs()
