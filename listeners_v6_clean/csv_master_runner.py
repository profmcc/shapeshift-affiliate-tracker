#!/usr/bin/env python3
"""
CSV Master Runner - Centralized Configuration Version
====================================================

This is the main orchestrator for all ShapeShift affiliate fee listeners.
It uses the centralized configuration system and saves all data to CSV files.

Key Features:
- Centralized configuration management
- CSV-based data storage (no databases)
- Multi-protocol support (CoW Swap, THORChain, Portals, Relay)
- Block tracking and incremental processing
- Comprehensive logging and error handling

Author: ShapeShift Affiliate Tracker Team
Version: v6.0 - Clean Centralized CSV
Date: 2024
"""

import os
import sys
import time
import logging
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Import centralized configuration
from config_loader import (
    get_config,
    get_storage_path,
    get_listener_config,
    get_threshold,
)

# Import all CSV listeners
from csv_cowswap_listener import CSVCowSwapListener
from csv_thorchain_listener import CSVThorChainListener
from csv_portals_listener import CSVPortalsListener
from csv_relay_listener import CSVRelayListener

# =============================================================================
# CONFIGURATION & SETUP
# =============================================================================


def setup_logging():
    """Setup comprehensive logging for the master runner"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File handler for detailed logs
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "master_runner.log"), encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Root logger configuration
    logging.basicConfig(
        level=logging.DEBUG, handlers=[file_handler, console_handler], format=log_format
    )

    return logging.getLogger(__name__)


def load_centralized_config():
    """Load and validate centralized configuration"""
    try:
        config = get_config()
        logger = logging.getLogger(__name__)

        # Validate essential configuration
        alchemy_key = config.get_alchemy_api_key()
        if not alchemy_key:
            raise ValueError("ALCHEMY_API_KEY not found in configuration")

        csv_dir = config.get_storage_path("csv_directory")
        if not csv_dir:
            raise ValueError("CSV directory path not found in configuration")

        logger.info("✅ Centralized configuration loaded successfully")
        logger.info(f"📁 CSV Directory: {csv_dir}")
        logger.info(f"🔑 Alchemy API Key: {'✅ Set' if alchemy_key else '❌ Not set'}")

        return config

    except Exception as e:
        logging.error(f"❌ Failed to load centralized configuration: {e}")
        raise


# =============================================================================
# CSV MANAGEMENT & UTILITIES
# =============================================================================


def ensure_csv_directory_structure(config):
    """Ensure all necessary CSV directories and files exist"""
    csv_dir = config.get_storage_path("csv_directory")
    os.makedirs(csv_dir, exist_ok=True)

    # Create subdirectories for different data types
    subdirs = ["transactions", "block_tracking", "consolidated", "reports"]
    for subdir in subdirs:
        os.makedirs(os.path.join(csv_dir, subdir), exist_ok=True)

    # Initialize consolidated transactions CSV
    consolidated_path = os.path.join(csv_dir, "consolidated", "all_transactions.csv")
    if not os.path.exists(consolidated_path):
        headers = [
            "protocol",
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
            "created_at",
        ]
        with open(consolidated_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    logging.info(f"✅ CSV directory structure initialized: {csv_dir}")
    return csv_dir


def get_csv_stats(csv_dir: str) -> Dict[str, Any]:
    """Get comprehensive statistics about all CSV data"""
    stats = {
        "total_transactions": 0,
        "protocols": {},
        "chains": {},
        "affiliate_addresses": {},
        "volume_ranges": {
            "under_13": 0,
            "13_to_100": 0,
            "100_to_1000": 0,
            "over_1000": 0,
        },
    }

    try:
        # Scan all CSV files in the transactions directory
        transactions_dir = os.path.join(csv_dir, "transactions")
        if os.path.exists(transactions_dir):
            for filename in os.listdir(transactions_dir):
                if filename.endswith(".csv"):
                    filepath = os.path.join(transactions_dir, filename)
                    protocol = filename.replace("_transactions.csv", "")

                    try:
                        with open(filepath, "r", newline="", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)

                            if rows:
                                stats["protocols"][protocol] = len(rows)
                                stats["total_transactions"] += len(rows)

                                # Analyze volume distribution
                                for row in rows:
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

                    except Exception as e:
                        logging.warning(f"⚠️ Error reading {filename}: {e}")
                        continue

    except Exception as e:
        logging.error(f"❌ Error getting CSV stats: {e}")

    return stats


# =============================================================================
# LISTENER MANAGEMENT
# =============================================================================


class ListenerManager:
    """Manages all CSV-based listeners with centralized configuration"""

    def __init__(self, config):
        """Initialize the listener manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.listeners = {}
        self.csv_dir = config.get_storage_path("csv_directory")

        # Initialize all listeners
        self._initialize_listeners()

    def _initialize_listeners(self):
        """Initialize all CSV-based listeners"""
        try:
            # Initialize CoW Swap listener
            self.listeners["cowswap"] = CSVCowSwapListener()
            self.logger.info("✅ CoW Swap listener initialized")

            # Initialize THORChain listener
            self.listeners["thorchain"] = CSVThorChainListener()
            self.logger.info("✅ THORChain listener initialized")

            # Initialize Portals listener
            self.listeners["portals"] = CSVPortalsListener()
            self.logger.info("✅ Portals listener initialized")

            # Initialize Relay listener
            self.listeners["relay"] = CSVRelayListener()
            self.logger.info("✅ Relay listener initialized")

            self.logger.info(
                f"✅ All {len(self.listeners)} listeners initialized successfully"
            )

        except Exception as e:
            self.logger.error(f"❌ Error initializing listeners: {e}")
            raise

    def run_all_listeners(self, max_blocks: Optional[int] = None):
        """Run all listeners with specified block limits"""
        results = {}
        total_events = 0

        self.logger.info("🚀 Starting all listeners...")

        for protocol, listener in self.listeners.items():
            try:
                self.logger.info(f"📡 Running {protocol} listener...")
                start_time = time.time()

                # Run listener with optional block limit
                if max_blocks:
                    events = listener.run_listener(max_blocks=max_blocks)
                else:
                    events = listener.run_listener()

                elapsed = time.time() - start_time
                results[protocol] = {
                    "events_found": events,
                    "execution_time": elapsed,
                    "status": "success",
                }
                total_events += events

                self.logger.info(f"✅ {protocol}: {events} events in {elapsed:.2f}s")

            except Exception as e:
                self.logger.error(f"❌ {protocol} listener failed: {e}")
                results[protocol] = {
                    "events_found": 0,
                    "execution_time": 0,
                    "status": "failed",
                    "error": str(e),
                }

        self.logger.info(f"🎯 All listeners completed. Total events: {total_events}")
        return results, total_events

    def consolidate_all_data(self):
        """Consolidate all protocol data into a single CSV"""
        try:
            consolidated_path = os.path.join(
                self.csv_dir, "consolidated", "all_transactions.csv"
            )
            transactions_dir = os.path.join(self.csv_dir, "transactions")

            all_transactions = []

            # Read all protocol CSV files
            for protocol in self.listeners.keys():
                protocol_file = os.path.join(
                    transactions_dir, f"{protocol}_transactions.csv"
                )
                if os.path.exists(protocol_file):
                    try:
                        with open(
                            protocol_file, "r", newline="", encoding="utf-8"
                        ) as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                row["protocol"] = protocol
                                all_transactions.append(row)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error reading {protocol_file}: {e}")
                        continue

            # Write consolidated data
            if all_transactions:
                headers = all_transactions[0].keys()
                with open(consolidated_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(all_transactions)

                self.logger.info(f"✅ Consolidated {len(all_transactions)} transactions")
                return len(all_transactions)
            else:
                self.logger.warning("⚠️ No transactions to consolidate")
                return 0

        except Exception as e:
            self.logger.error(f"❌ Error consolidating data: {e}")
            return 0


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main execution function for the CSV master runner"""
    print("🚀 CSV Master Runner - Centralized Configuration v6.0")
    print("=" * 60)

    try:
        # Setup logging
        logger = setup_logging()
        logger.info("🚀 Starting CSV Master Runner")

        # Load centralized configuration
        config = load_centralized_config()

        # Ensure CSV directory structure
        csv_dir = ensure_csv_directory_structure(config)

        # Initialize listener manager
        manager = ListenerManager(config)

        # Get initial stats
        initial_stats = get_csv_stats(csv_dir)
        print(f"\n📊 Initial Data Status:")
        print(f"   Total transactions: {initial_stats['total_transactions']}")
        print(f"   Protocols with data: {len(initial_stats['protocols'])}")

        # Run all listeners
        print(f"\n📡 Running all listeners...")
        results, total_events = manager.run_all_listeners()

        # Consolidate data
        print(f"\n🔗 Consolidating data...")
        consolidated_count = manager.consolidate_all_data()

        # Get final stats
        final_stats = get_csv_stats(csv_dir)

        # Print results
        print(f"\n📊 Final Results:")
        print(f"   New events found: {total_events}")
        print(f"   Total transactions: {final_stats['total_transactions']}")
        print(f"   Consolidated: {consolidated_count}")

        print(f"\n📋 Protocol Results:")
        for protocol, result in results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"   {status_icon} {protocol}: {result['events_found']} events")

        print(f"\n💰 Volume Distribution:")
        for range_name, count in final_stats["volume_ranges"].items():
            print(f"   {range_name}: {count} transactions")

        print(f"\n🎉 CSV Master Runner completed successfully!")

    except Exception as e:
        logging.error(f"❌ Master runner failed: {e}")
        print(f"❌ Master runner failed: {e}")
        raise


if __name__ == "__main__":
    main()
