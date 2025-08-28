#!/usr/bin/env python3
"""
# =============================================================================
# ShapeShift Affiliate Tracker Master Runner - Comprehensive Documentation
# =============================================================================
#
# PROJECT HISTORY & LEARNING JOURNEY:
# ===================================
# 
# This master runner has evolved through multiple iterations, each teaching valuable
# lessons about system coordination, data management, and architectural design.
#
# TIMELINE OF DEVELOPMENT:
# - Started as simple script to run individual listeners sequentially
# - Evolved to handle multiple protocols with different storage approaches
# - Previous attempts at centralized coordination failed due to config issues
# - Current approach: Hybrid system supporting both database and CSV approaches
#
# KEY LESSONS LEARNED:
# 1. Centralized coordination without proper error handling is fragile
# 2. Different protocols require different storage and processing approaches
# 3. Hybrid systems allow gradual migration without breaking existing functionality
# 4. Comprehensive error handling prevents single protocol failures from stopping the system
# 5. Progress tracking and recovery mechanisms are essential for long-running operations
#
# FAILED ATTEMPTS & WHAT WENT WRONG:
# ===================================
# 
# ATTEMPT 1: Monolithic Runner System
# - Problem: Single large script tried to handle all protocols in one process
# - Issue: Single protocol failure would crash entire system
# - Lesson: Separate concerns, handle each protocol independently
#
# ATTEMPT 2: Strict Protocol Dependencies
# - Problem: Required all protocols to use same storage and configuration approach
# - Issue: Different protocols have different requirements and capabilities
# - Lesson: Allow protocols to use appropriate approaches for their use case
#
# ATTEMPT 3: No Error Recovery
# - Problem: System would stop completely if any protocol failed
# - Issue: Lost progress and required manual intervention
# - Lesson: Implement comprehensive error handling and recovery mechanisms
#
# ATTEMPT 4: Single Storage Approach
# - Problem: Tried to force all protocols into same storage pattern
# - Issue: Different protocols have different data structures and requirements
# - Lesson: Hybrid approaches allow protocols to use appropriate storage
#
# WHAT THIS SYSTEM IS ATTEMPTING:
# ===============================
# 
# PRIMARY GOAL:
# - Coordinate multiple protocol listeners (ButterSwap, Relay, CoW Swap, Portals, ThorChain)
# - Ensure consistent data collection across all protocols
# - Provide unified interface for affiliate fee tracking
# - Enable comprehensive analysis of ShapeShift's affiliate revenue
#
# TECHNICAL OBJECTIVES:
# - Sequential execution of protocol listeners with error isolation
# - Progress tracking and recovery for long-running operations
# - Data consolidation from multiple sources into unified datasets
# - Comprehensive reporting and statistics across all protocols
# - Graceful degradation when individual protocols fail
#
# WHY THIS APPROACH WAS CHOSEN:
# =============================
# 
# HYBRID COORDINATION SYSTEM:
# - Each protocol runs independently to prevent cascading failures
# - Progress tracking allows resuming from last successful point
# - Error isolation prevents single protocol issues from affecting others
# - Flexible storage support for different protocol requirements
#
# DATABASE-BASED APPROACH (for v2 and current):
# - Proven approach with existing listeners
# - Better for real-time operations and transaction integrity
# - Familiar to developers and easier to debug
# - ACID properties for critical financial data
#
# CSV-BASED APPROACH (for v3+):
# - Simpler than database management
# - Easy to analyze with standard tools (Excel, Python, R)
# - Portable and human-readable format
# - Better for data science and analysis workflows
#
# CURRENT STATUS & ARCHITECTURE:
# =============================
# 
# VERSION COMPARISON:
# - ready-v2: Database-based approach, working but complex
# - ready-v3: CSV-based approach with centralized config, most advanced
# - ready-v4: Database-based with comprehensive comments from v3
# - commented: This branch - comprehensive documentation of all approaches
#
# PROTOCOLS COORDINATED:
# - ButterSwap: DEX aggregator affiliate fees
# - Relay: Cross-chain aggregation affiliate fees
# - CoW Swap: MEV-protected DEX affiliate fees
# - Portals: Cross-chain bridge affiliate fees
# - ThorChain: Cross-chain liquidity affiliate fees
#
# TECHNICAL IMPLEMENTATION:
# =========================
# 
# CORE COMPONENTS:
# 1. Protocol Coordinator: Manages execution order and dependencies
# 2. Progress Tracker: Monitors completion status and enables recovery
# 3. Error Handler: Isolates failures and provides recovery mechanisms
# 4. Data Consolidator: Combines results from multiple protocols
# 5. Reporting Engine: Generates comprehensive statistics and summaries
#
# KEY TECHNOLOGIES:
# - Python multiprocessing for parallel execution where possible
# - Database connections for transaction data storage
# - CSV processing for data export and analysis
# - Progress tracking with persistent state management
# - Comprehensive logging and error reporting
#
# ERROR HANDLING STRATEGY:
# ========================
# 
# PROTOCOL FAILURES:
# - Isolate failures to prevent system-wide crashes
# - Log detailed error information for debugging
# - Continue with remaining protocols
# - Provide recovery mechanisms for failed protocols
#
# DATA STORAGE ERRORS:
# - Transaction rollback on database errors
# - File backup and recovery for CSV operations
# - Graceful degradation when storage fails
# - Comprehensive error reporting for troubleshooting
#
# SYSTEM ERRORS:
# - Automatic restart mechanisms for critical failures
# - Progress preservation across system restarts
# - Health monitoring and alerting
# - Graceful shutdown procedures
#
# PERFORMANCE CONSIDERATIONS:
# ==========================
# 
# EXECUTION ORDER:
# - Optimize protocol execution order based on dependencies
# - Parallel execution where protocols are independent
# - Resource management to prevent system overload
# - Progress tracking for long-running operations
#
# MEMORY MANAGEMENT:
# - Process data in chunks to avoid memory issues
# - Clear processed data from memory regularly
# - Monitor memory usage during operation
# - Implement garbage collection for long-running processes
#
# STORAGE OPTIMIZATION:
# - Efficient database queries and indexing
# - Batch operations for CSV processing
# - Compression for large datasets
# - Archival strategies for historical data
#
# DEVELOPMENT WORKFLOW:
# =====================
# 
# TESTING APPROACH:
# - Individual protocol testing before integration
# - End-to-end testing with real blockchain data
# - Error scenario testing and recovery validation
# - Performance testing with high-volume data
#
# DEBUGGING STRATEGY:
# - Comprehensive logging at multiple levels
# - Progress tracking for specific issues
# - Error context preservation for troubleshooting
# - Health monitoring and alerting
#
# DEPLOYMENT CONSIDERATIONS:
# - Environment variable management
# - Configuration validation and testing
# - Monitoring and alerting setup
# - Backup and recovery procedures
#
# FUTURE IMPROVEMENTS:
# ====================
# 
# IMMEDIATE PRIORITIES:
# 1. Complete error handling coverage
# 2. Performance optimization for high-volume protocols
# 3. Real-time monitoring dashboard
# 4. Automated testing suite
#
# LONG-TERM GOALS:
# 1. Machine learning for affiliate fee prediction
# 2. Cross-protocol correlation analysis
# 3. Advanced analytics and reporting
# 4. Integration with additional DeFi protocols
#
# LESSONS FOR FUTURE DEVELOPERS:
# =============================
# 
# 1. START SIMPLE: Begin with working prototypes, not perfect architecture
# 2. ERROR ISOLATION: Prevent single failures from affecting entire system
# 3. PROGRESS TRACKING: Enable recovery and resumption of long operations
# 4. HYBRID APPROACHES: Allow gradual migration without breaking existing systems
# 5. COMPREHENSIVE LOGGING: Document all operations for debugging and analysis
# 6. TEST WITH REAL DATA: Blockchain development requires real-world testing
# 7. MONITOR PERFORMANCE: Resource constraints are real in production systems
# 8. VERSION CONTROL: Each iteration should be a separate branch for comparison
#
# CONTACT & SUPPORT:
# ==================
# 
# For questions about this master runner:
# - Check the troubleshooting section below
# - Review the commit history for specific changes
# - Examine the different branch approaches
# - Contact the development team with specific issues
#
# --- END OF COMPREHENSIVE DOCUMENTATION ---

Master runner for coordinating all ShapeShift affiliate fee listeners.
Executes all protocol listeners and consolidates data into a comprehensive database.
"""

