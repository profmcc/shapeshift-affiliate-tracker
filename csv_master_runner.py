#!/usr/bin/env python3
"""
CSV Master Runner for ShapeShift Affiliate Tracker
=================================================

HISTORY & LEARNING:
- Originally had separate database-based listeners for each protocol
- Database approach led to complexity and maintenance issues
- Migrated to CSV-based storage for simplicity and easy analysis
- Previous attempts at centralized coordination failed due to config issues
# - Current approach: CSV-based listeners with centralized coordination

WHAT THIS SYSTEM IS ATTEMPTING:
- Coordinate multiple protocol listeners (ButterSwap, Relay, CoW Swap, Portals, ThorChain)
- Ensure consistent data collection across all protocols
- Provide unified interface for affiliate fee tracking
- Enable comprehensive analysis of ShapeShift's affiliate revenue

WHY CSV-BASED APPROACH:
- Simpler than database management
- Easy to analyze with standard tools (Excel, Python, R)
- No database setup or maintenance required
- Portable and human-readable format
- Better for data science and analysis workflows

CURRENT STATUS:
- CSV-based listeners implemented for all major protocols
- Centralized coordination through this master runner
- Hybrid configuration approach (centralized config + legacy hardcoded)
- No volume thresholds for comprehensive tracking

TECHNICAL APPROACH:
- Sequential execution of protocol listeners
- CSV file management and consolidation
- Progress tracking and error handling
- Comprehensive reporting and statistics
"""

import os
import sys
import time
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Add the project root to the path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import protocol listeners
from affiliate_listeners_csv.csv_butterswap_listener import CSVButterSwapListener
from affiliate_listeners_csv.csv_relay_listener import CSVRelayListener
from affiliate_listeners_csv.csv_cowswap_listener import CSVCowSwapListener
from affiliate_listeners_csv.csv_portals_listener import CSVPortalsListener
from affiliate_listeners_csv.csv_thorchain_listener import CSVThorChainListener

