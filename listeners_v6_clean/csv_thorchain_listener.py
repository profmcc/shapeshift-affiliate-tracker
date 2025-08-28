#!/usr/bin/env python3
"""
CSV THORChain Listener - Centralized Configuration Version
=========================================================

This listener monitors THORChain swaps for ShapeShift affiliate fees.
It uses the centralized configuration system and saves data to CSV files.

Key Features:
- Centralized configuration management
- CSV-based data storage (no databases)
- Midgard API integration for real-time swap data
- Dual detection: affiliate name "ss" + address thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju
- Cross-chain liquidity pool transaction support

Enhanced Affiliate Detection (Commented Out):
- Memo pattern detection using :ss: suffix (e.g., :ss:55, :ss:0)
- Asset-specific patterns: =:b: (Bitcoin), =:r: (RUNE), =:THOR.TCY: (THORChain)
- Based on discoveries from blocks 22,456,113 and 22,470,673

Author: ShapeShift Affiliate Tracker Team
Version: v6.0 - Clean Centralized CSV
Date: 2024
"""

import os
import sys
import time
import logging
import csv
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Import centralized configuration
from config_loader import (
    get_config,
    get_storage_path,
    get_listener_config,
    get_threshold,
)

# =============================================================================
# CONFIGURATION & SETUP
# =============================================================================


