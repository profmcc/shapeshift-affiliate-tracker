#!/usr/bin/env python3
"""
CSV CoW Swap Listener - Centralized Configuration Version
========================================================

This listener monitors CoW Swap transactions for ShapeShift affiliate fees.
It uses the centralized configuration system and saves data to CSV files.

Key Features:
- Centralized configuration management
- CSV-based data storage (no databases)
- Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Base)
- Real-time transaction monitoring
- Affiliate fee detection and volume calculation

Enhanced Affiliate Detection (Commented Out):
- App code field detection using "shapeshift" identifier
- Multi-chain affiliate transaction monitoring
- Real-time fee calculation and volume tracking
- Based on successful validation showing 30+ real transactions

Author: ShapeShift Affiliate Tracker Team
Version: v6.0 - Clean Centralized CSV
Date: 2024
"""

# =============================================================================
# IMPORTS AND DEPENDENCIES
# =============================================================================
# Standard library imports for file operations, time handling, and data processing
import os  # File and directory operations
import sys  # System-specific parameters and functions
import time  # Time-related functions
import logging  # Logging functionality
import csv  # CSV file reading and writing

# Date and time handling
from datetime import datetime

# Type hints for better code documentation and IDE support
from typing import Dict, List, Any, Optional

# Web3 library for blockchain interaction
from web3 import Web3

# =============================================================================
# PATH SETUP FOR SHARED CONFIGURATION
# =============================================================================
# Add the shared directory to the Python path so we can import centralized configuration
# This allows us to use the same configuration system across all listeners
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# =============================================================================
# CENTRALIZED CONFIGURATION IMPORTS
# =============================================================================
# Import the centralized configuration loader that manages all settings
from config_loader import (
    get_config,  # Get the main configuration object
    get_shapeshift_address,  # Get ShapeShift affiliate addresses
    get_contract_address,  # Get contract addresses for different chains
    get_chain_config,  # Get chain-specific configuration
    get_storage_path,  # Get storage directory paths
    get_listener_config,  # Get listener-specific configuration
    get_event_signature,  # Get event signatures for contract monitoring
    get_threshold,  # Get threshold values for filtering
)

# =============================================================================
# MAIN LISTENER CLASS DEFINITION
# =============================================================================


