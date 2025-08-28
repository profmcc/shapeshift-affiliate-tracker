#!/usr/bin/env python3
"""
Comprehensive Trade Pair Analysis
Analyzes all databases and webscrape data to find top trade pairs across all platforms.
Uses token names instead of addresses for better aggregation.
"""

import sqlite3
import pandas as pd
import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import sys

# Add shared directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.token_name_resolver import TokenNameResolver


class ComprehensiveTradeAnalyzer:
    def __init__(self):
        self.token_resolver = TokenNameResolver()
        self.trade_pairs = defaultdict(int)
        self.platform_stats = defaultdict(lambda: defaultdict(int))

    def analyze_relay_database(self):
        """Analyze Relay database for trade pairs"""
        print("🔍 Analyzing Relay database...")

        try:
            conn = sqlite3.connect("databases/affiliate.db")

            # Check if token_address_name column exists
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(relay_affiliate_fees)")
            columns = [row[1] for row in cursor.fetchall()]

            if "token_address_name" in columns:
                # Use token names if available
                query = """
                    SELECT token_address_name, COUNT(*) as count
                    FROM relay_affiliate_fees 
                    WHERE token_address_name IS NOT NULL 
                    GROUP BY token_address_name 
                    ORDER BY count DESC
                """
            else:
                # Fallback to token addresses
                query = """
                    SELECT token_address, COUNT(*) as count
                    FROM relay_affiliate_fees 
                    WHERE token_address != '0x0000000000000000000000000000000000000000'
                    GROUP BY token_address 
                    ORDER BY count DESC
                """

            cursor.execute(query)
            results = cursor.fetchall()

            for token, count in results:
                if token and token != "ETH":
                    self.trade_pairs[f"ETH/{token}"] += count
                    self.platform_stats["Relay"][f"ETH/{token}"] += count

            print(f"   ✅ Found {len(results)} unique tokens in Relay")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Relay: {e}")

    def analyze_portals_database(self):
        """Analyze Portals database for trade pairs"""
        print("🔍 Analyzing Portals database...")

        try:
            conn = sqlite3.connect("databases/portals_transactions.db")
            cursor = conn.cursor()

            # Check if token name columns exist
            cursor.execute("PRAGMA table_info(portals_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            if "input_token_name" in columns and "output_token_name" in columns:
                query = """
                    SELECT input_token_name, output_token_name, COUNT(*) as count
                    FROM portals_transactions 
                    WHERE input_token_name IS NOT NULL AND output_token_name IS NOT NULL
                    GROUP BY input_token_name, output_token_name 
                    ORDER BY count DESC
                """
            else:
                # Fallback to token addresses
                query = """
                    SELECT input_token, output_token, COUNT(*) as count
                    FROM portals_transactions 
                    WHERE input_token IS NOT NULL AND output_token IS NOT NULL
                    GROUP BY input_token, output_token 
                    ORDER BY count DESC
                """

            cursor.execute(query)
            results = cursor.fetchall()

            for input_token, output_token, count in results:
                if input_token and output_token:
                    # Resolve token names if using addresses
                    if "input_token_name" not in columns:
                        input_name = self.token_resolver.get_token_name(
                            input_token, "ethereum"
                        )
                        output_name = self.token_resolver.get_token_name(
                            output_token, "ethereum"
                        )
                    else:
                        input_name = input_token
                        output_name = output_token

                    if input_name and output_name:
                        pair = f"{input_name}/{output_name}"
                        self.trade_pairs[pair] += count
                        self.platform_stats["Portals"][pair] += count

            print(f"   ✅ Found {len(results)} unique pairs in Portals")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Portals: {e}")

    def analyze_chainflip_database(self):
        """Analyze Chainflip database for trade pairs"""
        print("🔍 Analyzing Chainflip database...")

        try:
            conn = sqlite3.connect("databases/chainflip_transactions.db")
            cursor = conn.cursor()

            # Check if token name columns exist
            cursor.execute("PRAGMA table_info(chainflip_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            if "source_asset_name" in columns and "destination_asset_name" in columns:
                query = """
                    SELECT source_asset_name, destination_asset_name, COUNT(*) as count
                    FROM chainflip_transactions 
                    WHERE source_asset_name IS NOT NULL AND destination_asset_name IS NOT NULL
                    GROUP BY source_asset_name, destination_asset_name 
                    ORDER BY count DESC
                """
            else:
                # Fallback to asset addresses
                query = """
                    SELECT source_asset, destination_asset, COUNT(*) as count
                    FROM chainflip_transactions 
                    WHERE source_asset IS NOT NULL AND destination_asset IS NOT NULL
                    GROUP BY source_asset, destination_asset 
                    ORDER BY count DESC
                """

            cursor.execute(query)
            results = cursor.fetchall()

            for source_asset, dest_asset, count in results:
                if source_asset and dest_asset:
                    # Resolve asset names if using addresses
                    if "source_asset_name" not in columns:
                        source_name = self.token_resolver.get_token_name(
                            source_asset, "chainflip"
                        )
                        dest_name = self.token_resolver.get_token_name(
                            dest_asset, "chainflip"
                        )
                    else:
                        source_name = source_asset
                        dest_name = dest_asset

                    if source_name and dest_name:
                        pair = f"{source_name}/{dest_name}"
                        self.trade_pairs[pair] += count
                        self.platform_stats["Chainflip"][pair] += count

            print(f"   ✅ Found {len(results)} unique pairs in Chainflip")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Chainflip: {e}")

    def analyze_cowswap_database(self):
        """Analyze CowSwap database for trade pairs"""
        print("🔍 Analyzing CowSwap database...")

        try:
            conn = sqlite3.connect("databases/cowswap_transactions.db")
            cursor = conn.cursor()

            # Check if token name columns exist
            cursor.execute("PRAGMA table_info(cowswap_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            if "sell_token_name" in columns and "buy_token_name" in columns:
                query = """
                    SELECT sell_token_name, buy_token_name, COUNT(*) as count
                    FROM cowswap_transactions 
                    WHERE sell_token_name IS NOT NULL AND buy_token_name IS NOT NULL
                    GROUP BY sell_token_name, buy_token_name 
                    ORDER BY count DESC
                """
            else:
                # Fallback to token addresses
                query = """
                    SELECT sell_token, buy_token, COUNT(*) as count
                    FROM cowswap_transactions 
                    WHERE sell_token IS NOT NULL AND buy_token IS NOT NULL
                    GROUP BY sell_token, buy_token 
                    ORDER BY count DESC
                """

            cursor.execute(query)
            results = cursor.fetchall()

            for sell_token, buy_token, count in results:
                if sell_token and buy_token:
                    # Resolve token names if using addresses
                    if "sell_token_name" not in columns:
                        sell_name = self.token_resolver.get_token_name(
                            sell_token, "ethereum"
                        )
                        buy_name = self.token_resolver.get_token_name(
                            buy_token, "ethereum"
                        )
                    else:
                        sell_name = sell_token
                        buy_name = buy_token

                    if sell_name and buy_name:
                        pair = f"{sell_name}/{buy_token}"
                        self.trade_pairs[pair] += count
                        self.platform_stats["CowSwap"][pair] += count

            print(f"   ✅ Found {len(results)} unique pairs in CowSwap")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap: {e}")

    def analyze_thorchain_database(self):
        """Analyze THORChain database for trade pairs"""
        print("🔍 Analyzing THORChain database...")

        try:
            conn = sqlite3.connect("databases/thorchain_transactions.db")
            cursor = conn.cursor()

            # Check if token name columns exist
            cursor.execute("PRAGMA table_info(thorchain_transactions)")
            columns = [row[1] for row in cursor.fetchall()]

            if "from_asset_name" in columns and "to_asset_name" in columns:
                query = """
                    SELECT from_asset_name, to_asset_name, COUNT(*) as count
                    FROM thorchain_transactions 
                    WHERE from_asset_name IS NOT NULL AND to_asset_name IS NOT NULL
                    GROUP BY from_asset_name, to_asset_name 
                    ORDER BY count DESC
                """
            else:
                # Fallback to asset addresses
                query = """
                    SELECT from_asset, to_asset, COUNT(*) as count
                    FROM thorchain_transactions 
                    WHERE from_asset IS NOT NULL AND to_asset IS NOT NULL
                    GROUP BY from_asset, to_asset 
                    ORDER BY count DESC
                """

            cursor.execute(query)
            results = cursor.fetchall()

            for from_asset, to_asset, count in results:
                if from_asset and to_asset:
                    # Resolve asset names if using addresses
                    if "from_asset_name" not in columns:
                        from_name = self.token_resolver.get_token_name(
                            from_asset, "thorchain"
                        )
                        to_name = self.token_resolver.get_token_name(
                            to_asset, "thorchain"
                        )
                    else:
                        from_name = from_asset
                        to_name = to_asset

                    if from_name and to_name:
                        pair = f"{from_name}/{to_name}"
                        self.trade_pairs[pair] += count
                        self.platform_stats["THORChain"][pair] += count

            print(f"   ✅ Found {len(results)} unique pairs in THORChain")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain: {e}")

    def analyze_webscrape_data(self):
        """Analyze webscrape CSV and Excel data"""
        print("🔍 Analyzing webscrape data...")

        # Analyze THORChain CSV
        csv_path = "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                print(f"   📊 THORChain CSV: {len(df)} records")

                # Look for trade pair columns
                pair_columns = [
                    col
                    for col in df.columns
                    if "pair" in col.lower() or "asset" in col.lower()
                ]
                if pair_columns:
                    for col in pair_columns:
                        pairs = df[col].value_counts()
                        for pair, count in pairs.items():
                            if pd.notna(pair) and str(pair).strip():
                                self.trade_pairs[str(pair)] += count
                                self.platform_stats["THORChain_Webscrape"][
                                    str(pair)
                                ] += count

            except Exception as e:
                print(f"   ❌ Error analyzing THORChain CSV: {e}")

        # Analyze CowSwap Excel
        excel_path = "webscrape/CoW Swap Partner Dashboard Table.xlsx"
        if os.path.exists(excel_path):
            try:
                # Try to read Excel file
                df = pd.read_excel(excel_path)
                print(f"   📊 CowSwap Excel: {len(df)} records")

                # Look for trade pair columns
                pair_columns = [
                    col
                    for col in df.columns
                    if "pair" in col.lower() or "token" in col.lower()
                ]
                if pair_columns:
                    for col in pair_columns:
                        pairs = df[col].value_counts()
                        for pair, count in pairs.items():
                            if pd.notna(pair) and str(pair).strip():
                                self.trade_pairs[str(pair)] += count
                                self.platform_stats["CowSwap_Webscrape"][
                                    str(pair)
                                ] += count

            except Exception as e:
                print(f"   ❌ Error analyzing CowSwap Excel: {e}")

    def analyze_comprehensive_database(self):
        """Analyze comprehensive database"""
        print("🔍 Analyzing comprehensive database...")

        try:
            conn = sqlite3.connect("databases/comprehensive_affiliate.db")
            cursor = conn.cursor()

            query = """
                SELECT from_asset, to_asset, COUNT(*) as count
                FROM comprehensive_transactions 
                WHERE from_asset IS NOT NULL AND to_asset IS NOT NULL
                GROUP BY from_asset, to_asset 
                ORDER BY count DESC
            """

            cursor.execute(query)
            results = cursor.fetchall()

            for from_asset, to_asset, count in results:
                if from_asset and to_asset:
                    # Resolve token names
                    from_name = self.token_resolver.get_token_name(
                        from_asset, "ethereum"
                    )
                    to_name = self.token_resolver.get_token_name(to_asset, "ethereum")

                    if from_name and to_name:
                        pair = f"{from_name}/{to_name}"
                        self.trade_pairs[pair] += count
                        self.platform_stats["Comprehensive"][pair] += count

            print(f"   ✅ Found {len(results)} unique pairs in Comprehensive")
            conn.close()

        except Exception as e:
            print(f"   ❌ Error analyzing Comprehensive: {e}")

    def generate_report(self):
        """Generate comprehensive trade pair report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TRADE PAIR ANALYSIS")
        print("=" * 80)

        # Get top 5 overall trade pairs
        top_pairs = sorted(self.trade_pairs.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        print(f"\n🏆 TOP 5 TRADE PAIRS ACROSS ALL PLATFORMS:")
        print("-" * 50)
        for i, (pair, count) in enumerate(top_pairs, 1):
            print(f"{i}. {pair}: {count:,} transactions")

        # Platform breakdown for top pairs
        print(f"\n📋 PLATFORM BREAKDOWN FOR TOP PAIRS:")
        print("-" * 50)
        for pair, _ in top_pairs:
            print(f"\n{pair}:")
            for platform, pairs in self.platform_stats.items():
                if pair in pairs:
                    print(f"   {platform}: {pairs[pair]:,}")

        # Platform totals
        print(f"\n📊 PLATFORM TOTALS:")
        print("-" * 30)
        for platform, pairs in self.platform_stats.items():
            total = sum(pairs.values())
            unique_pairs = len(pairs)
            print(f"{platform}: {total:,} transactions, {unique_pairs} unique pairs")

        # Save detailed results
        self.save_detailed_results()

    def save_detailed_results(self):
        """Save detailed analysis results"""
        results = {
            "top_pairs": dict(
                sorted(self.trade_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "platform_stats": dict(self.platform_stats),
            "summary": {
                "total_unique_pairs": len(self.trade_pairs),
                "total_transactions": sum(self.trade_pairs.values()),
                "platforms_analyzed": list(self.platform_stats.keys()),
            },
        }

        with open("trade_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Detailed results saved to: trade_analysis_results.json")

    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting comprehensive trade pair analysis...")

        # Analyze all databases
        self.analyze_relay_database()
        self.analyze_portals_database()
        self.analyze_chainflip_database()
        self.analyze_cowswap_database()
        self.analyze_thorchain_database()
        self.analyze_comprehensive_database()

        # Analyze webscrape data
        self.analyze_webscrape_data()

        # Generate report
        self.generate_report()


def main():
    """Main function"""
    analyzer = ComprehensiveTradeAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
