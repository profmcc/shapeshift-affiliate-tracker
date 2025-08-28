#!/usr/bin/env python3
"""
CSV Master Runner
Runs multiple CSV-based affiliate fee listeners and consolidates data.

This master runner:
1. Initializes all protocol-specific listeners (Portals, CoW Swap, THORChain)
2. Runs each listener independently to scan for affiliate transactions
3. Consolidates all data into a single CSV file
4. Provides comprehensive statistics across all protocols

Each listener is completely separated and can be run independently:
- Portals: Cross-chain bridge affiliate fees
- CoW Swap: DEX aggregator affiliate fees  
- THORChain: Cross-chain swap affiliate fees
"""

import os
import csv
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import argparse

# Import CSV listeners - each is completely independent
from csv_portals_listener import CSVPortalsListener
from csv_relay_listener import CSVRelayListener
from csv_thorchain_listener import CSVThorChainListener
from csv_cowswap_listener import CSVCowSwapListener

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CSVMasterRunner:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Initialize all protocol listeners
        # Each listener is completely independent and handles its own CSV files
        self.listeners = {
            "portals": CSVPortalsListener(csv_dir),  # Cross-chain bridge affiliate fees
            "relay": CSVRelayListener(csv_dir),  # Relay protocol affiliate fees
            "thorchain": CSVThorChainListener(csv_dir),  # THORChain swap affiliate fees
            "cowswap": CSVCowSwapListener(csv_dir),  # CoW Swap DEX affiliate fees
        }

        # Create consolidated CSV structure
        self.init_consolidated_csv()

    def init_consolidated_csv(self):
        """Initialize consolidated CSV file that combines data from all protocols"""
        os.makedirs(self.csv_dir, exist_ok=True)

        consolidated_csv = os.path.join(
            self.csv_dir, "consolidated_affiliate_transactions.csv"
        )

        if not os.path.exists(consolidated_csv):
            headers = [
                "source",
                "chain",
                "tx_hash",
                "block_number",
                "block_timestamp",
                "block_date",
                "input_token",
                "input_amount",
                "output_token",
                "output_amount",
                "sender",
                "recipient",
                "partner",
                "affiliate_token",
                "affiliate_amount",
                "affiliate_fee_usd",
                "volume_usd",
                "created_at",
                "created_date",
            ]

            with open(consolidated_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created consolidated CSV: {consolidated_csv}")

    def consolidate_csv_data(self):
        """
        Consolidate data from all CSV files into one master file

        This function reads data from each protocol's CSV files and combines them
        into a single consolidated file for easy analysis across all protocols.
        """
        logger.info("🔄 Consolidating CSV data from all protocols...")

        consolidated_data = []

        # Process Portals transactions
        portals_csv = os.path.join(self.csv_dir, "portals_transactions.csv")
        if os.path.exists(portals_csv):
            try:
                df = pd.read_csv(portals_csv)
                for _, row in df.iterrows():
                    consolidated_data.append(
                        {
                            "source": "portals",
                            "chain": row["chain"],
                            "tx_hash": row["tx_hash"],
                            "block_number": row["block_number"],
                            "block_timestamp": row["block_timestamp"],
                            "block_date": row["block_date"],
                            "input_token": row["input_token"],
                            "input_amount": row["input_amount"],
                            "output_token": row["output_token"],
                            "output_amount": row["output_amount"],
                            "sender": row.get("sender"),
                            "recipient": row.get("recipient"),
                            "partner": row.get("partner"),
                            "affiliate_token": row["affiliate_token"],
                            "affiliate_amount": row["affiliate_amount"],
                            "affiliate_fee_usd": row["affiliate_fee_usd"],
                            "volume_usd": row["volume_usd"],
                            "created_at": row["created_at"],
                            "created_date": row["created_date"],
                        }
                    )
                logger.info(f"   📊 Added {len(df)} Portals transactions")
            except Exception as e:
                logger.error(f"Error processing Portals CSV: {e}")

        # Process Relay transactions
        relay_csv = os.path.join(self.csv_dir, "relay_transactions.csv")
        if os.path.exists(relay_csv):
            try:
                df = pd.read_csv(relay_csv)
                for _, row in df.iterrows():
                    consolidated_data.append(
                        {
                            "source": "relay",
                            "chain": row["chain"],
                            "tx_hash": row["tx_hash"],
                            "block_number": row["block_number"],
                            "block_timestamp": row["block_timestamp"],
                            "block_date": row["block_date"],
                            "input_token": row["input_token"],
                            "input_amount": row["input_amount"],
                            "output_token": row["output_token"],
                            "output_amount": row["output_amount"],
                            "sender": row.get("sender"),
                            "recipient": row.get("recipient"),
                            "partner": row.get("partner"),
                            "affiliate_token": row["affiliate_token"],
                            "affiliate_amount": row["affiliate_amount"],
                            "affiliate_fee_usd": row["affiliate_fee_usd"],
                            "volume_usd": row["volume_usd"],
                            "created_at": row["created_at"],
                            "created_date": row["created_date"],
                        }
                    )
                logger.info(f"   📊 Added {len(df)} Relay transactions")
            except Exception as e:
                logger.error(f"Error processing Relay CSV: {e}")

        # Process THORChain transactions
        thorchain_csv = os.path.join(self.csv_dir, "thorchain_transactions.csv")
        if os.path.exists(thorchain_csv):
            try:
                df = pd.read_csv(thorchain_csv)
                for _, row in df.iterrows():
                    consolidated_data.append(
                        {
                            "source": "thorchain",
                            "chain": "thorchain",  # THORChain is its own chain
                            "tx_hash": row["tx_id"],
                            "block_number": row["height"],
                            "block_timestamp": row["timestamp"],
                            "block_date": row["date"],
                            "input_token": row["from_asset"],
                            "input_amount": row["from_amount"],
                            "output_token": row["to_asset"],
                            "output_amount": row["to_amount"],
                            "sender": row.get("from_address"),
                            "recipient": row.get("to_address"),
                            "partner": row.get("affiliate_address"),
                            "affiliate_token": row.get("affiliate_token"),
                            "affiliate_amount": row.get("affiliate_amount"),
                            "affiliate_fee_usd": row.get("affiliate_fee_usd", 0.0),
                            "volume_usd": row.get("volume_usd", 0.0),
                            "created_at": row["created_at"],
                            "created_date": row["created_date"],
                        }
                    )
                logger.info(f"   📊 Added {len(df)} THORChain transactions")
            except Exception as e:
                logger.error(f"Error processing THORChain CSV: {e}")

        # Process CoW Swap transactions
        cowswap_csv = os.path.join(self.csv_dir, "cowswap_transactions.csv")
        if os.path.exists(cowswap_csv):
            try:
                df = pd.read_csv(cowswap_csv)
                for _, row in df.iterrows():
                    consolidated_data.append(
                        {
                            "source": "cowswap",
                            "chain": row["chain"],
                            "tx_hash": row["tx_hash"],
                            "block_number": row["block_number"],
                            "block_timestamp": row["block_timestamp"],
                            "block_date": row["block_time"],
                            "input_token": row["sell_token"],
                            "input_amount": row["sell_amount"],
                            "output_token": row["buy_token"],
                            "output_amount": row["buy_amount"],
                            "sender": row.get("trader"),
                            "recipient": row.get("owner"),
                            "partner": row.get("affiliate_address"),
                            "affiliate_token": row.get("affiliate_token"),
                            "affiliate_amount": row.get("affiliate_amount"),
                            "affiliate_fee_usd": row.get("affiliate_fee_usd", 0.0),
                            "volume_usd": row.get("volume_usd", 0.0),
                            "created_at": row["created_at"],
                            "created_date": row["created_date"],
                        }
                    )
                logger.info(f"   📊 Added {len(df)} CoW Swap transactions")
            except Exception as e:
                logger.error(f"Error processing CoW Swap CSV: {e}")

        if consolidated_data:
            # Write consolidated CSV
            consolidated_csv = os.path.join(
                self.csv_dir, "consolidated_affiliate_transactions.csv"
            )

            with open(consolidated_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=consolidated_data[0].keys())
                writer.writeheader()
                writer.writerows(consolidated_data)

            logger.info(
                f"✅ Consolidated {len(consolidated_data)} transactions to: {consolidated_csv}"
            )

            # Show summary
            df = pd.read_csv(consolidated_csv)
            print(f"\n📊 Consolidated CSV Summary:")
            print(f"   Total transactions: {len(df)}")
            print(f"   Sources: {df['source'].unique()}")
            print(f"   Unique chains: {df['chain'].nunique()}")
            print(f"   Unique transaction hashes: {df['tx_hash'].nunique()}")

            if "block_date" in df.columns and df["block_date"].notna().any():
                print(
                    f"   Date range: {df['block_date'].min()} to {df['block_date'].max()}"
                )

            # Show breakdown by source
            print(f"\n📈 Breakdown by Source:")
            source_counts = df["source"].value_counts()
            for source, count in source_counts.items():
                print(f"   {source.capitalize()}: {count} transactions")

        else:
            logger.info("No data to consolidate")

    def run_all_listeners(self, blocks_to_scan: int = 1000):
        """
        Run all CSV-based listeners to scan for affiliate transactions

        Args:
            blocks_to_scan: Number of blocks to scan (for block-based listeners)
        """
        logger.info("🚀 Starting CSV Master Runner - All Protocols")

        total_events = 0

        # Run each listener independently
        for listener_name, listener in self.listeners.items():
            logger.info(f"\n🔍 Running {listener_name.upper()} listener...")
            try:
                # Each listener has its own run_listener method with appropriate parameters
                if listener_name == "thorchain":
                    # THORChain uses API calls, not block scanning
                    listener.run_listener(max_actions=100, action_limit=50)
                else:
                    # Other listeners use block scanning
                    listener.run_listener(blocks_to_scan)

                # Count events from the listener's CSV
                csv_file = os.path.join(
                    self.csv_dir, f"{listener_name}_transactions.csv"
                )
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    total_events += len(df)

            except Exception as e:
                logger.error(f"Error running {listener_name} listener: {e}")

        logger.info(
            f"\n✅ All listeners completed! Total events across all sources: {total_events}"
        )

        # Consolidate all data
        self.consolidate_csv_data()

    def show_overall_stats(self):
        """
        Show overall statistics from all CSV files

        This provides a comprehensive view of all affiliate transaction data
        across all protocols and chains.
        """
        logger.info("📊 Overall CSV Statistics - All Protocols")

        csv_files = []
        for file in os.listdir(self.csv_dir):
            if file.endswith(".csv"):
                csv_files.append(file)

        print(f"\n📁 CSV Files in {self.csv_dir}:")
        total_transactions = 0

        for csv_file in sorted(csv_files):
            file_path = os.path.join(self.csv_dir, csv_file)
            try:
                df = pd.read_csv(file_path)
                print(f"   {csv_file:40} {len(df):>6} rows")
                total_transactions += len(df)
            except Exception as e:
                print(f"   {csv_file:40} Error reading - {e}")

        print(f"\n📊 Total transactions across all files: {total_transactions}")

        # Show recent transactions from consolidated file
        consolidated_csv = os.path.join(
            self.csv_dir, "consolidated_affiliate_transactions.csv"
        )
        if os.path.exists(consolidated_csv):
            try:
                df = pd.read_csv(consolidated_csv)
                if len(df) > 0:
                    print(f"\n🔍 Recent Transactions (All Protocols):")
                    recent = df.sort_values("block_timestamp", ascending=False).head(5)
                    for _, row in recent.iterrows():
                        print(
                            f"   {row['source'].upper()}: {row['chain']} - {row['tx_hash'][:10]}... - {row.get('block_date', 'N/A')}"
                        )
            except Exception as e:
                print(f"Error reading consolidated CSV: {e}")


def main():
    """Main function to run the CSV Master Runner"""
    parser = argparse.ArgumentParser(
        description="CSV Master Runner for All Affiliate Fee Listeners"
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=1000,
        help="Number of blocks to scan (for block-based listeners)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show statistics only, don't run listeners",
    )
    args = parser.parse_args()

    try:
        runner = CSVMasterRunner()

        if args.stats_only:
            runner.show_overall_stats()
        else:
            runner.run_all_listeners(args.blocks)
            runner.show_overall_stats()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