class CSVThorChainListener:
    """CSV-based listener for THORChain swaps with ShapeShift affiliate fees

    Note: Enhanced affiliate detection logic using memo patterns (:ss:) has been
    discovered and documented but is currently commented out. See the
    _is_shapeshift_affiliate_swap method for details on the enhanced detection
    patterns found in blocks 22,456,113 and 22,470,673.
    """

    def __init__(self):
        """Initialize the THORChain listener with centralized configuration"""
        # Load centralized configuration
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # Get THORChain-specific configuration
        thorchain_config = self.config.config.get("contracts", {}).get("thorchain", {})
        self.midgard_api = thorchain_config.get(
            "midgard_api", "https://midgard.ninerealms.com/v2"
        )
        self.thornode_api = thorchain_config.get(
            "thornode_api", "https://thornode.ninerealms.com"
        )

        # Get ShapeShift affiliate information for THORChain
        self.shapeshift_affiliate_address = thorchain_config.get(
            "affiliate_address", "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju"
        )
        self.shapeshift_affiliate_name = thorchain_config.get("affiliate_name", "ss")

        # Get storage paths
        self.csv_dir = self.config.get_storage_path("csv_directory")
        self.transactions_dir = os.path.join(self.csv_dir, "transactions")
        self.block_tracking_dir = os.path.join(self.csv_dir, "block_tracking")

        # Get listener configuration
        self.listener_config = self.config.get_listener_config("thorchain")
        self.api_rate_limit = self.listener_config.get("api_rate_limit", 1.0)
        self.max_swaps_per_request = self.listener_config.get(
            "max_swaps_per_request", 100
        )

        # Get thresholds
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")

        # Initialize CSV structure
        self._init_csv_structure()

        self.logger.info("✅ CSVThorChainListener initialized successfully")
        self.logger.info(
            f"🎯 THORChain affiliate address: {self.shapeshift_affiliate_address}"
        )
        self.logger.info(
            f"🎯 THORChain affiliate name: {self.shapeshift_affiliate_name}"
        )
        self.logger.info(f"🌐 Midgard API: {self.midgard_api}")

    def _init_csv_structure(self):
        """Initialize CSV file structure for THORChain data"""
        # Ensure directories exist
        os.makedirs(self.transactions_dir, exist_ok=True)
        os.makedirs(self.block_tracking_dir, exist_ok=True)

        # Initialize transactions CSV
        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )
        if not os.path.exists(transactions_path):
            headers = [
                "tx_hash",
                "chain",
                "block_number",
                "timestamp",
                "from_address",
                "to_address",
                "affiliate_address",
                "affiliate_fee_amount",
                "affiliate_fee_token",
                "affiliate_fee_usd",
                "volume_amount",
                "volume_token",
                "volume_usd",
                "gas_used",
                "gas_price",
                "pool",
                "from_asset",
                "to_asset",
                "from_amount",
                "to_amount",
                "affiliate_fee_asset",
                "affiliate_fee_amount_asset",
                "created_at",
            ]
            with open(transactions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(
                f"✅ Created THORChain transactions CSV: {transactions_path}"
            )

        # Initialize block tracker CSV (for API pagination tracking)
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )
        if not os.path.exists(block_tracker_path):
            headers = [
                "last_processed_offset",
                "last_processed_date",
                "total_swaps_processed",
            ]
            with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(
                f"✅ Created THORChain block tracker CSV: {block_tracker_path}"
            )

    # =============================================================================
    # CSV MANAGEMENT & TRACKING
    # =============================================================================

    def get_last_processed_offset(self) -> int:
        """Get the last processed offset for API pagination"""
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )

        if not os.path.exists(block_tracker_path):
            return 0

        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    return int(row.get("last_processed_offset", 0))
        except Exception as e:
            self.logger.error(f"❌ Error reading block tracker: {e}")

        return 0

    def update_block_tracker(self, offset: int):
        """Update the block tracker with the latest processed offset"""
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )

        # Read existing data
        rows = []
        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            pass

        # Update or add entry
        if rows:
            rows[0]["last_processed_offset"] = str(offset)
            rows[0]["last_processed_date"] = str(int(time.time()))
            rows[0]["total_swaps_processed"] = str(
                int(rows[0].get("total_swaps_processed", 0)) + 1
            )
        else:
            rows.append(
                {
                    "last_processed_offset": str(offset),
                    "last_processed_date": str(int(time.time())),
                    "total_swaps_processed": "1",
                }
            )

        # Write updated data
        headers = [
            "last_processed_offset",
            "last_processed_date",
            "total_swaps_processed",
        ]
        with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def save_transactions_to_csv(self, transactions: List[Dict[str, Any]]):
        """Save THORChain transactions to CSV file"""
        if not transactions:
            return

        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )

        with open(transactions_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
            writer.writerows(transactions)

        self.logger.info(f"✅ Saved {len(transactions)} THORChain transactions to CSV")

    # =============================================================================
    # THORCHAIN API INTEGRATION
    # =============================================================================

    def fetch_thorchain_swaps(
        self, offset: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch THORChain swaps from Midgard API"""
        try:
            url = f"{self.midgard_api}/actions"
            params = {
                "offset": offset,
                "limit": limit,
                "type": "swap",  # Only fetch swap actions
            }

            self.logger.info(
                f"📡 Fetching THORChain swaps: offset={offset}, limit={limit}"
            )

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            actions = data.get("actions", [])

            self.logger.info(f"✅ Fetched {len(actions)} THORChain swap actions")
            return actions

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Error fetching THORChain swaps: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Unexpected error fetching THORChain swaps: {e}")
            return []

    def filter_shapeshift_affiliate_swaps(
        self, swaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter swaps to only include ShapeShift affiliate transactions"""
        affiliate_swaps = []

        for swap in swaps:
            try:
                # Check if this swap involves ShapeShift affiliate
                if self._is_shapeshift_affiliate_swap(swap):
                    affiliate_swaps.append(swap)

            except Exception as e:
                self.logger.warning(f"⚠️ Error processing swap: {e}")
                continue

        self.logger.info(
            f"🎯 Found {len(affiliate_swaps)} ShapeShift affiliate swaps out of {len(swaps)} total"
        )
        return affiliate_swaps

    def _is_shapeshift_affiliate_swap(self, swap: Dict[str, Any]) -> bool:
        """Check if a swap involves ShapeShift affiliate"""
        try:
            # Check for affiliate name "ss" in the swap data
            swap_data = swap.get("in", {})
            if isinstance(swap_data, dict):
                # Look for affiliate information in swap metadata
                memo = swap_data.get("memo", "")
                if self.shapeshift_affiliate_name.lower() in memo.lower():
                    return True

                # Check for affiliate address in memo or other fields
                if self.shapeshift_affiliate_address.lower() in memo.lower():
                    return True

            # Check out data as well
            swap_data = swap.get("out", {})
            if isinstance(swap_data, dict):
                memo = swap_data.get("memo", "")
                if self.shapeshift_affiliate_name.lower() in memo.lower():
                    return True
                if self.shapeshift_affiliate_address.lower() in memo.lower():
                    return True

            # Check additional fields that might contain affiliate info
            for field in ["memo", "affiliate", "referrer", "partner"]:
                if (
                    field in swap
                    and self.shapeshift_affiliate_name.lower()
                    in str(swap[field]).lower()
                ):
                    return True
                if (
                    field in swap
                    and self.shapeshift_affiliate_address.lower()
                    in str(swap[field]).lower()
                ):
                    return True

            # =============================================================================
            # ENHANCED SHAPESHIFT AFFILIATE DETECTION LOGIC (COMMENTED OUT)
            # =============================================================================
            # Based on discoveries from blocks 22,456,113 and 22,470,673
            # This logic provides more accurate affiliate detection using memo patterns

            # # Check for ShapeShift affiliate memo patterns in swap metadata
            # swap_metadata = swap.get('metadata', {}).get('swap', {})
            # if swap_metadata:
            #     # Check memo field for ShapeShift affiliate pattern (:ss:)
            #     memo = swap_metadata.get('memo', '')
            #     if memo and ':ss:' in memo.lower():
            #         self.logger.info(f"🎯 Found ShapeShift affiliate transaction with :ss: pattern: {memo}")
            #         return True
            #
            #     # Check affiliate address in swap metadata
            #     affiliate_address = swap_metadata.get('affiliateAddress', '')
            #     if affiliate_address and self.shapeshift_affiliate_address in affiliate_address:
            #         self.logger.info(f"🎯 Found ShapeShift affiliate transaction with address: {affiliate_address}")
            #         return True
            #
            #     # Check for specific memo patterns we discovered:
            #     # =:b:...:ss:55 (Bitcoin transactions with 55 basis points)
            #     # =:r:...:ss:55 (RUNE transactions with 55 basis points)
            #     # =:THOR.TCY:...:ss:0 (THORChain TCY transactions with 0 basis points)
            #     if memo:
            #         memo_parts = memo.split(':')
            #         if len(memo_parts) >= 4:
            #             # Check if memo ends with :ss: pattern
            #             if memo_parts[-2] == 'ss':
            #                 basis_points = memo_parts[-1]
            #                 self.logger.info(f"🎯 Found ShapeShift affiliate transaction with :ss:{basis_points} pattern")
            #                 return True
            #
            #             # Check for specific asset patterns
            #             if memo_parts[1] in ['b', 'r'] and 'ss' in memo_parts:
            #                 self.logger.info(f"🎯 Found ShapeShift affiliate transaction with asset pattern: {memo_parts[1]}")
            #                 return True

            # # Alternative approach: Check if any field contains the :ss: pattern
            # for key, value in swap.items():
            #     if isinstance(value, str) and ':ss:' in value.lower():
            #         self.logger.info(f"🎯 Found ShapeShift affiliate transaction with :ss: in field {key}: {value}")
            #         return True

            # =============================================================================
            # END ENHANCED LOGIC
            # =============================================================================

            return False

        except Exception as e:
            self.logger.warning(f"⚠️ Error checking affiliate involvement: {e}")
            return False

    # =============================================================================
    # TRANSACTION PROCESSING & CONVERSION
    # =============================================================================

    def convert_swap_to_transaction(self, swap: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a THORChain swap to our transaction format"""
        try:
            # Extract basic swap information
            tx_hash = swap.get(
                "txID",
                "0x0000000000000000000000000000000000000000000000000000000000000000",
            )
            timestamp = swap.get("date", int(time.time()))

            # Extract in/out information
            in_data = swap.get("in", {})
            out_data = swap.get("out", {})

            # Calculate volume (use in amount as primary volume indicator)
            volume_amount = 0
            volume_token = "0x0000000000000000000000000000000000000000"
            volume_usd = 0

            if isinstance(in_data, dict):
                volume_amount = in_data.get("amount", "0")
                volume_token = (
                    in_data.get("coins", [{}])[0].get(
                        "asset", "0x0000000000000000000000000000000000000000"
                    )
                    if in_data.get("coins")
                    else "0x0000000000000000000000000000000000000000"
                )
                # Convert to USD (simplified - would need price feeds for accuracy)
                try:
                    volume_usd = float(volume_amount) / (10**8) * 50  # Rough estimate
                except (ValueError, TypeError):
                    volume_usd = 0

            # Create transaction record
            transaction = {
                "tx_hash": tx_hash,
                "chain": "thorchain",
                "block_number": swap.get("height", 0),
                "timestamp": timestamp,
                "from_address": in_data.get(
                    "address", "0x0000000000000000000000000000000000000000"
                )
                if isinstance(in_data, dict)
                else "0x0000000000000000000000000000000000000000",
                "to_address": out_data.get(
                    "address", "0x0000000000000000000000000000000000000000"
                )
                if isinstance(out_data, dict)
                else "0x0000000000000000000000000000000000000000",
                "affiliate_address": self.shapeshift_affiliate_address,
                "affiliate_fee_amount": "0",  # THORChain doesn't have explicit affiliate fees
                "affiliate_fee_token": "0x0000000000000000000000000000000000000000",
                "affiliate_fee_usd": "0",
                "volume_amount": str(volume_amount),
                "volume_token": volume_token,
                "volume_usd": str(volume_usd),
                "gas_used": 0,  # THORChain doesn't use gas
                "gas_price": 0,
                "pool": swap.get("pool", ""),
                "from_asset": in_data.get("coins", [{}])[0].get("asset", "")
                if in_data.get("coins")
                else "",
                "to_asset": out_data.get("coins", [{}])[0].get("asset", "")
                if out_data.get("coins")
                else "",
                "from_amount": str(in_data.get("amount", "0"))
                if isinstance(in_data, dict)
                else "0",
                "to_amount": str(out_data.get("amount", "0"))
                if isinstance(out_data, dict)
                else "0",
                "affiliate_fee_asset": "",
                "affiliate_fee_amount_asset": "0",
                "created_at": int(time.time()),
            }

            return transaction

        except Exception as e:
            self.logger.error(f"❌ Error converting swap to transaction: {e}")
            return {}

    # =============================================================================
    # MAIN LISTENER EXECUTION
    # =============================================================================

    def run_listener(self, max_swaps: Optional[int] = None):
        """Run the THORChain listener to fetch and process swaps"""
        if max_swaps is None:
            max_swaps = self.max_swaps_per_request

        self.logger.info(f"🚀 Starting THORChain listener")
        self.logger.info(f"📊 Max swaps per request: {max_swaps}")

        total_transactions = 0
        offset = self.get_last_processed_offset()

        try:
            # Fetch swaps from THORChain
            swaps = self.fetch_thorchain_swaps(offset=offset, limit=max_swaps)

            if not swaps:
                self.logger.info("✅ No new swaps found")
                return 0

            # Filter for ShapeShift affiliate swaps
            affiliate_swaps = self.filter_shapeshift_affiliate_swaps(swaps)

            if not affiliate_swaps:
                self.logger.info("✅ No ShapeShift affiliate swaps found")
                # Still update offset to avoid re-processing
                self.update_block_tracker(offset + len(swaps))
                return 0

            # Convert swaps to transactions
            transactions = []
            for swap in affiliate_swaps:
                try:
                    transaction = self.convert_swap_to_transaction(swap)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.logger.error(f"❌ Error converting swap: {e}")
                    continue

            # Save transactions to CSV
            if transactions:
                self.save_transactions_to_csv(transactions)
                total_transactions = len(transactions)

            # Update block tracker
            self.update_block_tracker(offset + len(swaps))

            # Rate limiting
            time.sleep(self.api_rate_limit)

            self.logger.info(
                f"🎯 THORChain listener completed. Total transactions: {total_transactions}"
            )
            return total_transactions

        except Exception as e:
            self.logger.error(f"❌ Error running THORChain listener: {e}")
            return 0

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the CSV data"""
        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )

        if not os.path.exists(transactions_path):
            return {"total_transactions": 0, "pools": {}, "volume_ranges": {}}

        try:
            with open(transactions_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            stats = {
                "total_transactions": len(rows),
                "pools": {},
                "volume_ranges": {
                    "under_13": 0,
                    "13_to_100": 0,
                    "100_to_1000": 0,
                    "over_1000": 0,
                },
            }

            for row in rows:
                pool = row.get("pool", "unknown")
                if pool not in stats["pools"]:
                    stats["pools"][pool] = 0
                stats["pools"][pool] += 1

                # Analyze volume distribution
                try:
                    volume_usd = float(row.get("volume_usd", 0))
                    if volume_usd < 13:
                        stats["volume_ranges"]["under_13"] += 1
                    elif volume_usd < 100:
                        stats["volume_ranges"]["13_to_100"] += 1
                    elif volume_usd < 1000:
                        stats["volume_ranges"]["100_to_1000"] += 1
                    else:
                        stats["volume_ranges"]["over_1000"] += 1
                except (ValueError, TypeError):
                    continue

            return stats

        except Exception as e:
            self.logger.error(f"❌ Error getting CSV stats: {e}")
            return {"total_transactions": 0, "pools": {}, "volume_ranges": {}}


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main function to run the THORChain listener"""
    try:
        listener = CSVThorChainListener()
        total_transactions = listener.run_listener()

        stats = listener.get_csv_stats()

        print(f"\n📊 THORChain Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by pool:")
        for pool, count in stats["pools"].items():
            print(f"     {pool}: {count}")
        print(f"   Volume distribution:")
        for range_name, count in stats["volume_ranges"].items():
            print(f"     {range_name}: {count} transactions")

        print(f"\n✅ THORChain listener completed successfully!")
        print(f"   Total events found: {total_transactions}")

    except Exception as e:
        logging.error(f"❌ Error running THORChain listener: {e}")
        raise


if __name__ == "__main__":
    main()
