#!/usr/bin/env python3
"""
CSV-based THORChain Affiliate Fee Listener
Tracks ShapeShift affiliate fees from THORChain swaps using Midgard API.
Stores data in CSV format instead of databases.

This listener:
1. Connects to THORChain's Midgard API
2. Fetches swap actions and filters for ShapeShift affiliate IDs
3. Extracts affiliate fee data and transaction details
4. Saves everything to CSV files for easy analysis
"""

import os
import csv
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CSVThorChainListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # THORChain API endpoint
        self.midgard_url = "https://midgard.ninerealms.com"

        # ShapeShift affiliate identifiers in THORChain
        # These are the specific IDs that identify ShapeShift as the affiliate
        self.shapeshift_affiliate_ids = [
            "ss",  # Short identifier
            "thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p",  # Full THORChain address
        ]

        # Initialize CSV structure
        self.init_csv_structure()

        # Rate limiting and API settings
        self.api_delay = 1.0  # Seconds between API calls
        self.max_retries = 3  # Maximum retries for failed API calls

    def init_csv_structure(self):
        """Initialize CSV file structure for THORChain data"""
        os.makedirs(self.csv_dir, exist_ok=True)

        # Main THORChain transactions CSV
        thorchain_csv = os.path.join(self.csv_dir, "thorchain_transactions.csv")

        # Create CSV with headers if it doesn't exist
        if not os.path.exists(thorchain_csv):
            headers = [
                "tx_id",
                "date",
                "height",
                "from_address",
                "to_address",
                "affiliate_address",
                "affiliate_fee_basis_points",
                "affiliate_fee_amount",
                "affiliate_fee_usd",
                "from_asset",
                "to_asset",
                "from_amount",
                "to_amount",
                "from_amount_usd",
                "to_amount_usd",
                "volume_usd",
                "swap_path",
                "is_streaming_swap",
                "liquidity_fee",
                "swap_slip",
                "timestamp",
                "created_at",
                "created_date",
            ]

            with open(thorchain_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created THORChain CSV file: {thorchain_csv}")

        # Block tracker CSV for THORChain
        block_tracker_csv = os.path.join(self.csv_dir, "thorchain_block_tracker.csv")
        if not os.path.exists(block_tracker_csv):
            headers = [
                "last_processed_height",
                "last_processed_date",
                "total_actions_processed",
            ]
            with open(block_tracker_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created THORChain block tracker CSV: {block_tracker_csv}")

    def fetch_thorchain_actions(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Fetch THORChain actions from Midgard API

        Args:
            limit: Number of actions to fetch (max 50 per request)
            offset: Number of actions to skip (for pagination)

        Returns:
            List of THORChain actions or empty list if error
        """
        try:
            # Build API URL with parameters
            url = f"{self.midgard_url}/v2/actions"
            params = {
                "limit": min(limit, 50),  # Midgard API max is 50
                "offset": offset,
                "type": "swap",  # Only fetch swap actions
            }

            logger.info(f"🔍 Fetching THORChain actions from Midgard API...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            # Make API request with timeout
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                actions = data.get("actions", [])
                logger.info(f"   ✅ Retrieved {len(actions)} swap actions")
                return actions
            else:
                logger.error(f"❌ Midgard API error: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return []

        except requests.exceptions.Timeout:
            logger.error("❌ API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching THORChain actions: {e}")
            return []

    def is_shapeshift_affiliate(self, action: Dict) -> bool:
        """
        Check if a THORChain action involves ShapeShift as affiliate

        Args:
            action: THORChain action dictionary from API

        Returns:
            True if ShapeShift is the affiliate, False otherwise
        """
        try:
            # Extract affiliate address from action metadata
            # The affiliate address is nested in the swap metadata
            swap_metadata = action.get("metadata", {}).get("swap", {})
            affiliate_address = swap_metadata.get("affiliateAddress", "")

            # Check if any ShapeShift affiliate ID is present
            for affiliate_id in self.shapeshift_affiliate_ids:
                if affiliate_id.lower() in affiliate_address.lower():
                    logger.info(f"   ✅ Found ShapeShift affiliate: {affiliate_address}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking affiliate status: {e}")
            return False

    def extract_affiliate_data(self, action: Dict) -> Optional[Dict]:
        """
        Extract affiliate fee data from a THORChain action

        Args:
            action: THORChain action dictionary from API

        Returns:
            Dictionary with affiliate data or None if extraction fails
        """
        try:
            # Get basic transaction info
            tx_id = action.get("in", {}).get("txID", "")
            height = action.get("height", 0)
            date = action.get("date", "")

            # Get swap metadata
            swap_metadata = action.get("metadata", {}).get("swap", {})

            # Extract affiliate information
            affiliate_address = swap_metadata.get("affiliateAddress", "")
            affiliate_fee_basis_points = swap_metadata.get("affiliateFeeBasisPoints", 0)
            affiliate_fee_amount = swap_metadata.get("affiliateFeeAmount", 0)

            # Extract asset and amount information
            from_asset = swap_metadata.get("fromAsset", "")
            to_asset = swap_metadata.get("toAsset", "")
            from_amount = swap_metadata.get("fromAmount", 0)
            to_amount = swap_metadata.get("toAmount", 0)

            # Extract addresses
            from_address = swap_metadata.get("fromAddress", "")
            to_address = swap_metadata.get("toAddress", "")

            # Extract additional swap details
            swap_path = swap_metadata.get("swapPath", "")
            is_streaming_swap = swap_metadata.get("isStreamingSwap", False)
            liquidity_fee = swap_metadata.get("liquidityFee", 0)
            swap_slip = swap_metadata.get("swapSlip", 0)

            # Calculate USD values (if available)
            from_amount_usd = swap_metadata.get("fromAmountUSD", 0)
            to_amount_usd = swap_metadata.get("toAmountUSD", 0)
            volume_usd = swap_metadata.get("volumeUSD", 0)
            affiliate_fee_usd = swap_metadata.get("affiliateFeeUSD", 0)

            # Convert date to timestamp
            try:
                timestamp = int(
                    datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp()
                )
            except:
                timestamp = int(time.time())

            return {
                "tx_id": tx_id,
                "date": date,
                "height": height,
                "from_address": from_address,
                "to_address": to_address,
                "affiliate_address": affiliate_address,
                "affiliate_fee_basis_points": affiliate_fee_basis_points,
                "affiliate_fee_amount": affiliate_fee_amount,
                "affiliate_fee_usd": affiliate_fee_usd,
                "from_asset": from_asset,
                "to_asset": to_asset,
                "from_amount": from_amount,
                "to_amount": to_amount,
                "from_amount_usd": from_amount_usd,
                "to_amount_usd": to_amount_usd,
                "volume_usd": volume_usd,
                "swap_path": swap_path,
                "is_streaming_swap": is_streaming_swap,
                "liquidity_fee": liquidity_fee,
                "swap_slip": swap_slip,
                "timestamp": timestamp,
                "created_at": int(time.time()),
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            logger.error(f"Error extracting affiliate data: {e}")
            return None

    def save_actions_to_csv(self, actions: List[Dict]):
        """
        Save THORChain actions to CSV file

        Args:
            actions: List of action dictionaries to save
        """
        if not actions:
            return

        csv_file = os.path.join(self.csv_dir, "thorchain_transactions.csv")

        # Append new actions to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=actions[0].keys())

            for action in actions:
                try:
                    writer.writerow(action)
                except Exception as e:
                    logger.error(
                        f"Error saving action {action.get('tx_id', 'unknown')}: {e}"
                    )

        logger.info(f"💾 Saved {len(actions)} THORChain actions to CSV: {csv_file}")

    def update_block_tracker(self, last_height: int, total_processed: int):
        """
        Update block tracker CSV with processing status

        Args:
            last_height: Last processed block height
            total_processed: Total actions processed
        """
        csv_file = os.path.join(self.csv_dir, "thorchain_block_tracker.csv")

        # Write current status
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "last_processed_height",
                    "last_processed_date",
                    "total_actions_processed",
                ]
            )
            writer.writerow(
                [
                    str(last_height),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(total_processed),
                ]
            )

    def get_csv_stats(self):
        """Get CSV statistics for THORChain data"""
        csv_file = os.path.join(self.csv_dir, "thorchain_transactions.csv")

        if not os.path.exists(csv_file):
            print("No THORChain CSV file found")
            return

        try:
            df = pd.read_csv(csv_file)

            print(f"\n📊 THORChain CSV Statistics:")
            print(f"   Total transactions: {len(df)}")
            print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"   Total affiliate fees: ${df['affiliate_fee_usd'].sum():.2f}")
            print(f"   Total volume: ${df['volume_usd'].sum():.2f}")

            # Show recent transactions
            if len(df) > 0:
                print(f"\n🔍 Recent THORChain Transactions:")
                recent = df.sort_values("timestamp", ascending=False).head(3)
                for _, row in recent.iterrows():
                    print(
                        f"   {row['date']}: {row['from_asset']} → {row['to_asset']} (${row['affiliate_fee_usd']:.2f} fee)"
                    )

        except Exception as e:
            print(f"Error reading THORChain CSV: {e}")

    def run_listener(self, max_actions: int = 100, action_limit: int = 50):
        """
        Run the THORChain listener to fetch and process affiliate transactions

        Args:
            max_actions: Maximum total actions to process
            action_limit: Actions per API request (max 50)
        """
        logger.info("🚀 Starting CSV-based THORChain affiliate fee listener")

        total_processed = 0
        offset = 0
        all_affiliate_actions = []

        while total_processed < max_actions:
            # Fetch actions from API
            actions = self.fetch_thorchain_actions(action_limit, offset)

            if not actions:
                logger.info("No more actions to process")
                break

            # Process each action
            for action in actions:
                # Check if this is a ShapeShift affiliate transaction
                if self.is_shapeshift_affiliate(action):
                    # Extract affiliate data
                    affiliate_data = self.extract_affiliate_data(action)
                    if affiliate_data:
                        all_affiliate_actions.append(affiliate_data)
                        logger.info(
                            f"   ✅ Found affiliate transaction: {affiliate_data['tx_id']}"
                        )

                total_processed += 1

                if total_processed >= max_actions:
                    break

            # Update offset for next batch
            offset += len(actions)

            # Rate limiting
            time.sleep(self.api_delay)

            logger.info(
                f"   📊 Processed {total_processed} actions, found {len(all_affiliate_actions)} affiliate transactions"
            )

        # Save all affiliate actions to CSV
        if all_affiliate_actions:
            self.save_actions_to_csv(all_affiliate_actions)

            # Update block tracker
            if all_affiliate_actions:
                last_height = max(action["height"] for action in all_affiliate_actions)
                self.update_block_tracker(last_height, total_processed)

        logger.info(f"\n✅ THORChain listener completed!")
        logger.info(f"   Total actions processed: {total_processed}")
        logger.info(f"   Affiliate transactions found: {len(all_affiliate_actions)}")

        # Show statistics
        self.get_csv_stats()


def main():
    """Main function to run the THORChain listener"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV-based THORChain Affiliate Fee Listener"
    )
    parser.add_argument(
        "--max-actions", type=int, default=100, help="Maximum actions to process"
    )
    parser.add_argument(
        "--action-limit", type=int, default=50, help="Actions per API request (max 50)"
    )
    args = parser.parse_args()

    try:
        listener = CSVThorChainListener()
        listener.run_listener(args.max_actions, args.action_limit)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
