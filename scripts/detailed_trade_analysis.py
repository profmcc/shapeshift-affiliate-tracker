#!/usr/bin/env python3
"""
Detailed Trade Pair Analysis
Enhanced analysis that properly handles trade pairs from all sources.
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


class DetailedTradeAnalyzer:
    def __init__(self):
        self.token_resolver = TokenNameResolver()
        self.trade_pairs = defaultdict(int)
        self.platform_stats = defaultdict(lambda: defaultdict(int))
        self.token_volume = defaultdict(float)

    def analyze_thorchain_csv(self):
        """Analyze THORChain CSV for actual trade pairs"""
        print("🔍 Analyzing THORChain CSV for trade pairs...")

        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Create trade pairs from from_asset and to_asset
            for _, row in df.iterrows():
                from_asset = str(row["from_asset"]).strip()
                to_asset = str(row["to_asset"]).strip()

                if from_asset and to_asset and from_asset != to_asset:
                    pair = f"{from_asset}/{to_asset}"
                    self.trade_pairs[pair] += 1
                    self.platform_stats["THORChain"][pair] += 1

                    # Track volume
                    try:
                        from_amount = (
                            float(row["from_amount"])
                            if pd.notna(row["from_amount"])
                            else 0
                        )
                        self.token_volume[from_asset] += from_amount
                    except:
                        pass

            print(f"   ✅ Found {len(df)} THORChain transactions")

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain CSV: {e}")

    def analyze_cowswap_excel(self):
        """Analyze CowSwap Excel for trade pairs"""
        print("🔍 Analyzing CowSwap Excel for trade pairs...")

        try:
            df = pd.read_excel("webscrape/CoW Swap Partner Dashboard Table.xlsx")
            print(f"   📊 CowSwap Excel columns: {df.columns.tolist()}")

            # Look for columns that might contain trade pairs
            pair_columns = [
                col
                for col in df.columns
                if any(keyword in col.lower() for keyword in ["pair", "token", "asset"])
            ]

            if pair_columns:
                print(f"   📋 Found potential pair columns: {pair_columns}")

                for col in pair_columns:
                    pairs = df[col].value_counts()
                    for pair, count in pairs.items():
                        if pd.notna(pair) and str(pair).strip():
                            pair_str = str(pair).strip()
                            self.trade_pairs[pair_str] += count
                            self.platform_stats["CowSwap"][pair_str] += count

            print(f"   ✅ Found {len(df)} CowSwap records")

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap Excel: {e}")

    def analyze_relay_database(self):
        """Analyze Relay database for ETH pairs"""
        print("🔍 Analyzing Relay database...")

        try:
            conn = sqlite3.connect("databases/affiliate.db")
            cursor = conn.cursor()

            # Check if token_address_name column exists
            cursor.execute("PRAGMA table_info(relay_affiliate_fees)")
            columns = [row[1] for row in cursor.fetchall()]

            if "token_address_name" in columns:
                query = """
                    SELECT token_address_name, COUNT(*) as count
                    FROM relay_affiliate_fees 
                    WHERE token_address_name IS NOT NULL AND token_address_name != 'ETH'
                    GROUP BY token_address_name 
                    ORDER BY count DESC
                """
            else:
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
                    pair = f"ETH/{token}"
                    self.trade_pairs[pair] += count
                    self.platform_stats["Relay"][pair] += count

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

    def generate_detailed_report(self):
        """Generate detailed trade pair report"""
        print("\n" + "=" * 80)
        print("📊 DETAILED TRADE PAIR ANALYSIS")
        print("=" * 80)

        # Get top 10 overall trade pairs
        top_pairs = sorted(self.trade_pairs.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        print(f"\n🏆 TOP 10 TRADE PAIRS ACROSS ALL PLATFORMS:")
        print("-" * 60)
        for i, (pair, count) in enumerate(top_pairs, 1):
            print(f"{i:2d}. {pair:30s}: {count:6,} transactions")

        # Platform breakdown for top pairs
        print(f"\n📋 PLATFORM BREAKDOWN FOR TOP PAIRS:")
        print("-" * 60)
        for pair, _ in top_pairs:
            print(f"\n{pair}:")
            for platform, pairs in self.platform_stats.items():
                if pair in pairs:
                    print(f"   {platform:20s}: {pairs[pair]:6,}")

        # Platform totals
        print(f"\n📊 PLATFORM TOTALS:")
        print("-" * 50)
        for platform, pairs in self.platform_stats.items():
            total = sum(pairs.values())
            unique_pairs = len(pairs)
            print(
                f"{platform:20s}: {total:6,} transactions, {unique_pairs:3d} unique pairs"
            )

        # Token volume analysis
        if self.token_volume:
            print(f"\n💰 TOP TOKENS BY VOLUME:")
            print("-" * 40)
            top_tokens = sorted(
                self.token_volume.items(), key=lambda x: x[1], reverse=True
            )[:10]
            for i, (token, volume) in enumerate(top_tokens, 1):
                print(f"{i:2d}. {token:15s}: {volume:12,.2f}")

        # Save detailed results
        self.save_detailed_results()

    def save_detailed_results(self):
        """Save detailed analysis results"""
        results = {
            "top_pairs": dict(
                sorted(self.trade_pairs.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "platform_stats": dict(self.platform_stats),
            "token_volume": dict(
                sorted(self.token_volume.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "summary": {
                "total_unique_pairs": len(self.trade_pairs),
                "total_transactions": sum(self.trade_pairs.values()),
                "platforms_analyzed": list(self.platform_stats.keys()),
            },
        }

        with open("detailed_trade_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Detailed results saved to: detailed_trade_analysis_results.json")

    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting detailed trade pair analysis...")

        # Analyze webscrape data first (most comprehensive)
        self.analyze_thorchain_csv()
        self.analyze_cowswap_excel()

        # Analyze databases
        self.analyze_relay_database()
        self.analyze_portals_database()
        self.analyze_chainflip_database()

        # Generate report
        self.generate_detailed_report()


def main():
    """Main function"""
    analyzer = DetailedTradeAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
