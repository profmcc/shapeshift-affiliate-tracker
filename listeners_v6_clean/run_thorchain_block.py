#!/usr/bin/env python3
"""
Custom ThorChain Listener Runner for Specific Block
==================================================

This script runs the ThorChain listener targeting a specific block (22,456,113)
by temporarily modifying the offset logic to fetch data from that block.

Author: ShapeShift Affiliate Tracker Team
Date: 2024
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Set the correct config path
os.environ["CONFIG_PATH"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "shapeshift_config.yaml"
)

# Import the ThorChain listener
from csv_thorchain_listener import CSVThorChainListener

# =============================================================================
# CUSTOM BLOCK RUNNER
# =============================================================================


class CustomThorChainBlockRunner:
    """Custom runner to process a specific ThorChain block"""

    def __init__(self, target_block: int):
        """Initialize with target block number"""
        self.target_block = target_block
        self.listener = CSVThorChainListener()
        self.logger = logging.getLogger(__name__)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        self.logger.info(
            f"🎯 Custom ThorChain Block Runner initialized for block {target_block}"
        )

    def run_for_specific_block(self):
        """Run ThorChain listener targeting the specific block"""
        try:
            self.logger.info(
                f"🚀 Starting ThorChain listener for block {self.target_block}"
            )

            # Temporarily modify the listener's offset to target our block
            original_offset = self.listener.get_last_processed_offset()

            # Calculate offset to reach our target block
            # We'll use a small limit to focus on the target area
            target_offset = max(
                0, self.target_block - 50
            )  # Start 50 blocks before target

            self.logger.info(f"📊 Original offset: {original_offset}")
            self.logger.info(f"📊 Target offset: {target_offset}")

            # Override the offset method temporarily
            original_method = self.listener.get_last_processed_offset

            def custom_offset():
                return target_offset

            self.listener.get_last_processed_offset = custom_offset

            # Run the listener with a small limit to focus on target area
            total_transactions = self.listener.run_listener(max_swaps=50)

            # Restore original method
            self.listener.get_last_processed_offset = original_method

            self.logger.info(
                f"✅ ThorChain listener completed for block {self.target_block}"
            )
            self.logger.info(f"📊 Total transactions found: {total_transactions}")

            return total_transactions

        except Exception as e:
            self.logger.error(
                f"❌ Error running ThorChain listener for block {self.target_block}: {e}"
            )
            raise

    def get_block_stats(self):
        """Get statistics about the processed data"""
        try:
            stats = self.listener.get_csv_stats()
            return stats
        except Exception as e:
            self.logger.error(f"❌ Error getting stats: {e}")
            return {}


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main function to run ThorChain listener for specific block"""
    target_block = 22456113

    try:
        print(f"\n🎯 ThorChain Affiliate Listener - Block {target_block}")
        print("=" * 60)

        runner = CustomThorChainBlockRunner(target_block)

        # Run the listener for the specific block
        total_transactions = runner.run_for_specific_block()

        # Get and display statistics
        stats = runner.get_block_stats()

        print(f"\n📊 ThorChain Listener Results for Block {target_block}:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Total transactions in CSV: {stats.get('total_transactions', 0)}")

        if stats.get("pools"):
            print(f"   Transactions by pool:")
            for pool, count in stats["pools"].items():
                print(f"     {pool}: {count}")

        if stats.get("volume_ranges"):
            print(f"   Volume distribution:")
            for range_name, count in stats["volume_ranges"].items():
                print(f"     {range_name}: {count} transactions")

        print(
            f"\n✅ ThorChain listener completed successfully for block {target_block}!"
        )
        print(f"   Events found: {total_transactions}")

    except Exception as e:
        logging.error(f"❌ Error running ThorChain listener: {e}")
        raise


if __name__ == "__main__":
    main()
