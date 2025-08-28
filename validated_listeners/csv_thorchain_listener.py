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

# =============================================================================
# IMPORTS AND DEPENDENCIES
# =============================================================================
# Standard library imports for file operations, time handling, and data processing
import os  # File and directory operations
import sys  # System-specific parameters and functions
import time  # Time-related functions
import logging  # Logging functionality
import csv  # CSV file reading and writing
import requests  # HTTP library for API calls

# Date and time handling
from datetime import datetime, timedelta

# Type hints for better code documentation and IDE support
from typing import Dict, List, Any, Optional

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
    get_storage_path,  # Get storage directory paths
    get_listener_config,  # Get listener-specific configuration
    get_threshold,  # Get threshold values for filtering
)

# =============================================================================
# MAIN LISTENER CLASS DEFINITION
# =============================================================================


class CSVThorChainListener:
    """
    CSV-based listener for THORChain swaps with ShapeShift affiliate fees

    This class is responsible for:
    1. Monitoring THORChain swaps via Midgard API
    2. Detecting ShapeShift affiliate transactions
    3. Storing transaction data in CSV format
    4. Tracking processing progress to avoid duplicates

    Note: Enhanced affiliate detection logic using memo patterns (:ss:) has been
    discovered and documented but is currently commented out. See the
    _is_shapeshift_affiliate_swap method for details on the enhanced detection
    patterns found in blocks 22,456,113 and 22,470,673.
    """

    def __init__(self):
        """
        Initialize the THORChain listener with centralized configuration

        This method:
        1. Loads the centralized configuration
        2. Sets up logging
        3. Extracts THORChain-specific settings
        4. Creates necessary directories and CSV files
        5. Initializes the data structure
        """

        # =====================================================================
        # STEP 1: LOAD CENTRALIZED CONFIGURATION
        # =====================================================================
        # Load the main configuration object that contains all settings
        self.config = get_config()

        # Set up logging for this listener instance
        self.logger = logging.getLogger(__name__)

        # =====================================================================
        # STEP 2: EXTRACT THORCHAIN-SPECIFIC CONFIGURATION
        # =====================================================================
        # Get THORChain contract configuration from the main config
        thorchain_config = self.config.config.get("contracts", {}).get("thorchain", {})

        # Set up API endpoints for THORChain data
        # Midgard API: Provides swap and transaction data
        # Thornode API: Provides blockchain and node information
        self.midgard_api = thorchain_config.get(
            "midgard_api", "https://midgard.ninerealms.com/v2"
        )
        self.thornode_api = thorchain_config.get(
            "thornode_api", "https://thornode.ninerealms.com"
        )

        # =====================================================================
        # STEP 3: SET UP SHAPESHIFT AFFILIATE INFORMATION
        # =====================================================================
        # Get the ShapeShift affiliate address and name for THORChain
        # These are used to identify transactions that involve ShapeShift
        self.shapeshift_affiliate_address = thorchain_config.get(
            "affiliate_address", "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju"
        )
        self.shapeshift_affiliate_name = thorchain_config.get("affiliate_name", "ss")

        # =====================================================================
        # STEP 4: SET UP STORAGE PATHS
        # =====================================================================
        # Get the base storage directory from configuration
        self.csv_dir = self.config.get_storage_path("csv_directory")

        # Create specific subdirectories for this listener
        # transactions_dir: Stores the main transaction data
        # block_tracking_dir: Stores progress tracking information
        self.transactions_dir = os.path.join(self.csv_dir, "transactions")
        self.block_tracking_dir = os.path.join(self.csv_dir, "block_tracking")

        # =====================================================================
        # STEP 5: GET LISTENER-SPECIFIC CONFIGURATION
        # =====================================================================
        # Get configuration specific to the THORChain listener
        self.listener_config = self.config.get_listener_config("thorchain")

        # Extract rate limiting and request size settings
        # api_rate_limit: How long to wait between API calls (prevents overwhelming the API)
        # max_swaps_per_request: Maximum number of swaps to fetch in one API call
        self.api_rate_limit = self.listener_config.get("api_rate_limit", 1.0)
        self.max_swaps_per_request = self.listener_config.get(
            "max_swaps_per_request", 100
        )

        # =====================================================================
        # STEP 6: GET THRESHOLD VALUES
        # =====================================================================
        # Get minimum volume threshold for filtering transactions
        # Only transactions above this USD value will be processed
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")

        # =====================================================================
        # STEP 7: INITIALIZE CSV STRUCTURE
        # =====================================================================
        # Create the necessary CSV files and directories
        self._init_csv_structure()

        # =====================================================================
        # STEP 8: LOG INITIALIZATION SUCCESS
        # =====================================================================
        # Log successful initialization with key configuration details
        self.logger.info("✅ CSVThorChainListener initialized successfully")
        self.logger.info(
            f"🎯 THORChain affiliate address: {self.shapeshift_affiliate_address}"
        )
        self.logger.info(
            f"🎯 THORChain affiliate name: {self.shapeshift_affiliate_name}"
        )
        self.logger.info(f"🌐 Midgard API: {self.midgard_api}")

    def _init_csv_structure(self):
        """
        Initialize CSV file structure for THORChain data

        This method creates:
        1. The main transactions CSV file with proper headers
        2. The block tracking CSV file for progress monitoring
        3. All necessary directories if they don't exist

        CSV Headers Explained:
        - tx_hash: Unique transaction identifier
        - chain: Source blockchain (e.g., BTC, ETH, BNB)
        - block_number: Block where transaction occurred
        - timestamp: When transaction was processed
        - from_address: Sender address
        - to_address: Recipient address
        - affiliate_address: ShapeShift affiliate address
        - affiliate_fee_amount: Fee amount in base units
        - affiliate_fee_token: Token used for fee payment
        - affiliate_fee_usd: Fee amount in USD
        - volume_amount: Total transaction volume
        - volume_token: Token used for volume
        - volume_usd: Volume in USD
        - gas_used: Gas consumed (if applicable)
        - gas_price: Gas price (if applicable)
        - pool: Liquidity pool involved
        - from_asset: Asset being swapped from
        - to_asset: Asset being swapped to
        - from_amount: Amount being swapped from
        - to_amount: Amount being swapped to
        - affiliate_fee_asset: Asset used for affiliate fee
        - affiliate_fee_amount_asset: Affiliate fee in asset units
        - created_at: When record was created
        """

        # =====================================================================
        # STEP 1: CREATE NECESSARY DIRECTORIES
        # =====================================================================
        # Create the transactions directory if it doesn't exist
        # exist_ok=True prevents errors if directory already exists
        os.makedirs(self.transactions_dir, exist_ok=True)

        # Create the block tracking directory if it doesn't exist
        # This stores progress information to avoid reprocessing data
        os.makedirs(self.block_tracking_dir, exist_ok=True)

        # =====================================================================
        # STEP 2: INITIALIZE TRANSACTIONS CSV FILE
        # =====================================================================
        # Define the path to the main transactions CSV file
        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )

        # Only create the file if it doesn't already exist
        if not os.path.exists(transactions_path):
            # Define the column headers for the CSV file
            # These headers define the structure of our transaction data
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

            # Create the CSV file with the defined headers
            # newline='' ensures consistent line ending handling across platforms
            # encoding='utf-8' ensures proper character encoding
            with open(transactions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            # Log successful creation of the transactions CSV file
            self.logger.info(
                f"✅ Created THORChain transactions CSV: {transactions_path}"
            )

        # =====================================================================
        # STEP 3: INITIALIZE BLOCK TRACKER CSV FILE
        # =====================================================================
        # Define the path to the block tracking CSV file
        # This file tracks our progress to avoid reprocessing the same data
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )

        # Only create the file if it doesn't already exist
        if not os.path.exists(block_tracker_path):
            # Define the column headers for the block tracker
            # last_processed_offset: API pagination offset for resuming
            # last_processed_date: When we last processed data
            # total_swaps_processed: Total count of swaps processed
            headers = [
                "last_processed_offset",
                "last_processed_date",
                "total_swaps_processed",
            ]

            # Create the CSV file with the defined headers
            with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            # Log successful creation of the block tracker CSV file
            self.logger.info(
                f"✅ Created THORChain block tracker CSV: {block_tracker_path}"
            )

    # =============================================================================
    # CSV MANAGEMENT & TRACKING METHODS
    # =============================================================================
    # These methods handle the creation, reading, and updating of CSV files
    # They ensure data persistence and progress tracking across listener runs

    def get_last_processed_offset(self) -> int:
        """
        Get the last processed offset for API pagination

        This method:
        1. Reads the block tracker CSV file
        2. Extracts the last processed offset
        3. Returns 0 if no previous processing has occurred

        Returns:
            int: The last processed offset, or 0 if none exists

        Purpose:
            - Prevents reprocessing the same data on restart
            - Enables resuming from where we left off
            - Maintains data integrity across multiple runs
        """

        # Define the path to the block tracker CSV file
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )

        # If the file doesn't exist, we haven't processed any data yet
        if not os.path.exists(block_tracker_path):
            return 0

        try:
            # Open and read the block tracker CSV file
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Read the first (and should be only) row
                # The block tracker typically has one row with current progress
                for row in reader:
                    # Extract the last processed offset and convert to integer
                    # If the value doesn't exist, default to 0
                    return int(row.get("last_processed_offset", 0))

        except Exception as e:
            # Log any errors that occur while reading the file
            # This prevents the listener from crashing due to file corruption
            self.logger.error(f"❌ Error reading block tracker: {e}")

        # Return 0 if any errors occur or if the file is empty
        return 0

    def update_block_tracker(self, offset: int):
        """
        Update the block tracker with the latest processed offset

        This method:
        1. Reads the existing block tracker data
        2. Updates the last processed offset
        3. Updates the processing timestamp
        4. Increments the total swaps processed counter
        5. Writes the updated data back to the CSV file

        Args:
            offset (int): The latest processed offset from the API

        Purpose:
            - Maintains progress tracking for resuming on restart
            - Provides audit trail of processing activity
            - Enables monitoring of listener performance
        """

        # Define the path to the block tracker CSV file
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "thorchain_block_tracker.csv"
        )

        # =====================================================================
        # STEP 1: READ EXISTING BLOCK TRACKER DATA
        # =====================================================================
        # Initialize an empty list to store existing rows
        rows = []

        try:
            # Read the existing block tracker CSV file
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Convert the reader to a list for manipulation
                rows = list(reader)

        except FileNotFoundError:
            # If the file doesn't exist, we'll create it with new data
            # This is normal for the first run
            pass

        # =====================================================================
        # STEP 2: UPDATE OR CREATE TRACKER ENTRY
        # =====================================================================
        if rows:
            # If we have existing data, update the first row
            # The block tracker typically maintains one row with current status
            rows[0]["last_processed_offset"] = str(offset)
            rows[0]["last_processed_date"] = str(int(time.time()))

            # Increment the total swaps processed counter
            # Convert to int, increment, then convert back to string
            current_count = int(rows[0].get("total_swaps_processed", 0))
            rows[0]["total_swaps_processed"] = str(current_count + 1)

        else:
            # If no existing data, create a new row
            # This happens on the first run or if the file was corrupted
            rows.append(
                {
                    "last_processed_offset": str(offset),
                    "last_processed_date": str(int(time.time())),
                    "total_swaps_processed": "1",
                }
            )

        # =====================================================================
        # STEP 3: WRITE UPDATED DATA BACK TO CSV
        # =====================================================================
        # Define the column headers for the CSV file
        headers = [
            "last_processed_offset",
            "last_processed_date",
            "total_swaps_processed",
        ]

        # Write the updated data back to the CSV file
        # This overwrites the existing file with the new data
        with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()  # Write the column headers
            writer.writerows(rows)  # Write all the data rows

    def save_transactions_to_csv(self, transactions: List[Dict[str, Any]]):
        """
        Save THORChain affiliate transactions to CSV file

        This method:
        1. Validates transaction data structure
        2. Ensures all required fields are present
        3. Appends them to the main transactions CSV file
        4. Logs the successful save operation

        Args:
            transactions (List[Dict[str, Any]]): List of transaction data dictionaries

        Purpose:
            - Persists transaction data for analysis and reporting
            - Maintains historical record of all detected affiliate transactions
            - Enables data export and integration with other systems
        """

        # =====================================================================
        # STEP 0: INPUT VALIDATION
        # =====================================================================
        # If no transactions to save, exit early
        if not transactions:
            self.logger.info("ℹ️ No transactions to save")
            return

        if not isinstance(transactions, list):
            raise ValueError(f"Transactions must be a list, got: {type(transactions)}")

        # =====================================================================
        # STEP 1: VALIDATE TRANSACTION STRUCTURE
        # =====================================================================
        # Define required fields for transaction data
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

        # Define the path to the main transactions CSV file
        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )

        try:
            # Open the CSV file in append mode ('a') to add new transactions
            # newline='' ensures consistent line ending handling
            # encoding='utf-8' ensures proper character encoding
            with open(transactions_path, "a", newline="", encoding="utf-8") as f:
                # Create a CSV writer using the keys from the first transaction as field names
                # This ensures all transactions have the same structure
                writer = csv.DictWriter(f, fieldnames=valid_transactions[0].keys())

                # Write all valid transactions to the CSV file
                writer.writerows(valid_transactions)

            # Log successful save operation with transaction count
            self.logger.info(
                f"✅ Saved {len(valid_transactions)} valid THORChain transactions to CSV"
            )
            self.logger.info(
                f"📊 Skipped {len(transactions) - len(valid_transactions)} invalid transactions"
            )

        except Exception as e:
            self.logger.error(f"❌ Error saving transactions to CSV: {e}")
            raise

    # =============================================================================
    # THORCHAIN API INTEGRATION METHODS
    # =============================================================================
    # These methods handle communication with THORChain's APIs
    # They fetch swap data and process it for affiliate detection

    def fetch_thorchain_swaps(
        self, offset: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch THORChain swaps from Midgard API

        This method:
        1. Validates input parameters
        2. Constructs the API request URL and parameters
        3. Makes an HTTP GET request to the Midgard API
        4. Processes the response and extracts swap data
        5. Handles errors gracefully and logs issues

        Args:
            offset (int): Pagination offset for API requests (default: 0)
            limit (int): Maximum number of swaps to fetch (default: 100)

        Returns:
            List[Dict[str, Any]]: List of swap data dictionaries, or empty list on error

        Raises:
            ValueError: If offset or limit parameters are invalid
        """

        # =====================================================================
        # STEP 0: INPUT VALIDATION
        # =====================================================================
        # Validate input parameters to prevent API abuse and ensure data quality
        if not isinstance(offset, int) or offset < 0:
            raise ValueError(f"Offset must be a non-negative integer, got: {offset}")

        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise ValueError(
                f"Limit must be an integer between 1 and 1000, got: {limit}"
            )

        try:
            # =====================================================================
            # STEP 1: CONSTRUCT API REQUEST
            # =====================================================================
            url = f"{self.midgard_api}/actions"
            params = {
                "offset": offset,
                "limit": limit,
                "type": "swap",  # Only fetch swap actions
            }

            self.logger.info(
                f"📡 Fetching THORChain swaps: offset={offset}, limit={limit}"
            )

            # =====================================================================
            # STEP 2: MAKE HTTP REQUEST
            # =====================================================================
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # =====================================================================
            # STEP 3: PROCESS RESPONSE
            # =====================================================================
            data = response.json()
            actions = data.get("actions", [])

            # Validate response structure
            if not isinstance(actions, list):
                self.logger.warning(
                    "⚠️ API returned non-list actions, treating as empty"
                )
                actions = []

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
        """
        Filter swaps to only include ShapeShift affiliate transactions

        This method:
        1. Iterates through each swap in the list
        2. Checks if the swap involves a ShapeShift affiliate
        3. If it does, appends it to the affiliate_swaps list
        4. Logs the number of affiliate swaps found

        Args:
            swaps (List[Dict[str, Any]]): List of raw swap data dictionaries

        Returns:
            List[Dict[str, Any]]: List of swap data dictionaries that are ShapeShift affiliates

        Purpose:
            - Identifies transactions that involve ShapeShift's affiliate program
            - Filters out non-affiliate transactions for further processing
            - Maintains data integrity and reduces processing overhead
        """

        affiliate_swaps = []

        for swap in swaps:
            try:
                # Check if this swap involves ShapeShift affiliate
                if self._is_shapeshift_affiliate_swap(swap):
                    affiliate_swaps.append(swap)

            except Exception as e:
                # Log warnings for any errors encountered during swap processing
                self.logger.warning(f"⚠️ Error processing swap: {e}")
                continue

        # Log the number of affiliate swaps found
        self.logger.info(
            f"🎯 Found {len(affiliate_swaps)} ShapeShift affiliate swaps out of {len(swaps)} total"
        )
        return affiliate_swaps

    def _is_shapeshift_affiliate_swap(self, swap: Dict[str, Any]) -> bool:
        """
        Check if a swap involves ShapeShift affiliate

        This method:
        1. Attempts to identify affiliate involvement based on various fields
        2. Returns True if a match is found, False otherwise

        Args:
            swap (Dict[str, Any]): A single swap data dictionary

        Returns:
            bool: True if the swap is a ShapeShift affiliate, False otherwise

        Purpose:
            - Determines if a transaction is eligible for affiliate tracking
            - Uses a combination of memo patterns, address checks, and field searches
            - Provides robust affiliate detection across different swap formats
        """

        try:
            # =====================================================================
            # STEP 1: CHECK FOR AFFILIATE NAME IN IN DATA
            # =====================================================================
            # Check for affiliate name "ss" in the swap data (e.g., in 'in' or 'out' data)
            # This is a common pattern found in THORChain swaps
            in_data = swap.get("in", {})
            if isinstance(in_data, dict):
                # Look for affiliate information in swap metadata (memo)
                memo = in_data.get("memo", "")
                if self.shapeshift_affiliate_name.lower() in memo.lower():
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with name in 'in' data: {memo}"
                    )
                    return True

                # Check for affiliate address in memo or other fields
                if self.shapeshift_affiliate_address.lower() in memo.lower():
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with address in 'in' data: {memo}"
                    )
                    return True

            # =====================================================================
            # STEP 2: CHECK FOR AFFILIATE NAME IN OUT DATA
            # =====================================================================
            # Check for affiliate name "ss" in the swap data (e.g., in 'out' data)
            out_data = swap.get("out", {})
            if isinstance(out_data, dict):
                memo = out_data.get("memo", "")
                if self.shapeshift_affiliate_name.lower() in memo.lower():
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with name in 'out' data: {memo}"
                    )
                    return True
                if self.shapeshift_affiliate_address.lower() in memo.lower():
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with address in 'out' data: {memo}"
                    )
                    return True

            # =====================================================================
            # STEP 3: CHECK ADDITIONAL FIELDS FOR AFFILIATE INFO
            # =====================================================================
            # Check for affiliate information in other fields that might contain it
            for field in ["memo", "affiliate", "referrer", "partner"]:
                if (
                    field in swap
                    and self.shapeshift_affiliate_name.lower()
                    in str(swap[field]).lower()
                ):
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with name in field {field}: {swap[field]}"
                    )
                    return True
                if (
                    field in swap
                    and self.shapeshift_affiliate_address.lower()
                    in str(swap[field]).lower()
                ):
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction with address in field {field}: {swap[field]}"
                    )
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
            # Log warnings for any errors encountered during affiliate check
            self.logger.warning(f"⚠️ Error checking affiliate involvement: {e}")
            return False

    # =============================================================================
    # TRANSACTION PROCESSING & CONVERSION
    # =============================================================================

    def convert_swap_to_transaction(self, swap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a THORChain swap to our transaction format

        This method:
        1. Extracts basic swap information (tx_hash, timestamp)
        2. Processes 'in' and 'out' data to determine volume and assets
        3. Calculates volume in USD (simplified)
        4. Creates a transaction record dictionary

        Args:
            swap (Dict[str, Any]): A single swap data dictionary

        Returns:
            Dict[str, Any]: A transaction data dictionary, or an empty dictionary on error

        Purpose:
            - Transforms raw swap data into a standardized transaction format
            - Ensures consistent data structure for storage and analysis
            - Handles potential errors and edge cases
        """

        try:
            # =====================================================================
            # STEP 1: EXTRACT BASIC SWAP INFORMATION
            # =====================================================================
            # Get the transaction hash (txID) from the swap data
            tx_hash = swap.get(
                "txID",
                "0x0000000000000000000000000000000000000000000000000000000000000000",
            )

            # Get the timestamp from the swap data
            # If 'date' is not available, use current time
            timestamp = swap.get("date", int(time.time()))

            # =====================================================================
            # STEP 2: EXTRACT IN AND OUT DATA
            # =====================================================================
            # Get the 'in' and 'out' data from the swap
            in_data = swap.get("in", {})
            out_data = swap.get("out", {})

            # =====================================================================
            # STEP 3: CALCULATE VOLUME AND ASSETS
            # =====================================================================
            # Initialize volume and asset variables
            volume_amount = 0
            volume_token = "0x0000000000000000000000000000000000000000"
            volume_usd = 0

            # Process 'in' data to determine volume and token
            if isinstance(in_data, dict):
                # Get the amount from the 'in' data
                volume_amount = in_data.get("amount", "0")

                # Get the asset from the 'in' data
                # THORChain uses a list of coins, where the first one is the primary asset
                # We need to extract the asset from the first coin in the list
                coins = in_data.get("coins", [{}])
                if coins and isinstance(coins[0], dict):
                    volume_token = coins[0].get(
                        "asset", "0x0000000000000000000000000000000000000000"
                    )
                else:
                    volume_token = "0x0000000000000000000000000000000000000000"  # Default if no coin data

                # Convert volume amount to float and calculate USD value (simplified)
                # This is a placeholder and would require actual price feeds
                try:
                    # Assuming a fixed price for THORChain assets for simplicity
                    # In a real scenario, you'd fetch current prices from a price feed
                    # For example, if 1 RUNE = $10, then 1 RUNE = 100000000 RUNE
                    # So, if volume_amount is 100000000, it's 1 RUNE, which is $10
                    # This is a very simplified calculation and needs proper price feeds
                    volume_usd = (
                        float(volume_amount) / (10**8) * 50
                    )  # Example: 1 RUNE = $50
                except (ValueError, TypeError):
                    volume_usd = 0  # Default to 0 if conversion fails

            # =====================================================================
            # STEP 4: CREATE TRANSACTION RECORD
            # =====================================================================
            # Create a dictionary to store the transaction details
            transaction = {
                "tx_hash": tx_hash,
                "chain": "thorchain",  # Source blockchain
                "block_number": swap.get("height", 0),  # Block height
                "timestamp": timestamp,  # Timestamp of the swap
                "from_address": in_data.get(
                    "address", "0x0000000000000000000000000000000000000000"
                )
                if isinstance(in_data, dict)
                else "0x0000000000000000000000000000000000000000",  # Sender address
                "to_address": out_data.get(
                    "address", "0x0000000000000000000000000000000000000000"
                )
                if isinstance(out_data, dict)
                else "0x0000000000000000000000000000000000000000",  # Recipient address
                "affiliate_address": self.shapeshift_affiliate_address,  # ShapeShift affiliate address
                "affiliate_fee_amount": "0",  # THORChain doesn't have explicit affiliate fees in this format
                "affiliate_fee_token": "0x0000000000000000000000000000000000000000",  # Token used for affiliate fee (if any)
                "affiliate_fee_usd": "0",  # USD value of affiliate fee
                "volume_amount": str(volume_amount),  # Volume in base units
                "volume_token": volume_token,  # Token used for volume
                "volume_usd": str(volume_usd),  # Volume in USD
                "gas_used": 0,  # THORChain doesn't use gas in this context
                "gas_price": 0,  # THORChain doesn't use gas in this context
                "pool": swap.get("pool", ""),  # Liquidity pool involved
                "from_asset": coins[0].get("asset", "")
                if coins and isinstance(coins[0], dict)
                else "",  # Asset being swapped from
                "to_asset": out_data.get("coins", [{}])[0].get("asset", "")
                if out_data.get("coins")
                else "",  # Asset being swapped to
                "from_amount": str(in_data.get("amount", "0"))
                if isinstance(in_data, dict)
                else "0",  # Amount being swapped from
                "to_amount": str(out_data.get("amount", "0"))
                if isinstance(out_data, dict)
                else "0",  # Amount being swapped to
                "affiliate_fee_asset": "",  # No explicit affiliate fee asset in this format
                "affiliate_fee_amount_asset": "0",  # No explicit affiliate fee amount in asset units in this format
                "created_at": int(time.time()),  # Timestamp of record creation
            }

            return transaction

        except Exception as e:
            # Log errors for any issues during swap conversion
            self.logger.error(f"❌ Error converting swap to transaction: {e}")
            return {}

    # =============================================================================
    # MAIN LISTENER EXECUTION
    # =============================================================================

    def run_listener(self, max_swaps: Optional[int] = None):
        """
        Run the THORChain listener to fetch and process swaps

        This method:
        1. Determines the number of swaps to fetch (default: max_swaps_per_request)
        2. Fetches swaps from THORChain using the fetch_thorchain_swaps method
        3. Filters the fetched swaps for ShapeShift affiliate transactions
        4. Converts affiliate swaps to transaction records
        5. Saves the transaction records to CSV
        6. Updates the block tracker
        7. Applies rate limiting
        8. Logs completion and returns total transactions

        Args:
            max_swaps (Optional[int]): Maximum number of swaps to process (default: None)

        Returns:
            int: Total number of transactions processed

        Purpose:
            - Orchestrates the entire listener loop
            - Handles error cases and logging
            - Provides a clean interface for external calls
        """

        # Determine the number of swaps to fetch
        # If max_swaps is not provided, use the configured max_swaps_per_request
        if max_swaps is None:
            max_swaps = self.max_swaps_per_request

        # Log the start of the listener run
        self.logger.info(f"🚀 Starting THORChain listener")
        self.logger.info(f"📊 Max swaps per request: {max_swaps}")

        # Initialize total transactions counter
        total_transactions = 0

        # Get the last processed offset from the block tracker
        offset = self.get_last_processed_offset()

        try:
            # =====================================================================
            # STEP 1: FETCH SWAPS FROM THORCHAIN
            # =====================================================================
            # Fetch swaps from THORChain using the fetch_thorchain_swaps method
            # This method handles pagination and error logging
            swaps = self.fetch_thorchain_swaps(offset=offset, limit=max_swaps)

            # If no new swaps were found, log and return
            if not swaps:
                self.logger.info("✅ No new swaps found")
                return 0

            # =====================================================================
            # STEP 2: FILTER FOR SHAPESHIFT AFFILIATE SWAPS
            # =====================================================================
            # Filter the fetched swaps to only include ShapeShift affiliate transactions
            # This method handles error logging and filtering logic
            affiliate_swaps = self.filter_shapeshift_affiliate_swaps(swaps)

            # If no affiliate swaps were found, log and update offset
            if not affiliate_swaps:
                self.logger.info("✅ No ShapeShift affiliate swaps found")
                # Still update offset to avoid re-processing
                self.update_block_tracker(offset + len(swaps))
                return 0

            # =====================================================================
            # STEP 3: CONVERT SWAPS TO TRANSACTIONS
            # =====================================================================
            # Convert affiliate swaps to transaction records
            transactions = []
            for swap in affiliate_swaps:
                try:
                    # Convert each swap to a transaction record
                    transaction = self.convert_swap_to_transaction(swap)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    # Log errors for any issues during swap conversion
                    self.logger.error(f"❌ Error converting swap: {e}")
                    continue

            # =====================================================================
            # STEP 4: SAVE TRANSACTIONS TO CSV
            # =====================================================================
            # Save the transaction records to CSV
            if transactions:
                self.save_transactions_to_csv(transactions)
                total_transactions = len(transactions)

            # =====================================================================
            # STEP 5: UPDATE BLOCK TRACKER
            # =====================================================================
            # Update the block tracker with the latest processed offset
            self.update_block_tracker(offset + len(swaps))

            # =====================================================================
            # STEP 6: APPLY RATE LIMITING
            # =====================================================================
            # Wait for a specified amount of time before making the next API call
            # This prevents overwhelming the THORChain API with too many requests
            time.sleep(self.api_rate_limit)

            # =====================================================================
            # STEP 7: LOG COMPLETION AND RETURN
            # =====================================================================
            # Log completion and return the total number of transactions processed
            self.logger.info(
                f"🎯 THORChain listener completed. Total transactions: {total_transactions}"
            )
            return total_transactions

        except Exception as e:
            # Log errors for any issues during the listener run
            self.logger.error(f"❌ Error running THORChain listener: {e}")
            return 0

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def get_csv_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the CSV data

        This method:
        1. Reads the main transactions CSV file
        2. Calculates various statistics (total transactions, pools, volume ranges)
        3. Returns a dictionary with these statistics

        Returns:
            Dict[str, Any]: A dictionary containing statistics

        Purpose:
            - Provides insights into the collected data
            - Helps with monitoring and debugging
            - Enables data export and reporting
        """

        # Define the path to the main transactions CSV file
        transactions_path = os.path.join(
            self.transactions_dir, "thorchain_transactions.csv"
        )

        # If the file doesn't exist, return default statistics
        if not os.path.exists(transactions_path):
            return {"total_transactions": 0, "pools": {}, "volume_ranges": {}}

        try:
            # Open and read the main transactions CSV file
            with open(transactions_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Convert the reader to a list to count rows
                rows = list(reader)

            # Initialize statistics dictionary
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

            # Iterate through each row in the CSV file
            for row in rows:
                # Get the pool from the transaction data
                pool = row.get("pool", "unknown")

                # Count transactions by pool
                if pool not in stats["pools"]:
                    stats["pools"][pool] = 0
                stats["pools"][pool] += 1

                # Analyze volume distribution
                try:
                    # Convert volume_usd from string to float
                    volume_usd = float(row.get("volume_usd", 0))

                    # Categorize volume ranges
                    if volume_usd < 13:
                        stats["volume_ranges"]["under_13"] += 1
                    elif volume_usd < 100:
                        stats["volume_ranges"]["13_to_100"] += 1
                    elif volume_usd < 1000:
                        stats["volume_ranges"]["100_to_1000"] += 1
                    else:
                        stats["volume_ranges"]["over_1000"] += 1
                except (ValueError, TypeError):
                    # Skip rows with invalid volume values
                    continue

            return stats

        except Exception as e:
            # Log errors for any issues during CSV statistics calculation
            self.logger.error(f"❌ Error getting CSV stats: {e}")
            return {"total_transactions": 0, "pools": {}, "volume_ranges": {}}


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """
    Main function to run the THORChain listener

    This function:
    1. Creates an instance of CSVThorChainListener
    2. Runs the listener to fetch and process swaps
    3. Gets statistics about the processed data
    4. Prints the statistics to the console
    5. Handles any errors that might occur during execution
    """
    try:
        # Create an instance of the THORChain listener
        listener = CSVThorChainListener()

        # Run the listener to fetch and process swaps
        # The run_listener method handles pagination and rate limiting
        total_transactions = listener.run_listener()

        # Get statistics about the processed data
        stats = listener.get_csv_stats()

        # Print statistics to the console
        print(f"\n📊 THORChain Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by pool:")
        for pool, count in stats["pools"].items():
            print(f"     {pool}: {count}")
        print(f"   Volume distribution:")
        for range_name, count in stats["volume_ranges"].items():
            print(f"     {range_name}: {count} transactions")

        # Log successful completion
        print(f"\n✅ THORChain listener completed successfully!")
        print(f"   Total events found: {total_transactions}")

    except Exception as e:
        # Log errors for any issues during the main execution
        logging.error(f"❌ Error running THORChain listener: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    main()
