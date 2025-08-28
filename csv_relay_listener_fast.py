#!/usr/bin/env python3
"""
Fast CSV-based Relay Affiliate Fee Listener
Optimized version that quickly scans recent blocks for ShapeShift affiliate transactions.
"""

import os
import csv
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from web3 import Web3

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FastCSVRelayListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Get Alchemy API key
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found")

        self.init_csv_structure()

        # Focus on the most active chains for Relay
        self.chains = {
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "router": "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
                "start_block": None,  # Will be calculated dynamically
            },
            "arbitrum": {
                "name": "Arbitrum",
                "chain_id": 42161,
                "rpc_url": f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "router": "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
                "start_block": None,
            },
        }

        # ShapeShift affiliate addresses
        # The correct address for Relay is 0x35339070f178dC4119732982C23F5a8d88D3f8a3
        self.shapeshift_affiliates = {
            8453: "0x35339070f178dC4119732982C23F5a8d88D3f8a3",  # Base
            42161: "0x35339070f178dC4119732982C23F5a8d88D3f8a3",  # Arbitrum
        }

    def init_csv_structure(self):
        """Initialize CSV structure"""
        os.makedirs(self.csv_dir, exist_ok=True)

        relay_csv = os.path.join(self.csv_dir, "relay_transactions_fast.csv")
        if not os.path.exists(relay_csv):
            headers = [
                "chain",
                "tx_hash",
                "block_number",
                "block_timestamp",
                "block_date",
                "affiliate_involved",
                "volume_estimate",
                "created_at",
            ]

            with open(relay_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created fast relay CSV: {relay_csv}")

    def get_recent_blocks(self, w3: Web3, hours_back: int = 24) -> int:
        """Calculate how many blocks to scan for the last N hours"""
        try:
            latest_block = w3.eth.block_number
            latest_block_data = w3.eth.get_block(latest_block)
            latest_timestamp = latest_block_data["timestamp"]

            # Calculate timestamp for N hours ago
            target_timestamp = latest_timestamp - (hours_back * 3600)

            # Estimate blocks per second (roughly 12 seconds per block for most chains)
            blocks_per_second = 1 / 12
            seconds_diff = latest_timestamp - target_timestamp
            estimated_blocks = int(seconds_diff * blocks_per_second)

            # Add some buffer and cap at reasonable limits
            blocks_to_scan = min(max(estimated_blocks, 100), 2000)

            logger.info(f"Latest block: {latest_block}, timestamp: {latest_timestamp}")
            logger.info(f"Target timestamp: {target_timestamp}")
            logger.info(f"Will scan approximately {blocks_to_scan} blocks")

            return blocks_to_scan

        except Exception as e:
            logger.error(f"Error calculating block range: {e}")
            return 1000  # Default fallback

    def quick_affiliate_check(
        self, w3: Web3, tx_hash: str, affiliate_address: str
    ) -> bool:
        """Quick check if transaction involves affiliate address"""
        try:
            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(tx_hash)

            # Quick check in logs for affiliate address
            affiliate_clean = affiliate_address.lower().replace("0x", "")

            for log in receipt["logs"]:
                if log["topics"]:
                    for topic in log["topics"]:
                        topic_hex = topic.hex().lower()
                        if affiliate_clean in topic_hex:
                            return True

                        if log["data"] and affiliate_clean in log["data"].hex().lower():
                            return True

            return False

        except Exception as e:
            logger.debug(f"Error checking transaction {tx_hash}: {e}")
            return False

    def scan_chain_fast(self, chain_name: str, hours_back: int = 24):
        """Fast scan of a single chain"""
        chain_config = self.chains[chain_name]

        try:
            w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
            if not w3.is_connected():
                logger.error(f"Failed to connect to {chain_name}")
                return []

            logger.info(f"🔍 Scanning {chain_name} for last {hours_back} hours...")

            # Calculate blocks to scan
            blocks_to_scan = self.get_recent_blocks(w3, hours_back)
            latest_block = w3.eth.block_number
            start_block = max(0, latest_block - blocks_to_scan)

            logger.info(f"   Scanning blocks {start_block} to {latest_block}")

            events = []
            affiliate_address = self.shapeshift_affiliates.get(chain_config["chain_id"])

            # Scan in larger chunks for speed
            chunk_size = 500
            current_block = start_block

            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)

                try:
                    # Get logs from router contract
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "address": chain_config["router"],
                    }

                    logs = w3.eth.get_logs(filter_params)

                    if logs:
                        logger.info(
                            f"   Found {len(logs)} logs in blocks {current_block}-{end_block}"
                        )

                        # Check each transaction for affiliate involvement
                        for log in logs:
                            tx_hash = log["transactionHash"].hex()

                            # Quick affiliate check
                            if self.quick_affiliate_check(
                                w3, tx_hash, affiliate_address
                            ):
                                # Get block info
                                block = w3.eth.get_block(log["blockNumber"])

                                event_data = {
                                    "chain": chain_name,
                                    "tx_hash": tx_hash,
                                    "block_number": log["blockNumber"],
                                    "block_timestamp": block["timestamp"],
                                    "block_date": datetime.fromtimestamp(
                                        block["timestamp"]
                                    ).strftime("%Y-%m-%d %H:%M:%S"),
                                    "affiliate_involved": True,
                                    "volume_estimate": "High",  # Placeholder
                                    "created_at": int(time.time()),
                                }

                                events.append(event_data)
                                logger.info(
                                    f"   ✅ Found affiliate transaction: {tx_hash[:10]}..."
                                )

                    current_block = end_block + 1

                    # Small delay to avoid rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(
                        f"Error scanning blocks {current_block}-{end_block}: {e}"
                    )
                    current_block = end_block + 1
                    continue

            logger.info(
                f"   Completed {chain_name}: found {len(events)} affiliate transactions"
            )
            return events

        except Exception as e:
            logger.error(f"Error scanning {chain_name}: {e}")
            return []

    def save_events_fast(self, events: List[Dict]):
        """Save events to CSV quickly"""
        if not events:
            return

        csv_file = os.path.join(self.csv_dir, "relay_transactions_fast.csv")

        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())

            for event in events:
                try:
                    writer.writerow(event)
                except Exception as e:
                    logger.error(f"Error saving event: {e}")

        logger.info(f"💾 Saved {len(events)} events to fast CSV")

    def run_fast_scan(self, hours_back: int = 24):
        """Run fast scan of all chains"""
        logger.info("🚀 Starting FAST Relay affiliate fee scan")
        start_time = time.time()

        total_events = 0

        for chain_name in self.chains.keys():
            events = self.scan_chain_fast(chain_name, hours_back)
            self.save_events_fast(events)
            total_events += len(events)

        elapsed_time = time.time() - start_time
        logger.info(f"\n✅ Fast scan completed in {elapsed_time:.1f} seconds!")
        logger.info(f"   Total affiliate transactions found: {total_events}")

        # Show results
        if total_events > 0:
            self.show_results()
        else:
            logger.info(
                "   No affiliate transactions found in the specified time range"
            )

    def show_results(self):
        """Show scan results"""
        csv_file = os.path.join(self.csv_dir, "relay_transactions_fast.csv")

        if not os.path.exists(csv_file):
            return

        try:
            import pandas as pd

            df = pd.read_csv(csv_file)
            if len(df) > 0:
                print(f"\n📊 Fast Scan Results:")
                print(f"   Total transactions: {len(df)}")
                print(f"   Chains: {', '.join(df['chain'].unique())}")

                print(f"\n🔍 Recent Transactions:")
                recent = df.sort_values("block_timestamp", ascending=False).head(5)
                for _, row in recent.iterrows():
                    print(
                        f"   {row['chain']}: {row['tx_hash'][:10]}... - {row['block_date']}"
                    )

        except Exception as e:
            print(f"Error reading results: {e}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fast CSV Relay Affiliate Fee Listener"
    )
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    args = parser.parse_args()

    try:
        listener = FastCSVRelayListener()
        listener.run_fast_scan(args.hours)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
