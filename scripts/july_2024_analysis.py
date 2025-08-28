#!/usr/bin/env python3
"""
July 2024 Trade Analysis
Analyzes July 2024 data for top trade pairs with volume and affiliate percentages.
"""

import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import sys

# Add shared directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.token_name_resolver import TokenNameResolver


class July2024Analyzer:
    def __init__(self):
        self.token_resolver = TokenNameResolver()
        self.trade_pairs = defaultdict(
            lambda: defaultdict(float)
        )  # pair -> affiliate -> volume
        self.affiliate_volumes = defaultdict(float)
        self.total_volumes = defaultdict(float)

        # July 2024 date range
        self.july_start = datetime(2024, 7, 1)
        self.july_end = datetime(2024, 7, 31)

    def analyze_thorchain_july(self):
        """Analyze THORChain July 2024 data"""
        print("🔍 Analyzing THORChain July 2024 data...")

        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

            # Filter for July 2024
            july_mask = (df["timestamp"] >= self.july_start) & (
                df["timestamp"] <= self.july_end
            )
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2024 THORChain transactions")

            for _, row in july_df.iterrows():
                from_asset = str(row["from_asset"]).strip()
                to_asset = str(row["to_asset"]).strip()

                if from_asset and to_asset and from_asset != to_asset:
                    pair = f"{from_asset}/{to_asset}"

                    # Get volume (use from_amount as volume)
                    try:
                        volume = (
                            float(row["from_amount"])
                            if pd.notna(row["from_amount"])
                            else 0
                        )
                    except:
                        volume = 0

                    # Use affiliate address from the data
                    affiliate = row.get("affiliate_address", "THORChain")

                    self.trade_pairs[pair][affiliate] += volume
                    self.affiliate_volumes[affiliate] += volume
                    self.total_volumes[pair] += volume

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain July data: {e}")

    def analyze_cowswap_july(self):
        """Analyze CowSwap July 2024 data"""
        print("🔍 Analyzing CowSwap July 2024 data...")

        try:
            df = pd.read_excel("webscrape/CoW Swap Partner Dashboard Table.xlsx")

            # Look for date/time columns
            date_columns = [
                col
                for col in df.columns
                if any(keyword in col.lower() for keyword in ["date", "time", "block"])
            ]

            if date_columns:
                print(f"   📋 Found date columns: {date_columns}")

                # Try to parse dates
                for date_col in date_columns:
                    try:
                        df[date_col] = pd.to_datetime(df[date_col])
                        july_mask = (df[date_col] >= self.july_start) & (
                            df[date_col] <= self.july_end
                        )
                        july_df = df[july_mask]

                        if len(july_df) > 0:
                            print(
                                f"   📊 Found {len(july_df)} July 2024 CowSwap transactions using {date_col}"
                            )

                            # Look for trade pair columns
                            pair_columns = [
                                col
                                for col in df.columns
                                if any(
                                    keyword in col.lower()
                                    for keyword in ["pair", "token", "asset"]
                                )
                            ]

                            for _, row in july_df.iterrows():
                                # Try to construct trade pair
                                if (
                                    "Sell Token" in df.columns
                                    and "Buy Token" in df.columns
                                ):
                                    sell_token = str(row["Sell Token"]).strip()
                                    buy_token = str(row["Buy Token"]).strip()

                                    if (
                                        sell_token
                                        and buy_token
                                        and sell_token != buy_token
                                    ):
                                        pair = f"{sell_token}/{buy_token}"

                                        # Get volume from USD Value column
                                        try:
                                            volume = (
                                                float(row["USD Value"])
                                                if pd.notna(row["USD Value"])
                                                else 0
                                            )
                                        except:
                                            volume = 0

                                        # Use CowSwap as affiliate
                                        affiliate = "CowSwap"

                                        self.trade_pairs[pair][affiliate] += volume
                                        self.affiliate_volumes[affiliate] += volume
                                        self.total_volumes[pair] += volume

                            break  # Use first successful date column

                    except Exception as e:
                        print(f"   ⚠️ Could not parse dates from {date_col}: {e}")
                        continue
            else:
                print("   ⚠️ No date columns found in CowSwap data")

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap July data: {e}")

    def analyze_relay_july(self):
        """Analyze Relay July 2024 data"""
        print("🔍 Analyzing Relay July 2024 data...")

        try:
            conn = sqlite3.connect("databases/affiliate.db")
            cursor = conn.cursor()

            # Check if timestamp column exists
            cursor.execute("PRAGMA table_info(relay_affiliate_fees)")
            columns = [row[1] for row in cursor.fetchall()]

            if "timestamp" in columns:
                # Convert July dates to timestamps
                july_start_ts = int(self.july_start.timestamp())
                july_end_ts = int(self.july_end.timestamp())

                query = """
                    SELECT token_address_name, amount, timestamp
                    FROM relay_affiliate_fees 
                    WHERE timestamp >= ? AND timestamp <= ?
                    AND token_address_name IS NOT NULL
                """

                cursor.execute(query, (july_start_ts, july_end_ts))
                results = cursor.fetchall()

                print(f"   📊 Found {len(results)} July 2024 Relay transactions")

                for token_name, amount_str, timestamp in results:
                    if token_name and token_name != "ETH":
                        pair = f"ETH/{token_name}"

                        try:
                            volume = float(amount_str) / 1e18  # Convert from wei to ETH
                        except:
                            volume = 0

                        affiliate = "Relay"

                        self.trade_pairs[pair][affiliate] += volume
                        self.affiliate_volumes[affiliate] += volume
                        self.total_volumes[pair] += volume

            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Relay July data: {e}")

    def analyze_portals_july(self):
        """Analyze Portals July 2024 data"""
        print("🔍 Analyzing Portals July 2024 data...")

        try:
            conn = sqlite3.connect("databases/portals_transactions.db")
            cursor = conn.cursor()

            # Check if block_timestamp column exists
            cursor.execute("PRAGMA table_info(portals_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            if "block_timestamp" in columns:
                # Convert July dates to timestamps
                july_start_ts = int(self.july_start.timestamp())
                july_end_ts = int(self.july_end.timestamp())

                query = """
                    SELECT input_token_name, output_token_name, input_amount, output_amount, block_timestamp
                    FROM portals_transactions 
                    WHERE block_timestamp >= ? AND block_timestamp <= ?
                    AND input_token_name IS NOT NULL AND output_token_name IS NOT NULL
                """

                cursor.execute(query, (july_start_ts, july_end_ts))
                results = cursor.fetchall()

                print(f"   📊 Found {len(results)} July 2024 Portals transactions")

                for (
                    input_token,
                    output_token,
                    input_amount,
                    output_amount,
                    timestamp,
                ) in results:
                    if input_token and output_token:
                        pair = f"{input_token}/{output_token}"

                        try:
                            # Use input amount as volume
                            volume = float(input_amount) if input_amount else 0
                        except:
                            volume = 0

                        affiliate = "Portals"

                        self.trade_pairs[pair][affiliate] += volume
                        self.affiliate_volumes[affiliate] += volume
                        self.total_volumes[pair] += volume

            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Portals July data: {e}")

    def generate_july_report(self):
        """Generate July 2024 analysis report"""
        print("\n" + "=" * 80)
        print("📊 JULY 2024 TRADE PAIR ANALYSIS")
        print("=" * 80)

        if not self.trade_pairs:
            print("❌ No July 2024 data found")
            return

        # Get top 10 trade pairs by total volume
        top_pairs = sorted(
            self.total_volumes.items(), key=lambda x: x[1], reverse=True
        )[:10]

        print(f"\n🏆 TOP 10 TRADE PAIRS IN JULY 2024:")
        print("-" * 60)
        for i, (pair, total_volume) in enumerate(top_pairs, 1):
            print(f"{i:2d}. {pair:30s}: {total_volume:12,.2f} volume")

        # Detailed breakdown for top pairs
        print(f"\n📋 DETAILED BREAKDOWN FOR TOP PAIRS:")
        print("-" * 60)

        for pair, total_volume in top_pairs:
            print(f"\n{pair}:")

            # Get affiliate breakdown for this pair
            affiliate_data = self.trade_pairs[pair]

            if affiliate_data:
                # Sort affiliates by volume
                sorted_affiliates = sorted(
                    affiliate_data.items(), key=lambda x: x[1], reverse=True
                )

                for affiliate, volume in sorted_affiliates:
                    percentage = (
                        (volume / total_volume * 100) if total_volume > 0 else 0
                    )
                    print(f"   {affiliate:15s}: {volume:10,.2f} ({percentage:5.1f}%)")

                # Show highest percentage affiliate
                top_affiliate, top_volume = sorted_affiliates[0]
                top_percentage = (
                    (top_volume / total_volume * 100) if total_volume > 0 else 0
                )
                print(f"   🏆 Highest: {top_affiliate} ({top_percentage:.1f}%)")

        # Overall affiliate statistics
        print(f"\n📊 OVERALL AFFILIATE STATISTICS:")
        print("-" * 50)
        total_overall_volume = sum(self.total_volumes.values())

        for affiliate, volume in sorted(
            self.affiliate_volumes.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (volume / total_overall_volume * 100) if total_overall_volume > 0 else 0
            )
            print(f"{affiliate:15s}: {volume:12,.2f} ({percentage:5.1f}%)")

        # Save detailed results
        self.save_july_results()

    def save_july_results(self):
        """Save July analysis results"""
        results = {
            "july_2024_analysis": {
                "date_range": {
                    "start": self.july_start.isoformat(),
                    "end": self.july_end.isoformat(),
                },
                "top_pairs": dict(
                    sorted(
                        self.total_volumes.items(), key=lambda x: x[1], reverse=True
                    )[:20]
                ),
                "affiliate_breakdown": dict(self.trade_pairs),
                "affiliate_totals": dict(self.affiliate_volumes),
                "summary": {
                    "total_unique_pairs": len(self.trade_pairs),
                    "total_volume": sum(self.total_volumes.values()),
                    "total_affiliates": len(self.affiliate_volumes),
                },
            }
        }

        with open("july_2024_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 July 2024 results saved to: july_2024_analysis_results.json")

    def run_analysis(self):
        """Run complete July 2024 analysis"""
        print("🚀 Starting July 2024 trade pair analysis...")

        # Analyze all data sources for July 2024
        self.analyze_thorchain_july()
        self.analyze_cowswap_july()
        self.analyze_relay_july()
        self.analyze_portals_july()

        # Generate report
        self.generate_july_report()


def main():
    """Main function"""
    analyzer = July2024Analyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
