#!/usr/bin/env python3
"""
Comprehensive July 2025 Analysis
Combines Relay, THORChain, and CowSwap data for accurate affiliate distribution.
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


class ComprehensiveJulyAnalyzer:
    def __init__(self):
        self.token_resolver = TokenNameResolver()
        self.trade_pairs = defaultdict(
            lambda: defaultdict(float)
        )  # pair -> affiliate -> volume
        self.affiliate_volumes = defaultdict(float)
        self.total_volumes = defaultdict(float)

        # July 2025 date range
        self.july_start = datetime(2025, 7, 1)
        self.july_end = datetime(2025, 7, 31)

    def analyze_relay_july(self):
        """Analyze Relay July 2025 data"""
        print("🔍 Analyzing Relay July 2025 data...")

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

                print(f"   📊 Found {len(results)} July 2025 Relay transactions")

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

    def analyze_thorchain_july(self):
        """Analyze THORChain July 2025 data"""
        print("🔍 Analyzing THORChain July 2025 data...")

        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Convert human-readable timestamps to datetime
            df["timestamp"] = pd.to_datetime(
                df["timestamp"], format="%b %d %Y %I:%M:%S %p (GMT-7)", errors="coerce"
            )

            # Filter for July 2025
            july_mask = (df["timestamp"] >= self.july_start) & (
                df["timestamp"] <= self.july_end
            )
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 THORChain transactions")

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
        """Analyze CowSwap July 2025 data"""
        print("🔍 Analyzing CowSwap July 2025 data...")

        try:
            df = pd.read_excel("webscrape/CoW Swap Partner Dashboard Table.xlsx")

            # Convert Block Time to datetime
            df["Block Time"] = pd.to_datetime(df["Block Time"], errors="coerce")

            # Filter for July 2025
            july_mask = (df["Block Time"] >= self.july_start) & (
                df["Block Time"] <= self.july_end
            )
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 CowSwap transactions")

            for _, row in july_df.iterrows():
                sell_token = str(row["Sell Token"]).strip()
                buy_token = str(row["Buy Token"]).strip()

                if sell_token and buy_token and sell_token != buy_token:
                    pair = f"{sell_token}/{buy_token}"

                    # Get volume from USD Value column
                    try:
                        volume = (
                            float(row["USD Value"]) if pd.notna(row["USD Value"]) else 0
                        )
                    except:
                        volume = 0

                    # Use CowSwap as affiliate
                    affiliate = "CowSwap"

                    self.trade_pairs[pair][affiliate] += volume
                    self.affiliate_volumes[affiliate] += volume
                    self.total_volumes[pair] += volume

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap July data: {e}")

    def generate_comprehensive_report(self):
        """Generate comprehensive July 2025 analysis report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE JULY 2025 TRADE PAIR ANALYSIS")
        print("=" * 80)

        if not self.trade_pairs:
            print("❌ No July 2025 data found")
            return

        # Get top 10 trade pairs by total volume
        top_pairs = sorted(
            self.total_volumes.items(), key=lambda x: x[1], reverse=True
        )[:10]

        print(f"\n🏆 TOP 10 TRADE PAIRS IN JULY 2025:")
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
            print(f"{affiliate:20s}: {volume:12,.2f} ({percentage:5.1f}%)")

        # FOX-specific analysis
        fox_pairs = {k: v for k, v in self.total_volumes.items() if "FOX" in k}
        if fox_pairs:
            print(f"\n🦊 FOX TRADE PAIRS ANALYSIS:")
            print("-" * 40)
            total_fox_volume = sum(fox_pairs.values())
            print(f"Total FOX volume: {total_fox_volume:,.2f}")

            for pair, volume in sorted(
                fox_pairs.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"{pair:20s}: {volume:10,.2f}")

            # FOX affiliate breakdown
            fox_affiliate_volumes = defaultdict(float)
            for pair in fox_pairs.keys():
                for affiliate, volume in self.trade_pairs[pair].items():
                    fox_affiliate_volumes[affiliate] += volume

            print(f"\nFOX Affiliate Breakdown:")
            for affiliate, volume in sorted(
                fox_affiliate_volumes.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (
                    (volume / total_fox_volume * 100) if total_fox_volume > 0 else 0
                )
                print(f"   {affiliate:15s}: {volume:10,.2f} ({percentage:5.1f}%)")

        # Save detailed results
        self.save_comprehensive_results()

    def save_comprehensive_results(self):
        """Save comprehensive analysis results"""
        results = {
            "comprehensive_july_2025_analysis": {
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

        with open("comprehensive_july_2025_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(
            f"\n💾 Comprehensive July 2025 results saved to: comprehensive_july_2025_analysis_results.json"
        )

    def run_comprehensive_analysis(self):
        """Run complete comprehensive July 2025 analysis"""
        print("🚀 Starting Comprehensive July 2025 trade pair analysis...")

        # Analyze all data sources for July 2025
        self.analyze_relay_july()
        self.analyze_thorchain_july()
        self.analyze_cowswap_july()

        # Generate comprehensive report
        self.generate_comprehensive_report()


def main():
    """Main function"""
    analyzer = ComprehensiveJulyAnalyzer()
    analyzer.run_comprehensive_analysis()


if __name__ == "__main__":
    main()
