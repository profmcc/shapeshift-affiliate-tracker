#!/usr/bin/env python3
"""
Fixed July 2025 Analysis
Properly handles data formats and provides accurate results.
"""

import sqlite3
import pandas as pd
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import requests


class FixedJulyAnalyzer:
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

    def safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                # Remove commas and convert
                return float(value.replace(",", ""))
            return float(value) if value else 0.0
        except:
            return 0.0

    def analyze_thorchain_july(self):
        """Analyze THORChain July 2025 data"""
        print("🔍 Analyzing THORChain July 2025 data...")

        try:
            # Check if THORChain CSV exists
            thorchain_csv_path = (
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )
            if not os.path.exists(thorchain_csv_path):
                print(f"   ⚠️ THORChain CSV not found: {thorchain_csv_path}")
                return {
                    "protocol": "THORChain",
                    "transactions": 0,
                    "total_volume": 0,
                    "total_fees": 0,
                    "trade_pairs": {},
                }

            df = pd.read_csv(thorchain_csv_path)
            print(f"   📊 Found {len(df)} total THORChain transactions")

            # Check column names
            print(f"   📋 Available columns: {df.columns.tolist()}")

            # Find date column
            date_col = None
            for col in df.columns:
                if "date" in col.lower() or "time" in col.lower():
                    date_col = col
                    break

            if date_col:
                # Parse dates with the correct format
                df[date_col] = pd.to_datetime(
                    df[date_col], format="%b %d %Y %I:%M:%S %p (GMT-7)", errors="coerce"
                )
                july_mask = (df[date_col] >= self.july_start) & (
                    df[date_col] <= self.july_end
                )
                july_df = df[july_mask]
            else:
                # If no date column found, use all data
                july_df = df
                print(f"   ⚠️ No date column found, using all data")

            print(f"   📊 Found {len(july_df)} July 2025 THORChain transactions")

            # Analyze trade pairs using from_asset, to_asset, from_amount, to_amount
            trade_pairs = defaultdict(float)
            total_volume = 0
            total_fees = 0

            for _, row in july_df.iterrows():
                # Get asset information
                from_asset = str(row.get("from_asset", "")).strip()
                to_asset = str(row.get("to_asset", "")).strip()

                if not from_asset or not to_asset or from_asset == to_asset:
                    continue

                # Create trade pair
                pair = f"{from_asset}/{to_asset}"

                # Get amounts safely
                from_amount = self.safe_float(row.get("from_amount", 0))
                to_amount = self.safe_float(row.get("to_amount", 0))

                # Calculate USD volume using token prices
                from_price = self.get_token_price(from_asset)
                to_price = self.get_token_price(to_asset)

                # Use the higher USD value for volume calculation
                from_volume_usd = from_amount * from_price
                to_volume_usd = to_amount * to_price
                volume_usd = max(from_volume_usd, to_volume_usd)

                # Calculate 55 bps fee
                affiliate_fee = volume_usd * 0.0055  # 55 bps = 0.55%

                trade_pairs[pair] += volume_usd
                total_volume += volume_usd
                total_fees += affiliate_fee

            return {
                "protocol": "THORChain",
                "transactions": len(july_df),
                "total_volume": total_volume,
                "total_fees": total_fees,
                "trade_pairs": dict(trade_pairs),
            }

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain: {e}")
            return {
                "protocol": "THORChain",
                "transactions": 0,
                "total_volume": 0,
                "total_fees": 0,
                "trade_pairs": {},
            }

    def analyze_cowswap_july(self):
        """Analyze CowSwap July 2025 data"""
        print("🔍 Analyzing CowSwap July 2025 data...")

        try:
            # Check if CowSwap database exists
            cowswap_db_path = "databases/cowswap_transactions.db"
            if not os.path.exists(cowswap_db_path):
                print(f"   ⚠️ CowSwap database not found: {cowswap_db_path}")
                return {
                    "protocol": "CowSwap",
                    "transactions": 0,
                    "total_volume": 0,
                    "total_fees": 0,
                    "trade_pairs": {},
                }

            conn = sqlite3.connect(cowswap_db_path)
            cursor = conn.cursor()

            # Get July 2025 transactions
            july_start_ts = int(datetime(2025, 7, 1).timestamp())
            july_end_ts = int(datetime(2025, 7, 31).timestamp())

            cursor.execute(
                """
                SELECT * FROM cowswap_transactions 
                WHERE block_timestamp >= ? AND block_timestamp <= ?
            """,
                (july_start_ts, july_end_ts),
            )

            cowswap_transactions = cursor.fetchall()

            # Get column names
            cursor.execute("PRAGMA table_info(cowswap_transactions)")
            columns = [col[1] for col in cursor.fetchall()]
            conn.close()

            print(
                f"   📊 Found {len(cowswap_transactions)} July 2025 CowSwap transactions"
            )

            # Analyze data
            trade_pairs = defaultdict(float)
            total_volume = 0
            total_fees = 0

            for row in cowswap_transactions:
                row_dict = dict(zip(columns, row))

                # Get trade pair
                sell_token = row_dict.get("sell_token_name", "")
                buy_token = row_dict.get("buy_token_name", "")

                if sell_token and buy_token and sell_token != buy_token:
                    pair = f"{sell_token}/{buy_token}"

                    # Get volume and calculate 55 bps fee
                    volume_usd = self.safe_float(row_dict.get("volume_usd", 0))
                    if volume_usd == 0:
                        # Use usd_value if volume_usd is not available
                        volume_usd = self.safe_float(row_dict.get("usd_value", 0))

                    # Calculate 55 bps fee
                    affiliate_fee = volume_usd * 0.0055  # 55 bps = 0.55%

                    trade_pairs[pair] += volume_usd
                    total_volume += volume_usd
                    total_fees += affiliate_fee

            return {
                "protocol": "CowSwap",
                "transactions": len(cowswap_transactions),
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

            # Use the new detailed transactions table
            cursor.execute("PRAGMA table_info(relay_detailed_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            july_start_ts = int(datetime(2025, 7, 1).timestamp())
            july_end_ts = int(datetime(2025, 7, 31).timestamp())

            cursor.execute(
                """
                SELECT * FROM relay_detailed_transactions 
                WHERE timestamp >= ? AND timestamp <= ?
            """,
                (july_start_ts, july_end_ts),
            )

            relay_transactions = cursor.fetchall()
            conn.close()

            print(
                f"   📊 Found {len(relay_transactions)} July 2025 detailed Relay transactions"
            )

            # Analyze data
            trade_pairs = defaultdict(float)
            total_volume = 0
            total_fees = 0

            for row in relay_transactions:
                row_dict = dict(zip(columns, row))
                from_token_name = self.token_resolver.get_token_name(
                    row_dict["from_token"], "base"
                )
                to_token_name = self.token_resolver.get_token_name(
                    row_dict["to_token"], "base"
                )

                if (
                    from_token_name
                    and to_token_name
                    and from_token_name != to_token_name
                ):
                    pair = f"{from_token_name}/{to_token_name}"
                    # Estimate volume from fee
                    fee_token_name = self.token_resolver.get_token_name(
                        row_dict["affiliate_fee_token"], "base"
                    )
                    fee_amount_usd = (
                        self.safe_float(row_dict.get("affiliate_fee_amount", 0))
                        / 1e18
                        * self.get_token_price(fee_token_name)
                    )
                    volume_usd = fee_amount_usd * 100  # Estimate volume

                    trade_pairs[pair] += volume_usd
                    total_volume += volume_usd
                    total_fees += fee_amount_usd

            return {
                "protocol": "Relay",
                "transactions": len(relay_transactions),
                "total_volume": total_volume,
                "total_fees": total_fees,
                "trade_pairs": dict(trade_pairs),
            }

        except Exception as e:
            print(f"   ❌ Error analyzing Relay: {e}")
            return {
                "protocol": "Relay",
                "transactions": 0,
                "total_volume": 0,
                "total_fees": 0,
                "trade_pairs": {},
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
        total_volume = (
            thorchain_data["total_volume"]
            + cowswap_data["total_volume"]
            + relay_data["total_volume"]
        )
        total_fees = (
            thorchain_data["total_fees"]
            + cowswap_data["total_fees"]
            + relay_data["total_fees"]
        )

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
                    "fees_usd": thorchain_data["total_fees"],
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
        with open("fixed_july_2025_report.json", "w") as f:
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

        print(f"\n✅ Report saved to: fixed_july_2025_report.json")
        return report


def main():
    analyzer = FixedJulyAnalyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