# Import shared utilities
from shared.config_loader import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/master_runner.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CSVMasterRunner:
    """
    Master coordinator for all CSV-based affiliate listeners

    This class orchestrates the execution of multiple protocol listeners
    to provide comprehensive affiliate fee tracking across all supported
    protocols and chains. It uses a CSV-based approach for simplicity
    and easy analysis.

    COORDINATION STRATEGY:
    - Sequential execution to avoid overwhelming RPC providers
    - Centralized configuration management
    - Unified error handling and reporting
    - Progress tracking across all protocols

    PROTOCOL SUPPORT:
    - ButterSwap: DEX aggregator with affiliate fees
    - Relay: Cross-chain aggregation protocol
    - CoW Swap: MEV-protected DEX
    - Portals: Cross-chain bridge protocol
    - ThorChain: Cross-chain liquidity protocol
    """

    def __init__(self):
        """
        Initialize the master runner

        INITIALIZATION APPROACH:
        - Load centralized configuration
        - Initialize all protocol listeners
        - Set up logging and error handling
        - Prepare data consolidation structures

        This approach ensures all listeners are properly configured
        and ready for coordinated execution.
        """
        # Load centralized configuration
        try:
            self.config = get_config()
            logger.info("✅ Centralized configuration loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load centralized config: {e}")
            logger.info("💡 Falling back to default configuration")
            self.config = None

        # Initialize protocol listeners
        self.listeners = {}
        self._init_listeners()

        # Data consolidation settings
        self.consolidated_file = "csv_data/consolidated_affiliate_transactions.csv"
        self._init_consolidated_file()

        # Execution tracking
        self.execution_history = []
        self.start_time = None

        logger.info("🚀 CSV Master Runner initialized successfully")
        logger.info(f"📊 Managing {len(self.listeners)} protocol listeners")

    def _init_listeners(self):
        """
        Initialize all protocol listeners

        LISTENER INITIALIZATION STRATEGY:
        - Create listener instances for each supported protocol
        - Handle initialization failures gracefully
        - Log successful initializations for monitoring
        - Support both centralized config and legacy approaches

        This method ensures all listeners are ready for execution
        while providing fallback options for failed initializations.
        """
        listener_classes = {
            "butterswap": CSVButterSwapListener,
            "relay": CSVRelayListener,
            "cowswap": CSVCowSwapListener,
            "portals": CSVPortalsListener,
            "thorchain": CSVThorChainListener,
        }

        for protocol, listener_class in listener_classes.items():
            try:
                # Initialize listener
                listener = listener_class()
                self.listeners[protocol] = listener
                logger.info(
                    f"✅ {protocol.capitalize()} listener initialized successfully"
                )

            except Exception as e:
                logger.error(f"❌ Failed to initialize {protocol} listener: {e}")
                logger.info(
                    f"💡 {protocol.capitalize()} will be skipped during execution"
                )

        if not self.listeners:
            raise Exception("No listeners could be initialized")

    def _init_consolidated_file(self):
        """
        Initialize consolidated CSV file for combined data

        CONSOLIDATED DATA STRUCTURE:
        - timestamp: When the transaction was processed
        - protocol: Which protocol generated the transaction
        - chain_id: Which blockchain the transaction occurred on
        - block_number: Block number containing the transaction
        - transaction_hash: Unique identifier for the transaction
        - user_address: Address of the user making the transaction
        - token_in: Token being swapped/bridged in
        - token_out: Token being swapped/bridged out
        - amount_in: Amount of input token
        - amount_out: Amount of output token
        - affiliate_fee: Affiliate fee received by ShapeShift
        - volume_usd: Total transaction volume in USD
        - affiliate_fee_usd: Affiliate fee in USD

        This structure allows for comprehensive analysis across
        all protocols and chains in a single dataset.
        """
        if not os.path.exists(self.consolidated_file):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.consolidated_file), exist_ok=True)

            # Define consolidated CSV headers
            headers = [
                "timestamp",
                "protocol",
                "chain_id",
                "block_number",
                "transaction_hash",
                "user_address",
                "token_in",
                "token_out",
                "amount_in",
                "amount_out",
                "affiliate_fee",
                "volume_usd",
                "affiliate_fee_usd",
            ]

            # Write headers to consolidated CSV
            with open(self.consolidated_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"📁 Created consolidated CSV file: {self.consolidated_file}")

    def run_all_listeners(
        self, start_block: Optional[int] = None, max_blocks: Optional[int] = None
    ):
        """
        Execute all protocol listeners sequentially

        EXECUTION STRATEGY:
        - Run listeners one at a time to avoid overwhelming RPC providers
        - Use consistent parameters across all listeners
        - Handle failures gracefully and continue with remaining listeners
        - Track execution progress and timing

        PARAMETERS:
        - start_block: Starting block number for all listeners
        - max_blocks: Maximum blocks to scan per listener

        This method provides the main interface for coordinated
        affiliate fee tracking across all protocols.
        """
        self.start_time = datetime.now()
        logger.info("🚀 Starting coordinated execution of all listeners")
        logger.info(f"⏰ Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Execution order (can be customized based on priority)
        execution_order = ["butterswap", "relay", "cowswap", "portals", "thorchain"]

        total_transactions = 0
        successful_listeners = 0

        for protocol in execution_order:
            if protocol not in self.listeners:
                logger.warning(f"⚠️  Skipping {protocol} - listener not available")
                continue

            try:
                logger.info(f"\n🔍 Executing {protocol.capitalize()} listener...")

                # Execute listener
                listener = self.listeners[protocol]
                transactions = self._execute_listener(
                    listener, protocol, start_block, max_blocks
                )

                if transactions is not None:
                    total_transactions += transactions
                    successful_listeners += 1
                    logger.info(
                        f"✅ {protocol.capitalize()} completed successfully: {transactions} transactions"
                    )
                else:
                    logger.warning(f"⚠️  {protocol.capitalize()} execution failed")

                # Rate limiting between listeners
                time.sleep(2)  # 2 second delay between protocols

            except Exception as e:
                logger.error(f"❌ Error executing {protocol} listener: {e}")
                continue

        # Consolidate data from all listeners
        self._consolidate_data()

        # Generate execution report
        self._generate_execution_report(total_transactions, successful_listeners)

        logger.info(f"\n🎉 Master runner execution completed!")
        logger.info(f"📊 Total transactions processed: {total_transactions}")
        logger.info(
            f"✅ Successful listeners: {successful_listeners}/{len(execution_order)}"
        )

    def _execute_listener(
        self,
        listener,
        protocol: str,
        start_block: Optional[int],
        max_blocks: Optional[int],
    ) -> Optional[int]:
        """
        Execute a single protocol listener

        LISTENER EXECUTION:
        - Call appropriate scanning method based on listener type
        - Handle different listener interfaces consistently
        - Track execution time and performance
        - Return transaction count for reporting

        This method provides a unified interface for executing
        different types of protocol listeners.
        """
        start_time = time.time()

        try:
            # Execute based on listener type
            if hasattr(listener, "scan_all_chains"):
                # Multi-chain listeners
                listener.scan_all_chains(start_block)
                transactions = self._count_transactions(protocol)

            elif hasattr(listener, "scan_chain"):
                # Single-chain listeners
                # Default to Base chain (chain ID 8453) for most protocols
                listener.scan_chain(8453, start_block, max_blocks)
                transactions = self._count_transactions(protocol)

            else:
                logger.warning(f"⚠️  Unknown listener interface for {protocol}")
                return None

            execution_time = time.time() - start_time
            logger.info(
                f"⏱️  {protocol.capitalize()} execution time: {execution_time:.2f} seconds"
            )

            return transactions

        except Exception as e:
            logger.error(f"❌ Error executing {protocol} listener: {e}")
            return None

    def _count_transactions(self, protocol: str) -> int:
        """
        Count transactions in a protocol's CSV file

        TRANSACTION COUNTING:
        - Read protocol-specific CSV file
        - Count non-header rows
        - Handle missing files gracefully
        - Provide accurate transaction counts

        This method gives us visibility into how many transactions
        each listener has processed.
        """
        csv_file = f"csv_data/{protocol}_transactions.csv"

        if not os.path.exists(csv_file):
            return 0

        try:
            with open(csv_file, "r") as f:
                reader = csv.reader(f)
                # Subtract 1 for header row
                return max(0, sum(1 for row in reader) - 1)

        except Exception as e:
            logger.error(f"❌ Error counting transactions for {protocol}: {e}")
            return 0

    def _consolidate_data(self):
        """
        Consolidate data from all protocol listeners

        DATA CONSOLIDATION STRATEGY:
        - Read all protocol CSV files
        - Add protocol identifier to each row
        - Combine into single consolidated file
        - Remove duplicates and ensure data quality

        This method creates a unified dataset that can be used
        for comprehensive affiliate revenue analysis.
        """
        logger.info("🔗 Consolidating data from all listeners...")

        # Clear existing consolidated file (keep headers)
        with open(self.consolidated_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "protocol",
                    "chain_id",
                    "block_number",
                    "transaction_hash",
                    "user_address",
                    "token_in",
                    "token_out",
                    "amount_in",
                    "amount_out",
                    "affiliate_fee",
                    "volume_usd",
                    "affiliate_fee_usd",
                ]
            )

        total_consolidated = 0

        for protocol in self.listeners.keys():
            csv_file = f"csv_data/{protocol}_transactions.csv"

            if not os.path.exists(csv_file):
                continue

            try:
                with open(csv_file, "r") as f:
                    reader = csv.DictReader(f)

                    # Read and consolidate data
                    for row in reader:
                        # Add protocol identifier
                        consolidated_row = {
                            "timestamp": row.get("timestamp", ""),
                            "protocol": protocol,
                            "chain_id": row.get("chain_id", ""),
                            "block_number": row.get("block_number", ""),
                            "transaction_hash": row.get("transaction_hash", ""),
                            "user_address": row.get("user_address", ""),
                            "token_in": row.get("token_in", ""),
                            "token_out": row.get("token_out", ""),
                            "amount_in": row.get("amount_in", ""),
                            "amount_out": row.get("amount_out", ""),
                            "affiliate_fee": row.get("affiliate_fee", ""),
                            "volume_usd": row.get("volume_usd", ""),
                            "affiliate_fee_usd": row.get("affiliate_fee_usd", ""),
                        }

                        # Write to consolidated file
                        with open(self.consolidated_file, "a", newline="") as f:
                            writer = csv.DictWriter(
                                f, fieldnames=consolidated_row.keys()
                            )
                            writer.writerow(consolidated_row)

                        total_consolidated += 1

                logger.info(
                    f"📊 Consolidated {protocol}: {self._count_transactions(protocol)} transactions"
                )

            except Exception as e:
                logger.error(f"❌ Error consolidating {protocol} data: {e}")
                continue

        logger.info(
            f"✅ Data consolidation completed: {total_consolidated} total transactions"
        )

    def _generate_execution_report(
        self, total_transactions: int, successful_listeners: int
    ):
        """
        Generate comprehensive execution report

        REPORT CONTENTS:
        - Execution summary and timing
        - Transaction counts by protocol
        - Error summary and recommendations
        - Performance metrics and insights

        This method provides a comprehensive overview of the
        master runner's execution and results.
        """
        if not self.start_time:
            return

        end_time = datetime.now()
        execution_duration = end_time - self.start_time

        # Generate report
        report = {
            "execution_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": execution_duration.total_seconds(),
                "total_transactions": total_transactions,
                "successful_listeners": successful_listeners,
                "total_listeners": len(self.listeners),
            },
            "protocol_summary": {},
            "consolidated_data": {
                "file_path": self.consolidated_file,
                "total_transactions": self._count_consolidated_transactions(),
            },
        }

        # Add protocol-specific summaries
        for protocol in self.listeners.keys():
            csv_file = f"csv_data/{protocol}_transactions.csv"
            if os.path.exists(csv_file):
                report["protocol_summary"][protocol] = {
                    "transactions": self._count_transactions(protocol),
                    "file_path": csv_file,
                }

        # Save report to file
        report_file = f"reports/master_runner_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary to console
        print("\n" + "=" * 60)
        print("📊 MASTER RUNNER EXECUTION REPORT")
        print("=" * 60)
        print(f"⏰ Execution Time: {execution_duration}")
        print(f"📊 Total Transactions: {total_transactions:,}")
        print(f"✅ Successful Listeners: {successful_listeners}/{len(self.listeners)}")
        print(
            f"🔗 Consolidated Data: {report['consolidated_data']['total_transactions']:,} transactions"
        )
        print(f"📁 Report Saved: {report_file}")
        print("=" * 60)

        logger.info(f"📋 Execution report generated: {report_file}")

    def _count_consolidated_transactions(self) -> int:
        """Count transactions in consolidated CSV file"""
        if not os.path.exists(self.consolidated_file):
            return 0

        try:
            with open(self.consolidated_file, "r") as f:
                reader = csv.reader(f)
                return max(0, sum(1 for row in reader) - 1)  # Subtract header
        except Exception:
            return 0

    def get_status(self) -> Dict:
        """
        Get current status of all listeners

        STATUS INFORMATION:
        - Listener availability and health
        - Transaction counts by protocol
        - File sizes and data freshness
        - Configuration status

        This method provides real-time visibility into the
        master runner's current state.
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "listeners": {},
            "data_summary": {},
            "configuration": "centralized" if self.config else "legacy",
        }

        # Listener status
        for protocol, listener in self.listeners.items():
            status["listeners"][protocol] = {
                "available": True,
                "class": type(listener).__name__,
                "transactions": self._count_transactions(protocol),
            }

        # Data summary
        csv_dir = "csv_data"
        if os.path.exists(csv_dir):
            total_files = 0
            total_size = 0

            for file in os.listdir(csv_dir):
                if file.endswith(".csv"):
                    file_path = os.path.join(csv_dir, file)
                    total_files += 1
                    total_size += os.path.getsize(file_path)

            status["data_summary"] = {
                "total_csv_files": total_files,
                "total_size_bytes": total_size,
                "consolidated_transactions": self._count_consolidated_transactions(),
            }

        return status


def main():
    """
    Main execution function

    USAGE:
    - Run directly: python csv_master_runner.py
    - Import as module: from csv_master_runner import CSVMasterRunner

    COMMAND LINE OPTIONS:
    - --start-block: Starting block number for all listeners
    - --max-blocks: Maximum blocks to scan per listener
    - --status: Show current status without executing

    This function provides the command-line interface for the
    master runner and demonstrates its usage.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV Master Runner for ShapeShift Affiliate Tracker"
    )
    parser.add_argument(
        "--start-block", type=int, help="Starting block number for all listeners"
    )
    parser.add_argument(
        "--max-blocks", type=int, help="Maximum blocks to scan per listener"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show current status without executing"
    )

    args = parser.parse_args()

    try:
        # Initialize master runner
        runner = CSVMasterRunner()

        if args.status:
            # Show status
            status = runner.get_status()
            print("📊 CSV Master Runner Status")
            print("=" * 40)
            print(f"Configuration: {status['configuration']}")
            print(f"Listeners: {len(status['listeners'])} available")
            print(
                f"Total CSV Files: {status['data_summary'].get('total_csv_files', 0)}"
            )
            print(
                f"Consolidated Transactions: {status['data_summary'].get('consolidated_transactions', 0):,}"
            )

            print("\nListener Details:")
            for protocol, info in status["listeners"].items():
                print(
                    f"  {protocol.capitalize()}: {info['transactions']:,} transactions"
                )

        else:
            # Execute all listeners
            runner.run_all_listeners(args.start_block, args.max_blocks)

    except KeyboardInterrupt:
        print("\n⏹️  Execution interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Master runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