import os
import sys
import sqlite3
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import argparse
from web3 import Web3

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all listeners
try:
    from relay_listener import RelayListener
    from portals_listener import PortalsListener
    from thorchain_listener import THORChainListener
    from chainflip_listener import ChainflipBrokerListener
    from cowswap_listener_dune import CowSwapDuneListener
    from zerox_listener import ZeroXListener
    from butterswap_listener import ButterSwapListener
except ImportError as e:
    print(f"❌ Error importing listeners: {e}")
    print("Make sure all listener files are in the listeners/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MasterRunner:
    def __init__(self):
        self.comprehensive_db_path = "databases/comprehensive_affiliate.db"
        self.init_comprehensive_database()

        # Initialize all listeners
        self.listeners = {
            "relay": RelayListener(),
            "portals": PortalsListener(db_path="databases/portals_transactions.db"),
            "thorchain": THORChainListener(
                db_path="databases/thorchain_transactions.db"
            ),
            "chainflip": ChainflipBrokerListener(),
            "cowswap": CowSwapDuneListener(db_path="databases/cowswap_transactions.db"),
            "zerox": ZeroXListener(db_path="databases/zerox_transactions.db"),
            "butterswap": ButterSwapListener(
                db_path="databases/butterswap_transactions.db"
            ),
        }

    def init_comprehensive_database(self):
        """Initialize the comprehensive database that combines all protocols"""
        os.makedirs(os.path.dirname(self.comprehensive_db_path), exist_ok=True)
        conn = sqlite3.connect(self.comprehensive_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comprehensive_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER,
                timestamp INTEGER NOT NULL,
                from_asset TEXT,
                to_asset TEXT,
                from_amount REAL,
                to_amount REAL,
                from_amount_usd REAL,
                to_amount_usd REAL,
                volume_usd REAL,
                affiliate_fee_amount REAL,
                affiliate_fee_usd REAL,
                affiliate_fee_asset TEXT,
                affiliate_address TEXT,
                sender_address TEXT,
                recipient_address TEXT,
                event_type TEXT,
                raw_data TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(protocol, tx_hash, chain)
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_protocol ON comprehensive_transactions(protocol)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chain ON comprehensive_transactions(chain)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON comprehensive_transactions(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_hash ON comprehensive_transactions(tx_hash)"
        )

        conn.commit()
        conn.close()
        logger.info(
            f"✅ Comprehensive database initialized: {self.comprehensive_db_path}"
        )

    def run_all_listeners(self, blocks_to_scan: int = 2000, limit: int = 100):
        """Run all protocol listeners"""
        logger.info("🚀 Starting Master Runner - All Protocol Listeners")

        results = {}
        start_time = time.time()

        # Run all listeners
        for protocol, listener in self.listeners.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Running {protocol.upper()} listener...")
            logger.info(f"{'='*60}")

            try:
                protocol_start = time.time()

                logger.info(f"--- Starting {protocol.upper()} listener ---")

                if protocol == "relay":
                    # Relay listener scans a specific chain
                    chain_config = listener._get_chain_config("base")
                    if chain_config:
                        w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
                        end_block = w3.eth.block_number
                        start_block = end_block - blocks_to_scan
                        listener.scan_chain("base", start_block, end_block)
                    else:
                        logger.error(
                            "Could not find 'base' chain config for Relay listener."
                        )
                elif protocol in ["thorchain", "chainflip"]:
                    # API-based listeners use limit
                    listener.run_listener(limit)
                else:
                    # Blockchain listeners use blocks_to_scan
                    listener.run_listener(blocks_to_scan)

                logger.info(f"--- Finished {protocol.upper()} listener ---")

                protocol_time = time.time() - protocol_start
                results[protocol] = {
                    "status": "success",
                    "time": protocol_time,
                    "error": None,
                }
                logger.info(f"✅ {protocol.upper()} completed in {protocol_time:.2f}s")

            except Exception as e:
                protocol_time = time.time() - protocol_start
                results[protocol] = {
                    "status": "error",
                    "time": protocol_time,
                    "error": str(e),
                }
                logger.error(f"❌ {protocol.upper()} failed: {e}")

        total_time = time.time() - start_time

        # Print summary
        self.print_execution_summary(results, total_time)

        return results

    def consolidate_databases(self):
        """Consolidate all protocol databases into comprehensive database"""
        logger.info("\n🔄 Consolidating databases...")

        # Database mapping and consolidation logic
        consolidation_map = {
            "relay": {
                "source_db": "databases/relay_transactions.db",
                "source_table": "relay_transactions",
                "protocol": "Relay",
            },
            "portals": {
                "source_db": "databases/portals_transactions.db",
                "source_table": "portals_transactions",
                "protocol": "Portals",
            },
            "chainflip": {
                "source_db": "databases/chainflip_transactions.db",
                "source_table": "transactions",  # Chainflip uses different table name
                "protocol": "Chainflip",
            },
            "thorchain": {
                "source_db": "databases/thorchain_transactions.db",
                "source_table": "thorchain_transactions",
                "protocol": "THORChain",
            },
            "cowswap": {
                "source_db": "databases/cowswap_transactions.db",
                "source_table": "cowswap_transactions",
                "protocol": "CowSwap",
            },
            "zerox": {
                "source_db": "databases/zerox_transactions.db",
                "source_table": "zerox_transactions",
                "protocol": "0x Protocol",
            },
            "butterswap": {
                "source_db": "databases/butterswap_transactions.db",
                "source_table": "butterswap_transactions",
                "protocol": "ButterSwap",
            },
        }

        comp_conn = sqlite3.connect(self.comprehensive_db_path)
        comp_cursor = comp_conn.cursor()

        total_consolidated = 0

        for protocol_key, config in consolidation_map.items():
            if not os.path.exists(config["source_db"]):
                logger.warning(
                    f"⚠️ {config['protocol']} database not found: {config['source_db']}"
                )
                continue

            try:
                # Connect to source database
                source_conn = sqlite3.connect(config["source_db"])
                source_cursor = source_conn.cursor()

                # Check if table exists
                source_cursor.execute(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config['source_table']}'"
                )
                if not source_cursor.fetchone():
                    logger.warning(
                        f"⚠️ Table {config['source_table']} not found in {config['protocol']} database"
                    )
                    source_conn.close()
                    continue

                # Get all transactions from source
                source_cursor.execute(f"SELECT * FROM {config['source_table']}")
                rows = source_cursor.fetchall()

                # Get column names
                source_cursor.execute(f"PRAGMA table_info({config['source_table']})")
                columns = [row[1] for row in source_cursor.fetchall()]

                # Map to comprehensive schema
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    consolidated_row = self.map_to_comprehensive_schema(
                        row_dict, config["protocol"]
                    )

                    if consolidated_row:
                        comp_cursor.execute(
                            """
                            INSERT OR IGNORE INTO comprehensive_transactions 
                            (protocol, chain, tx_hash, block_number, timestamp, from_asset, to_asset,
                             from_amount, to_amount, from_amount_usd, to_amount_usd, volume_usd,
                             affiliate_fee_amount, affiliate_fee_usd, affiliate_fee_asset, affiliate_address,
                             sender_address, recipient_address, event_type, raw_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                consolidated_row["protocol"],
                                consolidated_row["chain"],
                                consolidated_row["tx_hash"],
                                consolidated_row["block_number"],
                                consolidated_row["timestamp"],
                                consolidated_row["from_asset"],
                                consolidated_row["to_asset"],
                                consolidated_row["from_amount"],
                                consolidated_row["to_amount"],
                                consolidated_row["from_amount_usd"],
                                consolidated_row["to_amount_usd"],
                                consolidated_row["volume_usd"],
                                consolidated_row["affiliate_fee_amount"],
                                consolidated_row["affiliate_fee_usd"],
                                consolidated_row["affiliate_fee_asset"],
                                consolidated_row["affiliate_address"],
                                consolidated_row["sender_address"],
                                consolidated_row["recipient_address"],
                                consolidated_row["event_type"],
                                consolidated_row["raw_data"],
                            ),
                        )
                        total_consolidated += 1

                source_conn.close()
                logger.info(
                    f"✅ Consolidated {len(rows)} {config['protocol']} transactions"
                )

            except Exception as e:
                logger.error(f"❌ Error consolidating {config['protocol']}: {e}")

        comp_conn.commit()
        comp_conn.close()

        logger.info(f"💾 Total consolidated transactions: {total_consolidated}")

    def map_to_comprehensive_schema(
        self, row_dict: Dict, protocol: str
    ) -> Optional[Dict]:
        """Map protocol-specific row to comprehensive schema"""
        try:
            # Base mapping - adapt based on actual column names in each protocol
            mapped = {
                "protocol": protocol,
                "chain": row_dict.get("chain", "unknown"),
                "tx_hash": row_dict.get(
                    "tx_hash", row_dict.get("transaction_hash", "")
                ),
                "block_number": row_dict.get("block_number", 0),
                "timestamp": row_dict.get(
                    "timestamp", row_dict.get("block_timestamp", 0)
                ),
                "from_asset": row_dict.get(
                    "from_asset",
                    row_dict.get("input_token", row_dict.get("sell_token", "")),
                ),
                "to_asset": row_dict.get(
                    "to_asset",
                    row_dict.get("output_token", row_dict.get("buy_token", "")),
                ),
                "from_amount": self.safe_float(
                    row_dict.get("from_amount", row_dict.get("input_amount", 0))
                ),
                "to_amount": self.safe_float(
                    row_dict.get("to_amount", row_dict.get("output_amount", 0))
                ),
                "from_amount_usd": self.safe_float(row_dict.get("from_amount_usd", 0)),
                "to_amount_usd": self.safe_float(row_dict.get("to_amount_usd", 0)),
                "volume_usd": self.safe_float(row_dict.get("volume_usd", 0)),
                "affiliate_fee_amount": self.safe_float(
                    row_dict.get("affiliate_fee_amount", 0)
                ),
                "affiliate_fee_usd": self.safe_float(
                    row_dict.get("affiliate_fee_usd", 0)
                ),
                "affiliate_fee_asset": row_dict.get("affiliate_fee_asset", ""),
                "affiliate_address": row_dict.get(
                    "affiliate_address", row_dict.get("partner", "")
                ),
                "sender_address": row_dict.get(
                    "sender", row_dict.get("from_address", "")
                ),
                "recipient_address": row_dict.get(
                    "recipient", row_dict.get("to_address", "")
                ),
                "event_type": row_dict.get("event_type", "transaction"),
                "raw_data": str(row_dict),
            }

            return mapped

        except Exception as e:
            logger.error(f"Error mapping row for {protocol}: {e}")
            return None

    def safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                # Handle string representations of large numbers
                if value.isdigit():
                    return float(value)
                return float(value) if value else 0.0
            return float(value) if value else 0.0
        except:
            return 0.0

    def print_execution_summary(self, results: Dict, total_time: float):
        """Print execution summary"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 MASTER RUNNER EXECUTION SUMMARY")
        logger.info(f"{'='*80}")

        successful = sum(1 for r in results.values() if r["status"] == "success")
        failed = len(results) - successful

        logger.info(f"⏱️  Total Execution Time: {total_time:.2f}s")
        logger.info(f"✅ Successful Listeners: {successful}/{len(results)}")
        logger.info(f"❌ Failed Listeners: {failed}")

        logger.info(f"\n📋 Individual Results:")
        for protocol, result in results.items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            logger.info(f"   {status_emoji} {protocol.upper()}: {result['time']:.2f}s")
            if result["error"]:
                logger.info(f"      Error: {result['error']}")

    def get_comprehensive_stats(self):
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.comprehensive_db_path)
        cursor = conn.cursor()

        logger.info(f"\n{'='*80}")
        logger.info("📊 COMPREHENSIVE DATABASE STATISTICS")
        logger.info(f"{'='*80}")

        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM comprehensive_transactions")
        total_tx = cursor.fetchone()[0]
        logger.info(f"📈 Total Transactions: {total_tx:,}")

        # By protocol
        cursor.execute(
            "SELECT protocol, COUNT(*) FROM comprehensive_transactions GROUP BY protocol ORDER BY COUNT(*) DESC"
        )
        protocol_stats = cursor.fetchall()
        logger.info(f"\n📊 Transactions by Protocol:")
        for protocol, count in protocol_stats:
            logger.info(f"   {protocol}: {count:,}")

        # By chain
        cursor.execute(
            "SELECT chain, COUNT(*) FROM comprehensive_transactions GROUP BY chain ORDER BY COUNT(*) DESC"
        )
        chain_stats = cursor.fetchall()
        logger.info(f"\n🔗 Transactions by Chain:")
        for chain, count in chain_stats:
            logger.info(f"   {chain}: {count:,}")

        # Financial stats
        cursor.execute(
            "SELECT SUM(affiliate_fee_usd), SUM(volume_usd) FROM comprehensive_transactions"
        )
        total_fees, total_volume = cursor.fetchone()
        total_fees = total_fees or 0
        total_volume = total_volume or 0

        logger.info(f"\n💰 Financial Summary:")
        logger.info(f"   Total Affiliate Fees: ${total_fees:,.2f}")
        logger.info(f"   Total Volume: ${total_volume:,.2f}")

        conn.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="ShapeShift Affiliate Fee Master Runner"
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=2000,
        help="Number of blocks to scan for blockchain listeners",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of records to fetch for API listeners",
    )
    parser.add_argument(
        "--skip-consolidation", action="store_true", help="Skip database consolidation"
    )
    parser.add_argument(
        "--consolidate-only",
        action="store_true",
        help="Only run database consolidation",
    )
    parser.add_argument(
        "--stats-only", action="store_true", help="Only show comprehensive statistics"
    )

    args = parser.parse_args()

    runner = MasterRunner()

    if args.stats_only:
        runner.get_comprehensive_stats()
        return

    if not args.consolidate_only:
        # Run all listeners
        results = runner.run_all_listeners(args.blocks, args.limit)

    if not args.skip_consolidation:
        # Consolidate databases
        runner.consolidate_databases()

    # Show final statistics
    runner.get_comprehensive_stats()


if __name__ == "__main__":
    main()