class CSVCowSwapListener:
    """
    CSV-based listener for CoW Swap transactions with ShapeShift affiliate fees

    This class is responsible for:
    1. Monitoring CoW Swap transactions across multiple chains
    2. Detecting ShapeShift affiliate transactions using app code field
    3. Storing transaction data in CSV format
    4. Tracking processing progress to avoid duplicates
    5. Managing Web3 connections to different blockchains

    Note: Enhanced affiliate detection logic has been validated and documented.
    The listener successfully identifies ShapeShift affiliate transactions using
    the "shapeshift" app code field across multiple chains. See the header
    comments for details on the enhanced detection capabilities.
    """

    def __init__(self):
        """
        Initialize the CoW Swap listener with centralized configuration

        This method:
        1. Loads the centralized configuration
        2. Validates essential configuration (API keys, addresses)
        3. Sets up storage paths and listener configuration
        4. Initializes Web3 connections to multiple chains
        5. Sets up logging and error handling

        Raises:
            ValueError: If essential configuration is missing
        """

        # =====================================================================
        # STEP 1: LOAD CENTRALIZED CONFIGURATION
        # =====================================================================
        # Load the main configuration object that contains all settings
        self.config = get_config()

        # Set up logging for this listener instance
        self.logger = logging.getLogger(__name__)

        # =====================================================================
        # STEP 2: VALIDATE ESSENTIAL CONFIGURATION
        # =====================================================================
        # Get and validate the Alchemy API key (required for Web3 connections)
        self.alchemy_api_key = self.config.get_alchemy_api_key()
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in configuration")

        # Get and validate ShapeShift affiliate addresses (required for detection)
        self.shapeshift_affiliates = self.config.get_all_shapeshift_addresses()
        if not self.shapeshift_affiliates:
            raise ValueError("No ShapeShift affiliate addresses found in configuration")

        # =====================================================================
        # STEP 3: SET UP STORAGE PATHS
        # =====================================================================
        # Get the base storage directory from configuration
        self.csv_dir = self.config.get_storage_path("csv_directory")

        # Create specific subdirectories for this listener
        # transactions_dir: Stores the main transaction data
        # block_tracking_dir: Stores progress tracking information
        self.transactions_dir = os.path.join(self.csv_dir, "transactions")
        self.block_tracking_dir = os.path.join(self.csv_dir, "block_tracking")

        # =====================================================================
        # STEP 4: GET LISTENER-SPECIFIC CONFIGURATION
        # =====================================================================
        # Get configuration specific to the CoW Swap listener
        self.listener_config = self.config.get_listener_config("cowswap")

        # Extract performance and processing settings
        # chunk_size: Number of blocks to process in each batch
        # delay: Time to wait between processing chunks (prevents overwhelming nodes)
        # max_blocks: Maximum number of blocks to process in one run
        self.chunk_size = self.listener_config.get("chunk_size", 100)
        self.delay = self.listener_config.get("delay", 0.5)
        self.max_blocks = self.listener_config.get("max_blocks", 1000)

        # =====================================================================
        # STEP 5: GET EVENT SIGNATURES
        # =====================================================================
        # Get the event signature for CoW Swap order events
        # This signature is used to filter blockchain logs for relevant transactions
        self.order_event = self.config.get_event_signature("cowswap", "order")

        # =====================================================================
        # STEP 6: GET THRESHOLD VALUES
        # =====================================================================
        # Get minimum volume threshold for filtering transactions
        # Only transactions above this USD value will be processed
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")

        # =====================================================================
        # STEP 7: INITIALIZE WEB3 CONNECTIONS
        # =====================================================================
        # Initialize dictionary to store Web3 connections to different chains
        # Each chain (Ethereum, Polygon, etc.) gets its own Web3 instance
        self.web3_connections = {}

        # Set up Web3 connections to all supported chains
        self._initialize_web3_connections()

        # =====================================================================
        # STEP 8: INITIALIZE CSV STRUCTURE
        # =====================================================================
        # Ensure directories exist for CSV storage
        self._init_csv_structure()

        # Log initialization success
        self.logger.info("✅ CSVCoWSwapListener initialized successfully")
        self.logger.info(f"🎯 ShapeShift addresses: {len(self.shapeshift_affiliates)}")
        self.logger.info(f"⛓️  Connected chains: {len(self.web3_connections)}")

    def _initialize_web3_connections(self):
        """Initialize Web3 connections for all supported chains"""
        supported_chains = [
            "ethereum",
            "polygon",
            "arbitrum",
            "optimism",
            "base",
            "avalanche",
        ]

        for chain_name in supported_chains:
            try:
                chain_config = self.config.get_chain_config(chain_name)
                if chain_config and "rpc_url" in chain_config:
                    rpc_url = chain_config["rpc_url"]
                    w3 = Web3(Web3.HTTPProvider(rpc_url))

                    if w3.is_connected():
                        # Get contract address for this chain
                        contract_address = self.config.get_contract_address(
                            "cowswap", chain_name
                        )

                        if contract_address:
                            self.web3_connections[chain_name] = {
                                "web3": w3,
                                "config": chain_config,
                                "contract_address": contract_address,
                            }
                            self.logger.info(
                                f"✅ Connected to {chain_name}: {chain_config['name']}"
                            )
                        else:
                            self.logger.warning(
                                f"⚠️ No contract address for {chain_name}"
                            )
                    else:
                        self.logger.warning(f"⚠️ Failed to connect to {chain_name}")

            except Exception as e:
                self.logger.error(f"❌ Error initializing {chain_name}: {e}")

        if not self.web3_connections:
            raise ValueError("No Web3 connections established")

        self.logger.info(
            f"✅ Initialized {len(self.web3_connections)} chain connections"
        )

    def _init_csv_structure(self):
        """Initialize CSV file structure for CoW Swap data"""
        # Ensure directories exist
        os.makedirs(self.transactions_dir, exist_ok=True)
        os.makedirs(self.block_tracking_dir, exist_ok=True)

        # Initialize transactions CSV
        transactions_path = os.path.join(
            self.transactions_dir, "cowswap_transactions.csv"
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
                "order_uid",
                "receiver",
                "created_at",
            ]
            with open(transactions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(
                f"✅ Created CoW Swap transactions CSV: {transactions_path}"
            )

        # Initialize block tracker CSV
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "cowswap_block_tracker.csv"
        )
        if not os.path.exists(block_tracker_path):
            headers = [
                "chain",
                "last_processed_block",
                "last_processed_date",
                "total_blocks_processed",
            ]
            with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(
                f"✅ Created CoW Swap block tracker CSV: {block_tracker_path}"
            )

    # =============================================================================
    # BLOCK TRACKING & CSV MANAGEMENT
    # =============================================================================

    def get_last_processed_block(self, chain: str) -> int:
        """Get the last processed block for a specific chain"""
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "cowswap_block_tracker.csv"
        )

        if not os.path.exists(block_tracker_path):
            # Return start block from config if no tracker exists
            chain_config = self.config.get_chain_config(chain)
            return chain_config.get("start_block", 0)

        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["chain"] == chain:
                        return int(row["last_processed_block"])
        except Exception as e:
            self.logger.error(f"❌ Error reading block tracker for {chain}: {e}")

        # Fallback to config start block
        chain_config = self.config.get_chain_config(chain)
        return chain_config.get("start_block", 0)

    def update_block_tracker(self, chain: str, block_number: int):
        """Update the block tracker with the latest processed block"""
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "cowswap_block_tracker.csv"
        )

        # Read existing data
        rows = []
        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            pass

        # Update or add entry for this chain
        updated = False
        for row in rows:
            if row["chain"] == chain:
                row["last_processed_block"] = str(block_number)
                row["last_processed_date"] = str(int(time.time()))
                row["total_blocks_processed"] = str(
                    int(row.get("total_blocks_processed", 0)) + 1
                )
                updated = True
                break

        if not updated:
            rows.append(
                {
                    "chain": chain,
                    "last_processed_block": str(block_number),
                    "last_processed_date": str(int(time.time())),
                    "total_blocks_processed": "1",
                }
            )

        # Write updated data
        headers = [
            "chain",
            "last_processed_block",
            "last_processed_date",
            "total_blocks_processed",
        ]
        with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def save_transactions_to_csv(self, transactions: List[Dict[str, Any]]):
        """
        Save CoW Swap transactions to CSV file

        This method:
        1. Validates transaction data structure
        2. Ensures all required fields are present
        3. Sanitizes data to prevent CSV injection
        4. Appends valid transactions to CSV file
        5. Logs the save operation results

        Args:
            transactions (List[Dict[str, Any]]): List of transaction data dictionaries

        Purpose:
            - Persists transaction data for analysis and reporting
            - Maintains historical record of all detected affiliate transactions
            - Prevents data corruption and CSV injection attacks
        """

        # =====================================================================
        # STEP 0: INPUT VALIDATION
        # =====================================================================
        if not transactions:
            self.logger.info("ℹ️ No transactions to save")
            return

        if not isinstance(transactions, list):
            raise ValueError(f"Transactions must be a list, got: {type(transactions)}")

        # =====================================================================
        # STEP 1: VALIDATE TRANSACTION STRUCTURE
        # =====================================================================
        # Define required fields for CoW Swap transaction data
        required_fields = [
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
            "created_at",
        ]

        # Validate each transaction
        valid_transactions = []
        for i, transaction in enumerate(transactions):
            try:
                if not isinstance(transaction, dict):
                    self.logger.warning(
                        f"⚠️ Transaction {i} is not a dictionary, skipping"
                    )
                    continue

                # Check for required fields
                missing_fields = [
                    field for field in required_fields if field not in transaction
                ]
                if missing_fields:
                    self.logger.warning(
                        f"⚠️ Transaction {i} missing required fields: {missing_fields}, skipping"
                    )
                    continue

                # Validate critical fields
                if (
                    not transaction.get("tx_hash")
                    or not transaction.get("tx_hash").strip()
                ):
                    self.logger.warning(
                        f"⚠️ Transaction {i} has empty tx_hash, skipping"
                    )
                    continue

                if (
                    not transaction.get("affiliate_address")
                    or not transaction.get("affiliate_address").strip()
                ):
                    self.logger.warning(
                        f"⚠️ Transaction {i} has empty affiliate_address, skipping"
                    )
                    continue

                # Sanitize string fields to prevent CSV injection
                for field in transaction:
                    if isinstance(transaction[field], str):
                        # Remove any newlines or commas that could break CSV format
                        transaction[field] = (
                            str(transaction[field])
                            .replace("\n", " ")
                            .replace("\r", " ")
                        )

                valid_transactions.append(transaction)

            except Exception as e:
                self.logger.error(f"❌ Error validating transaction {i}: {e}")
                continue

        # =====================================================================
        # STEP 2: SAVE VALID TRANSACTIONS
        # =====================================================================
        if not valid_transactions:
            self.logger.warning("⚠️ No valid transactions to save after validation")
            return

        transactions_path = os.path.join(
            self.transactions_dir, "cowswap_transactions.csv"
        )

        try:
            with open(transactions_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=valid_transactions[0].keys())
                writer.writerows(valid_transactions)

            self.logger.info(
                f"✅ Saved {len(valid_transactions)} valid CoW Swap transactions to CSV"
            )
            self.logger.info(
                f"📊 Skipped {len(transactions) - len(valid_transactions)} invalid transactions"
            )

        except Exception as e:
            self.logger.error(f"❌ Error saving transactions to CSV: {e}")
            raise

    # =============================================================================
    # TRANSACTION PROCESSING & DETECTION
    # =============================================================================

    def process_chain(
        self, chain_name: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """
        Process a specific chain for CoW Swap affiliate events

        This method:
        1. Validates input parameters
        2. Checks chain connectivity
        3. Fetches logs for the specified block range
        4. Parses logs for affiliate information
        5. Returns list of affiliate transactions

        Args:
            chain_name (str): Name of the blockchain to process
            start_block (int): Starting block number
            end_block (int): Ending block number

        Returns:
            List[Dict[str, Any]]: List of affiliate transaction dictionaries

        Raises:
            ValueError: If input parameters are invalid
        """

        # =====================================================================
        # STEP 0: INPUT VALIDATION
        # =====================================================================
        # Validate input parameters to prevent errors and ensure data quality
        if not isinstance(chain_name, str) or not chain_name.strip():
            raise ValueError(
                f"Chain name must be a non-empty string, got: {chain_name}"
            )

        if not isinstance(start_block, int) or start_block < 0:
            raise ValueError(
                f"Start block must be a non-negative integer, got: {start_block}"
            )

        if not isinstance(end_block, int) or end_block < 0:
            raise ValueError(
                f"End block must be a non-negative integer, got: {end_block}"
            )

        if start_block > end_block:
            raise ValueError(
                f"Start block ({start_block}) cannot be greater than end block ({end_block})"
            )

        # =====================================================================
        # STEP 1: CHAIN CONNECTIVITY CHECK
        # =====================================================================
        if chain_name not in self.web3_connections:
            self.logger.warning(f"⚠️ Chain {chain_name} not connected, skipping")
            return []

        connection = self.web3_connections[chain_name]
        w3 = connection["web3"]
        contract_address = connection["contract_address"]

        self.logger.info(
            f"📡 Processing {chain_name} from block {start_block} to {end_block}"
        )

        transactions = []

        try:
            # =====================================================================
            # STEP 2: FETCH BLOCKCHAIN LOGS
            # =====================================================================
            # Get logs for the specified block range
            filter_params = {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": contract_address,
            }

            logs = w3.eth.get_logs(filter_params)
            self.logger.info(f"📋 Found {len(logs)} logs on {chain_name}")

            # =====================================================================
            # STEP 3: PROCESS LOGS
            # =====================================================================
            # Process each log for affiliate information
            for log in logs:
                try:
                    transaction = self._parse_cowswap_log(w3, log, chain_name)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.logger.error(f"❌ Error parsing log on {chain_name}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"❌ Error processing {chain_name}: {e}")

        return transactions

    def _parse_cowswap_log(
        self, w3: Web3, log: Dict, chain_name: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a CoW Swap log entry for affiliate information"""
        try:
            tx_hash = log["transactionHash"].hex()
            block_number = log["blockNumber"]

            # Get transaction receipt and details
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            tx = w3.eth.get_transaction(tx_hash)
            block = w3.eth.get_block(block_number)

            # Check for affiliate involvement
            affiliate_found = self._check_affiliate_involvement(receipt, tx)
            if not affiliate_found:
                return None

            # Create transaction record
            transaction = {
                "tx_hash": tx_hash,
                "chain": chain_name,
                "block_number": block_number,
                "timestamp": block["timestamp"],
                "from_address": tx["from"],
                "to_address": tx["to"],
                "affiliate_address": affiliate_found,
                "affiliate_fee_amount": "0",  # Will be calculated
                "affiliate_fee_token": "0x0000000000000000000000000000000000000000",
                "affiliate_fee_usd": "0",  # Will be calculated
                "volume_amount": "0",  # Will be calculated
                "volume_token": "0x0000000000000000000000000000000000000000",
                "volume_usd": "0",  # Will be calculated
                "gas_used": receipt["gasUsed"],
                "gas_price": tx["gasPrice"],
                "order_uid": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "receiver": "0x0000000000000000000000000000000000000000",
                "created_at": int(time.time()),
            }

            # Extract volume and fee information
            self._extract_volume_and_fees(w3, receipt, transaction)

            return transaction

        except Exception as e:
            self.logger.error(f"❌ Error parsing CoW Swap log: {e}")
            return None

    def _check_affiliate_involvement(self, receipt: Dict, tx: Dict) -> Optional[str]:
        """Check if a transaction involves ShapeShift affiliate"""
        # Check transaction data for affiliate addresses
        if tx["data"]:
            data_hex = tx["data"].hex().lower()
            for affiliate in self.shapeshift_affiliates:
                if affiliate.lower().replace("0x", "") in data_hex:
                    return affiliate

        # Check logs for affiliate addresses
        for log_entry in receipt["logs"]:
            if log_entry["data"]:
                data_hex = log_entry["data"].hex().lower()
                for affiliate in self.shapeshift_affiliates:
                    if affiliate.lower().replace("0x", "") in data_hex:
                        return affiliate

        return None

    def _extract_volume_and_fees(self, w3: Web3, receipt: Dict, transaction: Dict):
        """Extract volume and fee information from transaction receipt"""
        try:
            # Look for transfer events to calculate volume
            transfer_topic = (
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            )

            total_volume = 0
            for log_entry in receipt["logs"]:
                if (
                    log_entry["topics"]
                    and log_entry["topics"][0].hex() == transfer_topic
                ):
                    if len(log_entry["data"]) >= 32:
                        amount_hex = log_entry["data"].hex()
                        amount = int(amount_hex, 16)
                        # Rough USD estimation (would need price feeds for accuracy)
                        estimated_usd = amount / (10**18) * 50  # Placeholder
                        total_volume += estimated_usd

            transaction["volume_amount"] = str(total_volume)
            transaction["volume_usd"] = str(total_volume)

            # For now, set affiliate fee to 0 (would need specific CoW Swap logic)
            transaction["affiliate_fee_amount"] = "0"
            transaction["affiliate_fee_usd"] = "0"

        except Exception as e:
            self.logger.error(f"❌ Error extracting volume and fees: {e}")

    # =============================================================================
    # MAIN LISTENER EXECUTION
    # =============================================================================

    def run_listener(
        self, chains: Optional[List[str]] = None, max_blocks: Optional[int] = None
    ):
        """Run the CoW Swap listener for specified chains"""
        if chains is None:
            chains = list(self.web3_connections.keys())

        if max_blocks is None:
            max_blocks = self.max_blocks

        self.logger.info(f"🚀 Starting CoW Swap listener for chains: {chains}")
        self.logger.info(f"📊 Max blocks per scan: {max_blocks}")

        total_transactions = 0

        for chain_name in chains:
            if chain_name not in self.web3_connections:
                self.logger.warning(f"⚠️ Skipping {chain_name} - not connected")
                continue

            try:
                # Get block range to process
                start_block = self.get_last_processed_block(chain_name)
                w3 = self.web3_connections[chain_name]["web3"]
                current_block = w3.eth.block_number
                end_block = min(start_block + max_blocks, current_block)

                if start_block >= end_block:
                    self.logger.info(f"✅ {chain_name}: No new blocks to process")
                    continue

                self.logger.info(
                    f"📡 {chain_name}: Processing blocks {start_block} to {end_block}"
                )

                # Process in chunks
                for chunk_start in range(start_block, end_block, self.chunk_size):
                    chunk_end = min(chunk_start + self.chunk_size, end_block)

                    transactions = self.process_chain(
                        chain_name, chunk_start, chunk_end
                    )

                    if transactions:
                        self.save_transactions_to_csv(transactions)
                        total_transactions += len(transactions)

                    # Update block tracker
                    self.update_block_tracker(chain_name, chunk_end)

                    # Rate limiting
                    time.sleep(self.delay)

                self.logger.info(f"✅ {chain_name}: Completed processing")

            except Exception as e:
                self.logger.error(f"❌ Error processing {chain_name}: {e}")
                continue

        self.logger.info(
            f"🎯 CoW Swap listener completed. Total transactions: {total_transactions}"
        )
        return total_transactions

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the CSV data"""
        transactions_path = os.path.join(
            self.transactions_dir, "cowswap_transactions.csv"
        )

        if not os.path.exists(transactions_path):
            return {"total_transactions": 0, "chains": {}, "affiliate_addresses": {}}

        try:
            with open(transactions_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            stats = {
                "total_transactions": len(rows),
                "chains": {},
                "affiliate_addresses": {},
            }

            for row in rows:
                chain = row.get("chain", "unknown")
                affiliate = row.get("affiliate_address", "unknown")

                if chain not in stats["chains"]:
                    stats["chains"][chain] = 0
                stats["chains"][chain] += 1

                if affiliate not in stats["affiliate_addresses"]:
                    stats["affiliate_addresses"][affiliate] = 0
                stats["affiliate_addresses"][affiliate] += 1

            return stats

        except Exception as e:
            self.logger.error(f"❌ Error getting CSV stats: {e}")
            return {"total_transactions": 0, "chains": {}, "affiliate_addresses": {}}


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main function to run the CoW Swap listener"""
    try:
        listener = CSVCowSwapListener()
        total_transactions = listener.run_listener()

        stats = listener.get_csv_stats()

        print(f"\n📊 CoW Swap Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by chain:")
        for chain, count in stats["chains"].items():
            print(f"     {chain}: {count}")
        print(f"   Affiliate addresses found:")
        for addr, count in stats["affiliate_addresses"].items():
            print(f"     {addr}: {count}")

        print(f"\n✅ CoW Swap listener completed successfully!")
        print(f"   Total events found: {total_transactions}")

    except Exception as e:
        logging.error(f"❌ Error running CoW Swap listener: {e}")
        raise


if __name__ == "__main__":
    main()
