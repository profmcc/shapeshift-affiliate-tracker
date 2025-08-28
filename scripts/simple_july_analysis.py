#!/usr/bin/env python3
"""
Simple July 2025 Analysis
Fast, focused analysis with consistent formatting and shared utilities.
"""

import sqlite3
import pandas as pd
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import requests


class SimpleJulyAnalyzer:
    def __init__(self):
        self.july_start = datetime(2025, 7, 1)
        self.july_end = datetime(2025, 7, 31)
        self.price_cache = {}

    def get_token_price(self, token_symbol: str) -> float:
        """Get token price with caching"""
        if token_symbol in self.price_cache:
            return self.price_cache[token_symbol]

        # Fallback prices for common tokens
        fallback_prices = {
            "ETH": 3500,
            "WETH": 3500,
            "USDC": 1.0,
            "USDT": 1.0,
            "FOX": 0.15,
            "BTC": 65000,
            "DOGE": 0.08,
            "ATOM": 8.0,
            "ARB": 1.2,
            "1INCH": 0.4,
            "MATIC": 0.8,
            "TCY": 1.0,
        }

        price = fallback_prices.get(token_symbol.upper(), 1.0)
        self.price_cache[token_symbol] = price
        return price

    def analyze_thorchain_july(self):
        """Analyze THORChain July 2025 data"""
        print("🔍 Analyzing THORChain July 2025 data...")

        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Convert timestamps
            df["timestamp"] = pd.to_datetime(
                df["timestamp"], format="%b %d %Y %I:%M:%S %p (GMT-7)", errors="coerce"
            )

            # Filter for July 2025
            july_mask = (df["timestamp"] >= self.july_start) & (
                df["timestamp"] <= self.july_end
            )
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 THORChain transactions")

            # Analyze trade pairs
            trade_pairs = defaultdict(float)
            total_volume = 0

            for _, row in july_df.iterrows():
                from_asset = str(row["from_asset"]).strip()
                to_asset = str(row["to_asset"]).strip()

                if from_asset and to_asset and from_asset != to_asset:
                    pair = f"{from_asset}/{to_asset}"

                    # Get amounts
                    from_amount = (
                        float(row["from_amount"]) if pd.notna(row["from_amount"]) else 0
                    )
                    to_amount = (
                        float(row["to_amount"]) if pd.notna(row["to_amount"]) else 0
                    )

                    # Calculate USD volume
                    from_price = self.get_token_price(from_asset)
                    to_price = self.get_token_price(to_asset)
                    volume_usd = max(from_amount * from_price, to_amount * to_price)

                    trade_pairs[pair] += volume_usd
                    total_volume += volume_usd

            return {
                "protocol": "THORChain",
                "transactions": len(july_df),
                "total_volume": total_volume,
                "trade_pairs": dict(trade_pairs),
            }

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain: {e}")
            return {
                "protocol": "THORChain",
                "transactions": 0,
                "total_volume": 0,
                "trade_pairs": {},
            }

    def analyze_cowswap_july(self):
        """Analyze CowSwap July 2025 data"""
        print("🔍 Analyzing CowSwap July 2025 data...")

        try:
            df = pd.read_excel("webscrape/CoW Swap Partner Dashboard Table.xlsx")

            # Convert date column
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # Filter for July 2025
            july_mask = (df["Date"] >= self.july_start) & (df["Date"] <= self.july_end)
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 CowSwap transactions")

            # Analyze trade pairs
            trade_pairs = defaultdict(float)
            total_volume = 0
            total_fees = 0

            for _, row in july_df.iterrows():
                trade_pair = str(row.get("Trade Pair", ""))
                if "/" in trade_pair:
                    from_token, to_token = trade_pair.split("/", 1)
                    pair = f"{from_token}/{to_token}"
                else:
                    continue

                volume = float(row.get("Volume", 0))
                affiliate_fee = float(row.get("Affiliate Fee", 0))

                trade_pairs[pair] += volume
                total_volume += volume
                total_fees += affiliate_fee

            return {
                "protocol": "CowSwap",
                "transactions": len(july_df),
                "total_volume": total_volume,
                "total_fees": total_fees,
                "trade_pairs": dict(trade_pairs),
            }

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap: {e}")
            return {
                "protocol": "CowSwap",
                "transactions": 0,
                "total_volume": 0,
                "total_fees": 0,
                "trade_pairs": {},
            }

    def analyze_relay_july(self):
        """Analyze Relay July 2025 data"""
        print("🔍 Analyzing Relay July 2025 data...")

        try:
            # Check if Relay database exists
            relay_db_path = "databases/affiliate.db"
            if not os.path.exists(relay_db_path):
                print(f"   ⚠️ Relay database not found: {relay_db_path}")
                return {
                    "protocol": "Relay",
                    "transactions": 0,
                    "total_volume": 0,
                    "total_fees": 0,
                    "trade_pairs": {},
                }

            conn = sqlite3.connect(relay_db_path)
            cursor = conn.cursor()

            # Get July 2025 transactions
            cursor.execute(
                """
                SELECT * FROM relay_affiliate_fees 
                WHERE timestamp >= ? AND timestamp <= ?
            """,
                (int(self.july_start.timestamp()), int(self.july_end.timestamp())),
            )

            relay_transactions = cursor.fetchall()
            conn.close()

            print(f"   📊 Found {len(relay_transactions)} July 2025 Relay transactions")

            # Analyze data
            total_fees = 0
            fee_by_token = defaultdict(float)

            for row in relay_transactions:
                # Assuming standard column order - adjust if needed
                if len(row) >= 4:
                    fee_amount = float(row[3]) if row[3] else 0  # fee_amount column
                    token_address = (
                        row[2] if len(row) > 2 else ""
                    )  # token_address column

                    # Simple token mapping
                    token_symbol = (
                        "ETH"
                        if token_address == "0x0000000000000000000000000000000000000000"
                        else "UNKNOWN"
                    )

                    total_fees += fee_amount * self.get_token_price(token_symbol)
                    fee_by_token[token_symbol] += fee_amount * self.get_token_price(
                        token_symbol
                    )

            return {
                "protocol": "Relay",
                "transactions": len(relay_transactions),
                "total_volume": 0,  # Relay doesn't track volume directly
                "total_fees": total_fees,
                "fee_by_token": dict(fee_by_token),
            }

        except Exception as e:
            print(f"   ❌ Error analyzing Relay: {e}")
            return {
                "protocol": "Relay",
                "transactions": 0,
                "total_volume": 0,
                "total_fees": 0,
                "fee_by_token": {},
            }

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n📊 Generating July 2025 report...")

        # Analyze all protocols
        thorchain_data = self.analyze_thorchain_july()
        cowswap_data = self.analyze_cowswap_july()
        relay_data = self.analyze_relay_july()

        # Combine all trade pairs
        all_trade_pairs = defaultdict(float)
        all_trade_pairs.update(thorchain_data["trade_pairs"])
        all_trade_pairs.update(cowswap_data["trade_pairs"])

        # Sort by volume
        sorted_pairs = sorted(all_trade_pairs.items(), key=lambda x: x[1], reverse=True)

        # Calculate totals
        total_transactions = (
            thorchain_data["transactions"]
            + cowswap_data["transactions"]
            + relay_data["transactions"]
        )
        total_volume = thorchain_data["total_volume"] + cowswap_data["total_volume"]
        total_fees = cowswap_data["total_fees"] + relay_data["total_fees"]

        # Create report
        report = {
            "summary": {
                "total_transactions": total_transactions,
                "total_volume_usd": total_volume,
                "total_affiliate_fees_usd": total_fees,
            },
            "protocol_breakdown": [
                {
                    "protocol": thorchain_data["protocol"],
                    "transactions": thorchain_data["transactions"],
                    "volume_usd": thorchain_data["total_volume"],
                    "fees_usd": 0,
                },
                {
                    "protocol": cowswap_data["protocol"],
                    "transactions": cowswap_data["transactions"],
                    "volume_usd": cowswap_data["total_volume"],
                    "fees_usd": cowswap_data["total_fees"],
                },
                {
                    "protocol": relay_data["protocol"],
                    "transactions": relay_data["transactions"],
                    "volume_usd": relay_data["total_volume"],
                    "fees_usd": relay_data["total_fees"],
                },
            ],
            "top_trade_pairs": [
                {"pair": pair, "volume_usd": volume}
                for pair, volume in sorted_pairs[:10]
            ],
        }

        # Save report
        with open("simple_july_2025_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print(f"\n📊 JULY 2025 ANALYSIS SUMMARY")
        print(f"=" * 60)
        print(f"Total Transactions: {total_transactions:,}")
        print(f"Total Volume: ${total_volume:,.2f}")
        print(f"Total Affiliate Fees: ${total_fees:,.2f}")

        print(f"\n🏆 TOP 5 TRADE PAIRS:")
        for i, pair_data in enumerate(report["top_trade_pairs"][:5], 1):
            print(f"{i}. {pair_data['pair']}: ${pair_data['volume_usd']:,.2f}")

        print(f"\n📊 PROTOCOL BREAKDOWN:")
        for protocol_data in report["protocol_breakdown"]:
            print(
                f"   {protocol_data['protocol']}: {protocol_data['transactions']} transactions, ${protocol_data['volume_usd']:,.2f} volume, ${protocol_data['fees_usd']:,.2f} fees"
            )

        print(f"\n✅ Report saved to: simple_july_2025_report.json")
        return report


def main():
    analyzer = SimpleJulyAnalyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
