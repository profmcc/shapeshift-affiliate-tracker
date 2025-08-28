#!/usr/bin/env python3
"""
Unified July 2025 Analysis
Comprehensive analysis with consistent formatting, shared utilities, and unified database.
"""

import sqlite3
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import requests

# Add shared directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.token_name_resolver import TokenNameResolver


class UnifiedJulyAnalyzer:
    def __init__(self):
        self.token_resolver = TokenNameResolver()
        self.unified_db_path = "databases/unified_july_2025.db"
        self.july_start = datetime(2025, 7, 1)
        self.july_end = datetime(2025, 7, 31)

        # Initialize unified database
        self.init_unified_database()

        # Token price cache
        self.price_cache = {}

    def init_unified_database(self):
        """Initialize unified database with consistent schema"""
        os.makedirs(os.path.dirname(self.unified_db_path), exist_ok=True)
        conn = sqlite3.connect(self.unified_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS unified_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER,
                timestamp INTEGER NOT NULL,
                from_token TEXT NOT NULL,
                to_token TEXT NOT NULL,
                from_amount REAL NOT NULL,
                to_amount REAL NOT NULL,
                from_amount_usd REAL NOT NULL,
                to_amount_usd REAL NOT NULL,
                volume_usd REAL NOT NULL,
                affiliate_fee_amount REAL,
                affiliate_fee_usd REAL,
                affiliate_fee_token TEXT,
                affiliate_address TEXT,
                sender_address TEXT,
                recipient_address TEXT,
                event_type TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(protocol, tx_hash, chain)
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_protocol ON unified_transactions(protocol)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON unified_transactions(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_from_token ON unified_transactions(from_token)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_to_token ON unified_transactions(to_token)"
        )

        conn.commit()
        conn.close()
        print(f"✅ Unified database initialized: {self.unified_db_path}")

    def get_token_price(self, token_symbol: str) -> float:
        """Get token price in USD using CoinGecko API with caching"""
        if token_symbol in self.price_cache:
            return self.price_cache[token_symbol]

        try:
            # Map common tokens to CoinGecko IDs
            token_map = {
                "ETH": "ethereum",
                "WETH": "ethereum",
                "USDC": "usd-coin",
                "USDT": "tether",
                "FOX": "shapeshift-fox-token",
                "BTC": "bitcoin",
                "DOGE": "dogecoin",
                "ATOM": "cosmos",
                "TCY": "tcy",  # May need different mapping
                "ARB": "arbitrum",
                "1INCH": "1inch",
                "MATIC": "matic-network",
            }

            coin_id = token_map.get(token_symbol.upper(), token_symbol.lower())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()

            if coin_id in data and "usd" in data[coin_id]:
                price = data[coin_id]["usd"]
                self.price_cache[token_symbol] = price
                return price
            else:
                # Fallback prices for unknown tokens
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
                }
                price = fallback_prices.get(token_symbol.upper(), 1.0)
                self.price_cache[token_symbol] = price
                return price

        except Exception as e:
            print(f"⚠️ Error getting price for {token_symbol}: {e}")
            # Default fallback
            price = 1.0 if token_symbol.upper() in ["USDC", "USDT"] else 0.1
            self.price_cache[token_symbol] = price
            return price

    def normalize_token_symbol(
        self, token_address: str, chain: str = "ethereum"
    ) -> str:
        """Normalize token address to symbol using shared resolver"""
        try:
            return self.token_resolver.get_token_name(token_address, chain)
        except:
            # Fallback for common tokens
            common_tokens = {
                "0x0000000000000000000000000000000000000000": "ETH",
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
                "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8": "USDC",
                "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
                "0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d": "FOX",
            }
            return common_tokens.get(token_address, "UNKNOWN")

    def analyze_thorchain_july(self):
        """Analyze THORChain July 2025 data"""
        print("🔍 Analyzing THORChain July 2025 data...")

        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Convert timestamps to datetime
            df["timestamp"] = pd.to_datetime(
                df["timestamp"], format="%b %d %Y %I:%M:%S %p (GMT-7)", errors="coerce"
            )

            # Filter for July 2025
            july_mask = (df["timestamp"] >= self.july_start) & (
                df["timestamp"] <= self.july_end
            )
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 THORChain transactions")

            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()

            for _, row in july_df.iterrows():
                from_asset = str(row["from_asset"]).strip()
                to_asset = str(row["to_asset"]).strip()

                if from_asset and to_asset and from_asset != to_asset:
                    # Get amounts
                    from_amount = (
                        float(row["from_amount"]) if pd.notna(row["from_amount"]) else 0
                    )
                    to_amount = (
                        float(row["to_amount"]) if pd.notna(row["to_amount"]) else 0
                    )

                    # Get USD values
                    from_price = self.get_token_price(from_asset)
                    to_price = self.get_token_price(to_asset)
                    from_amount_usd = from_amount * from_price
                    to_amount_usd = to_amount * to_price
                    volume_usd = max(from_amount_usd, to_amount_usd)

                    # Insert into unified database
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO unified_transactions 
                        (protocol, chain, tx_hash, block_number, timestamp, from_token, to_token,
                         from_amount, to_amount, from_amount_usd, to_amount_usd, volume_usd,
                         affiliate_fee_amount, affiliate_fee_usd, affiliate_fee_token, affiliate_address,
                         sender_address, recipient_address, event_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            "THORChain",
                            "thorchain",
                            row.get("tx_hash", "unknown"),
                            row.get("block_number", 0),
                            int(row["timestamp"].timestamp()),
                            from_asset,
                            to_asset,
                            from_amount,
                            to_amount,
                            from_amount_usd,
                            to_amount_usd,
                            volume_usd,
                            0,
                            0,
                            "",
                            "",
                            "",
                            "",
                            "swap",
                        ),
                    )

            conn.commit()
            conn.close()
            print(f"   ✅ Saved {len(july_df)} THORChain transactions")

        except Exception as e:
            print(f"   ❌ Error analyzing THORChain: {e}")

    def analyze_cowswap_july(self):
        """Analyze CowSwap July 2025 data"""
        print("🔍 Analyzing CowSwap July 2025 data...")

        try:
            df = pd.read_excel("webscrape/CoW Swap Partner Dashboard Table.xlsx")

            # Convert date column to datetime
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # Filter for July 2025
            july_mask = (df["Date"] >= self.july_start) & (df["Date"] <= self.july_end)
            july_df = df[july_mask]

            print(f"   📊 Found {len(july_df)} July 2025 CowSwap transactions")

            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()

            for _, row in july_df.iterrows():
                # Extract token symbols from trade pair
                trade_pair = str(row.get("Trade Pair", ""))
                if "/" in trade_pair:
                    from_token, to_token = trade_pair.split("/", 1)
                else:
                    from_token, to_token = "UNKNOWN", "UNKNOWN"

                # Get amounts
                volume = float(row.get("Volume", 0))
                affiliate_fee = float(row.get("Affiliate Fee", 0))

                # Get USD values
                from_price = self.get_token_price(from_token)
                to_price = self.get_token_price(to_token)
                from_amount = volume / from_price if from_price > 0 else 0
                to_amount = volume / to_price if to_price > 0 else 0

                # Insert into unified database
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO unified_transactions 
                    (protocol, chain, tx_hash, block_number, timestamp, from_token, to_token,
                     from_amount, to_amount, from_amount_usd, to_amount_usd, volume_usd,
                     affiliate_fee_amount, affiliate_fee_usd, affiliate_fee_token, affiliate_address,
                     sender_address, recipient_address, event_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        "CowSwap",
                        "ethereum",
                        row.get("Transaction Hash", "unknown"),
                        row.get("Block Number", 0),
                        int(row["Date"].timestamp()),
                        from_token,
                        to_token,
                        from_amount,
                        to_amount,
                        volume,
                        volume,
                        volume,
                        affiliate_fee,
                        affiliate_fee,
                        from_token,
                        "",
                        "",
                        "",
                        "swap",
                    ),
                )

            conn.commit()
            conn.close()
            print(f"   ✅ Saved {len(july_df)} CowSwap transactions")

        except Exception as e:
            print(f"   ❌ Error analyzing CowSwap: {e}")

    def analyze_relay_july(self):
        """Analyze Relay July 2025 data from database"""
        print("🔍 Analyzing Relay July 2025 data...")

        try:
            # Connect to Relay database
            relay_db_path = "databases/affiliate.db"
            if not os.path.exists(relay_db_path):
                print(f"   ⚠️ Relay database not found: {relay_db_path}")
                return

            relay_conn = sqlite3.connect(relay_db_path)
            relay_cursor = relay_conn.cursor()

            # Get July 2025 transactions
            relay_cursor.execute(
                """
                SELECT * FROM relay_affiliate_fees 
                WHERE timestamp >= ? AND timestamp <= ?
            """,
                (int(self.july_start.timestamp()), int(self.july_end.timestamp())),
            )

            relay_transactions = relay_cursor.fetchall()
            relay_conn.close()

            print(f"   📊 Found {len(relay_transactions)} July 2025 Relay transactions")

            # Get column names
            relay_conn = sqlite3.connect(relay_db_path)
            relay_cursor = relay_conn.cursor()
            relay_cursor.execute("PRAGMA table_info(relay_affiliate_fees)")
            columns = [row[1] for row in relay_cursor.fetchall()]
            relay_conn.close()

            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()

            for row in relay_transactions:
                row_dict = dict(zip(columns, row))

                # Extract token information
                token_address = row_dict.get("token_address", "")
                token_symbol = self.normalize_token_symbol(
                    token_address, row_dict.get("chain", "ethereum")
                )

                # Get amounts
                fee_amount = float(row_dict.get("fee_amount", 0))
                fee_amount_usd = fee_amount * self.get_token_price(token_symbol)

                # Insert into unified database
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO unified_transactions 
                    (protocol, chain, tx_hash, block_number, timestamp, from_token, to_token,
                     from_amount, to_amount, from_amount_usd, to_amount_usd, volume_usd,
                     affiliate_fee_amount, affiliate_fee_usd, affiliate_fee_token, affiliate_address,
                     sender_address, recipient_address, event_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        "Relay",
                        row_dict.get("chain", "ethereum"),
                        row_dict.get("tx_hash", "unknown"),
                        row_dict.get("block_number", 0),
                        row_dict.get("timestamp", 0),
                        token_symbol,
                        token_symbol,
                        fee_amount,
                        fee_amount,
                        fee_amount_usd,
                        fee_amount_usd,
                        fee_amount_usd,
                        fee_amount,
                        fee_amount_usd,
                        token_symbol,
                        row_dict.get("affiliate_address", ""),
                        row_dict.get("sender", ""),
                        row_dict.get("recipient", ""),
                        "affiliate_fee",
                    ),
                )

            conn.commit()
            conn.close()
            print(f"   ✅ Saved {len(relay_transactions)} Relay transactions")

        except Exception as e:
            print(f"   ❌ Error analyzing Relay: {e}")

    def generate_unified_report(self):
        """Generate comprehensive report from unified database"""
        print("\n📊 Generating unified report...")

        conn = sqlite3.connect(self.unified_db_path)
        cursor = conn.cursor()

        # Get total statistics
        cursor.execute("SELECT COUNT(*) FROM unified_transactions")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(volume_usd) FROM unified_transactions")
        total_volume = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM unified_transactions")
        total_fees = cursor.fetchone()[0] or 0

        # Get top trade pairs
        cursor.execute(
            """
            SELECT from_token, to_token, SUM(volume_usd) as total_volume, COUNT(*) as count
            FROM unified_transactions 
            GROUP BY from_token, to_token 
            ORDER BY total_volume DESC 
            LIMIT 10
        """
        )
        top_pairs = cursor.fetchall()

        # Get protocol breakdown
        cursor.execute(
            """
            SELECT protocol, COUNT(*) as count, SUM(volume_usd) as volume, SUM(affiliate_fee_usd) as fees
            FROM unified_transactions 
            GROUP BY protocol 
            ORDER BY volume DESC
        """
        )
        protocol_stats = cursor.fetchall()

        # Get affiliate breakdown
        cursor.execute(
            """
            SELECT affiliate_fee_token, SUM(affiliate_fee_usd) as total_fees, COUNT(*) as count
            FROM unified_transactions 
            WHERE affiliate_fee_usd > 0
            GROUP BY affiliate_fee_token 
            ORDER BY total_fees DESC
        """
        )
        affiliate_stats = cursor.fetchall()

        conn.close()

        # Create report
        report = {
            "summary": {
                "total_transactions": total_transactions,
                "total_volume_usd": total_volume,
                "total_affiliate_fees_usd": total_fees,
            },
            "top_trade_pairs": [
                {
                    "pair": f"{from_token}/{to_token}",
                    "volume_usd": volume,
                    "count": count,
                }
                for from_token, to_token, volume, count in top_pairs
            ],
            "protocol_breakdown": [
                {
                    "protocol": protocol,
                    "count": count,
                    "volume_usd": volume,
                    "fees_usd": fees,
                }
                for protocol, count, volume, fees in protocol_stats
            ],
            "affiliate_breakdown": [
                {"token": token, "fees_usd": fees, "count": count}
                for token, fees, count in affiliate_stats
            ],
        }

        # Save report
        with open("unified_july_2025_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print(f"\n📊 UNIFIED JULY 2025 ANALYSIS SUMMARY")
        print(f"=" * 60)
        print(f"Total Transactions: {total_transactions:,}")
        print(f"Total Volume: ${total_volume:,.2f}")
        print(f"Total Affiliate Fees: ${total_fees:,.2f}")

        print(f"\n🏆 TOP 5 TRADE PAIRS:")
        for i, pair_data in enumerate(report["top_trade_pairs"][:5], 1):
            print(
                f"{i}. {pair_data['pair']}: ${pair_data['volume_usd']:,.2f} ({pair_data['count']} trades)"
            )

        print(f"\n📊 PROTOCOL BREAKDOWN:")
        for protocol_data in report["protocol_breakdown"]:
            print(
                f"   {protocol_data['protocol']}: ${protocol_data['volume_usd']:,.2f} volume, ${protocol_data['fees_usd']:,.2f} fees"
            )

        print(f"\n💰 AFFILIATE BREAKDOWN:")
        for affiliate_data in report["affiliate_breakdown"]:
            print(
                f"   {affiliate_data['token']}: ${affiliate_data['fees_usd']:,.2f} ({affiliate_data['count']} transactions)"
            )

        return report

    def run_analysis(self):
        """Run complete unified analysis"""
        print("🚀 Starting Unified July 2025 Analysis")
        print("=" * 60)

        # Analyze all protocols
        self.analyze_thorchain_july()
        self.analyze_cowswap_july()
        self.analyze_relay_july()

        # Generate unified report
        report = self.generate_unified_report()

        print(f"\n✅ Analysis complete! Report saved to: unified_july_2025_report.json")
        return report


def main():
    analyzer = UnifiedJulyAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
