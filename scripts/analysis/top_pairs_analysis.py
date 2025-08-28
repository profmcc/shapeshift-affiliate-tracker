#!/usr/bin/env python3
"""
Top Trading Pairs Analysis
Analyzes data from all protocol listeners to determine the top 10 trading pairs by volume.
"""

import sys
import os
import sqlite3
import pandas as pd
from typing import Dict, List, Tuple
import logging

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.token_name_resolver import TokenNameResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TopPairsAnalysis:
    def __init__(self):
        self.db_paths = {
            "relay": "databases/affiliate.db",
            "portals": "databases/portals_transactions.db",
            "thorchain": "databases/thorchain_transactions.db",
            "chainflip": "databases/chainflip_transactions.db",
            "cowswap": "databases/cowswap_transactions.db",
            "zerox": "databases/zerox_transactions.db",
        }
        self.all_trades = []

    def get_data_from_db(self, protocol: str, db_path: str) -> List[Dict]:
        """Fetch and normalize data from a specific protocol's database."""
        if not os.path.exists(db_path):
            logger.warning(f"Database not found for {protocol}: {db_path}")
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        trades = []

        try:
            if protocol == "relay":
                # Note: Simplified relay data extraction. Needs a more robust solution.
                # For now, we assume a separate process has populated trading pair info.
                logger.info("Relay data analysis is simplified and may not show pairs.")
                cursor.execute(
                    "SELECT from_token, to_token, volume_usd, affiliate_fee_usd FROM relay_affiliate_fees"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

            elif protocol == "portals":
                cursor.execute(
                    "SELECT input_token, output_token, volume_usd, affiliate_fee_usd FROM portals_transactions"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

            elif protocol == "thorchain":
                cursor.execute(
                    "SELECT from_asset, to_asset, volume_usd, affiliate_fee_usd FROM thorchain_transactions"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

            elif protocol == "chainflip":
                cursor.execute(
                    "SELECT source_asset_name, destination_asset_name, volume_usd, broker_fee_usd FROM chainflip_transactions"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

            elif protocol == "cowswap":
                cursor.execute(
                    "SELECT sell_token_name, buy_token_name, usd_value, affiliate_fee_usd FROM cowswap_transactions"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

            elif protocol == "zerox":
                cursor.execute(
                    "SELECT input_token, output_token, volume_usd, affiliate_fee_usd FROM zerox_transactions"
                )
                for row in cursor.fetchall():
                    trades.append(
                        {
                            "from_asset": row[0],
                            "to_asset": row[1],
                            "volume_usd": row[2],
                            "fee_usd": row[3],
                        }
                    )

        except sqlite3.OperationalError as e:
            logger.error(f"Error querying {protocol} database: {e}")
        finally:
            conn.close()

        return trades

    def run_analysis(self):
        """Run the full analysis across all protocols."""
        logger.info("🚀 Starting Top Pairs Analysis...")

        for protocol, db_path in self.db_paths.items():
            logger.info(f"🔍 Analyzing {protocol} data...")
            protocol_trades = self.get_data_from_db(protocol, db_path)
            if protocol_trades:
                self.all_trades.extend(protocol_trades)
                logger.info(f"   📊 Found {len(protocol_trades)} trades for {protocol}")
            else:
                logger.info(f"   ⚠️  No trades found for {protocol}")

        if not self.all_trades:
            logger.warning("No trading data found to analyze.")
            return

        # Create a DataFrame for analysis
        df = pd.DataFrame(self.all_trades)
        df["volume_usd"] = pd.to_numeric(df["volume_usd"], errors="coerce").fillna(0)
        df["fee_usd"] = pd.to_numeric(df["fee_usd"], errors="coerce").fillna(0)

        # Drop rows where asset names are None
        df.dropna(subset=["from_asset", "to_asset"], inplace=True)

        # Normalize asset names (e.g., WETH -> ETH)
        df["from_asset"] = df["from_asset"].astype(str)
        df["to_asset"] = df["to_asset"].astype(str)
        df.replace({"WETH": "ETH", "WBTC": "BTC", "None": "Unknown"}, inplace=True)

        # Create a canonical trading pair (e.g., ETH/USDC)
        df["pair"] = df.apply(
            lambda row: f"{row['from_asset']}/{row['to_asset']}"
            if row["from_asset"] < row["to_asset"]
            else f"{row['to_asset']}/{row['from_asset']}",
            axis=1,
        )

        # Group by trading pair and aggregate volume and fees
        top_pairs = (
            df.groupby("pair")
            .agg(
                total_volume_usd=("volume_usd", "sum"),
                total_fees_usd=("fee_usd", "sum"),
                trade_count=("pair", "size"),
            )
            .sort_values(by="total_volume_usd", ascending=False)
            .head(10)
        )

        # Print the report
        self.print_report(top_pairs)

    def print_report(self, top_pairs: pd.DataFrame):
        """Print the top trading pairs report."""
        logger.info("\n" + "=" * 80)
        logger.info("🏆 TOP 10 TRADING PAIRS BY VOLUME")
        logger.info("=" * 80)

        if top_pairs.empty:
            logger.info("No trading pairs found.")
            return

        print(
            top_pairs.to_string(
                formatters={
                    "total_volume_usd": "${:,.2f}".format,
                    "total_fees_usd": "${:,.2f}".format,
                    "trade_count": "{:,}".format,
                }
            )
        )
        logger.info("\n" + "=" * 80)


def main():
    """Main function"""
    analysis = TopPairsAnalysis()
    analysis.run_analysis()


if __name__ == "__main__":
    main()
