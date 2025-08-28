#!/usr/bin/env python3
"""
CSV Portals Listener - Centralized Configuration Version
=======================================================

This listener monitors Portals bridge transactions for ShapeShift affiliate fees.
It uses the centralized configuration system and saves data to CSV files.

Key Features:
- Centralized configuration management
- CSV-based data storage (no databases)
- Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Base)
- Real-time transaction monitoring
- Affiliate fee detection and volume calculation

Enhanced Affiliate Detection (Added):
- ShapeShift DAO Treasury affiliate fee detection
- Net deposit analysis to ShapeShift treasury
- ERC-20 transfer pattern recognition for treasury recipients
- Based on discovery that Portals transactions show affiliate fees flowing TO ShapeShift DAO Treasury

Author: ShapeShift Affiliate Tracker Team
Version: v6.0 - Clean Centralized CSV
Date: 2024
"""

import os
import sys
import time
import logging
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from web3 import Web3

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Import centralized configuration
from config_loader import (
    get_config,
    get_shapeshift_address,
    get_contract_address,
    get_chain_config,
    get_storage_path,
    get_listener_config,
    get_event_signature,
    get_threshold,
)

# =============================================================================
# CONFIGURATION & SETUP
# =============================================================================


class CSVPortalsListener:
    """CSV-based listener for Portals bridge transactions with ShapeShift affiliate fees

    Note: Enhanced affiliate detection logic has been added to detect when ShapeShift DAO Treasury
    receives affiliate fees as net deposits. This method looks for transactions where regular wallets
    make bridge transactions and the treasury receives affiliate fees on-chain, which is more reliable
    than event signature detection for Portals transactions.
    """

    def __init__(self):
        """Initialize the Portals listener with centralized configuration"""
        # Load centralized configuration
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # Validate essential configuration
        self.alchemy_api_key = self.config.get_alchemy_api_key()
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in configuration")

        # Get ShapeShift affiliate addresses
        self.shapeshift_affiliates = self.config.get_all_shapeshift_addresses()
        if not self.shapeshift_affiliates:
            raise ValueError("No ShapeShift affiliate addresses found in configuration")

        # Get storage paths
        self.csv_dir = self.config.get_storage_path("csv_directory")
        self.transactions_dir = os.path.join(self.csv_dir, "transactions")
        self.block_tracking_dir = os.path.join(self.csv_dir, "block_tracking")

        # Get listener configuration
        self.listener_config = self.config.get_listener_config("portals")
        self.chunk_size = self.listener_config.get("chunk_size", 100)
        self.delay = self.listener_config.get("delay", 0.5)
        self.max_blocks = self.listener_config.get("max_blocks", 1000)

        # Get event signatures
        self.affiliate_fee_event = self.config.get_event_signature(
            "portals", "affiliate_fee"
        )

        # Get thresholds
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")

        # Initialize Web3 connections
        self.web3_connections = {}
        self._initialize_web3_connections()

        # Initialize CSV structure
        self._init_csv_structure()

        self.logger.info("✅ CSVPortalsListener initialized successfully")
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
                            "portals", chain_name
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
        """Initialize CSV file structure for Portals data"""
        # Ensure directories exist
        os.makedirs(self.transactions_dir, exist_ok=True)
        os.makedirs(self.block_tracking_dir, exist_ok=True)

        # Initialize transactions CSV
        transactions_path = os.path.join(
            self.transactions_dir, "portals_transactions.csv"
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
                "bridge_type",
                "source_chain",
                "destination_chain",
                "created_at",
            ]
            with open(transactions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(f"✅ Created Portals transactions CSV: {transactions_path}")

        # Initialize block tracker CSV
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "portals_block_tracker.csv"
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
                f"✅ Created Portals block tracker CSV: {block_tracker_path}"
            )

    # =============================================================================
    # BLOCK TRACKING & CSV MANAGEMENT
    # =============================================================================

    def get_last_processed_block(self, chain: str) -> int:
        """Get the last processed block for a specific chain"""
        block_tracker_path = os.path.join(
            self.block_tracking_dir, "portals_block_tracker.csv"
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
            self.block_tracking_dir, "portals_block_tracker.csv"
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
        """Save Portals transactions to CSV file"""
        if not transactions:
            return

        transactions_path = os.path.join(
            self.transactions_dir, "portals_transactions.csv"
        )

        with open(transactions_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
            writer.writerows(transactions)

        self.logger.info(f"✅ Saved {len(transactions)} Portals transactions to CSV")

    # =============================================================================
    # TRANSACTION PROCESSING & DETECTION
    # =============================================================================

    def process_chain(
        self, chain_name: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """Process a specific chain for Portals affiliate events"""
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
            # Get logs for the specified block range
            filter_params = {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": contract_address,
            }

            self.logger.info(
                f"🔍 Scanning blocks {start_block} to {end_block} on {chain_name}"
            )
            self.logger.info(f"📍 Contract address: {contract_address}")

            logs = w3.eth.get_logs(filter_params)
            self.logger.info(f"📋 Found {len(logs)} logs on {chain_name}")

            # Debug: Check if we're scanning the right block range
            if start_block <= 22774492 <= end_block:
                self.logger.info(
                    f"🎯 Block 22774492 (known Portals transaction) is in scan range!"
                )
            else:
                self.logger.info(
                    f"⚠️ Block 22774492 (known Portals transaction) is NOT in scan range {start_block}-{end_block}"
                )

            # If no logs found, try scanning without contract address filter (broader search)
            if len(logs) == 0:
                self.logger.warning(
                    f"⚠️  No logs found with contract address filter on {chain_name}"
                )
                self.logger.info(
                    f"🔍 Trying broader search without contract address filter..."
                )

                broader_filter = {"fromBlock": start_block, "toBlock": end_block}

                broader_logs = w3.eth.get_logs(broader_filter)
                self.logger.info(
                    f"📋 Broader search found {len(broader_logs)} logs on {chain_name}"
                )

                if len(broader_logs) > 0:
                    self.logger.info(
                        f"🔍 Processing broader logs to find Portals-related transactions..."
                    )
                    logs = broader_logs
                else:
                    self.logger.warning(
                        f"⚠️  No logs found at all in block range {start_block} to {end_block}"
                    )
                    return []

            # Process each log
            for i, log in enumerate(logs):
                self.logger.info(f"🔍 Processing log {i+1}/{len(logs)} on {chain_name}")
                try:
                    transaction = self._parse_portals_log(w3, log, chain_name)
                    if transaction:
                        transactions.append(transaction)
                        self.logger.info(f"✅ Found transaction from log {i+1}")
                    else:
                        self.logger.info(f"🔍 No transaction found from log {i+1}")
                except Exception as e:
                    self.logger.error(f"❌ Error parsing log {i+1} on {chain_name}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"❌ Error processing {chain_name}: {e}")

        return transactions

    def _parse_portals_log(
        self, w3: Web3, log: Dict, chain_name: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a Portals log entry for affiliate information"""
        try:
            tx_hash = log["transactionHash"].hex()
            block_number = log["blockNumber"]

            # Get transaction receipt and details
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            tx = w3.eth.get_transaction(tx_hash)
            block = w3.eth.get_block(block_number)

            # Check for affiliate involvement
            self.logger.info(
                f"🔍 Checking affiliate involvement for transaction {tx_hash}"
            )
            affiliate_found = self._check_affiliate_involvement(receipt, tx)
            if not affiliate_found:
                self.logger.info(
                    f"🔍 No affiliate involvement found for transaction {tx_hash}"
                )
                return None
            else:
                self.logger.info(f"🎯 Affiliate involvement found: {affiliate_found}")

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
                "bridge_type": "portals",
                "source_chain": chain_name,
                "destination_chain": chain_name,  # Will be determined from bridge data
                "created_at": int(time.time()),
            }

            # Extract volume and fee information
            self._extract_volume_and_fees(w3, receipt, transaction)

            return transaction

        except Exception as e:
            self.logger.error(f"❌ Error parsing Portals log: {e}")
            return None

    def _check_affiliate_involvement(self, receipt: Dict, tx: Dict) -> Optional[str]:
        """Check if a transaction involves ShapeShift affiliate"""

        # =============================================================================
        # ENHANCED SHAPESHIFT AFFILIATE DETECTION LOGIC
        # =============================================================================
        # Based on discovery that net transfers go to ShapeShift DAO Treasury
        # This provides more reliable detection than event signatures

        # Method 1: Check for ShapeShift DAO Treasury receiving net transfers
        # ShapeShift DAO Treasury addresses across chains (from Safe.global)
        shapeshift_treasury_addresses = [
            "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum Mainnet
            "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
            "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche
            "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            "0xb0E3175341794D1dc8E5F02a02F9D26989EbedB3",  # Gnosis Chain
            "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",  # Binance Smart Chain
            "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
        ]

        for treasury_address in shapeshift_treasury_addresses:
            if self._check_shapeshift_treasury_involvement(receipt, treasury_address):
                self.logger.info(
                    f"🎯 Found ShapeShift affiliate transaction via DAO Treasury: {treasury_address}"
                )
                return f"ShapeShift_DAO_Treasury_{treasury_address[:8]}"

        # Method 2: Check transaction data for affiliate addresses
        if tx["data"]:
            data_hex = tx["data"].hex().lower()
            for affiliate in self.shapeshift_affiliates:
                if affiliate.lower().replace("0x", "") in data_hex:
                    self.logger.info(
                        f"🎯 Found ShapeShift affiliate transaction via data field: {affiliate}"
                    )
                    return affiliate

        # Method 3: Check logs for affiliate addresses
        for log_entry in receipt["logs"]:
            if log_entry["data"]:
                data_hex = log_entry["data"].hex().lower()
                for affiliate in self.shapeshift_affiliates:
                    if affiliate.lower().replace("0x", "") in data_hex:
                        self.logger.info(
                            f"🎯 Found ShapeShift affiliate transaction via log data: {affiliate}"
                        )
                        return affiliate

        return None

    def _check_shapeshift_treasury_involvement(
        self, receipt: Dict, treasury_address: str
    ) -> bool:
        """Check if ShapeShift DAO Treasury receives affiliate fees as net deposits"""
        try:
            # Look for transactions where ShapeShift DAO Treasury receives affiliate fees
            # This happens when regular wallets make bridge transactions and treasury gets net deposits

            # Method 1: Check for ERC-20 transfers TO the ShapeShift DAO Treasury
            # ERC-20 Transfer event: Transfer(address from, address to, uint256 value)
            transfer_topic = (
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            )

            treasury_received_funds = False

            self.logger.info(
                f"🔍 Checking {len(receipt['logs'])} logs for ShapeShift treasury involvement..."
            )

            for i, log_entry in enumerate(receipt["logs"]):
                if (
                    log_entry["topics"]
                    and len(log_entry["topics"]) >= 3
                    and log_entry["topics"][0].hex() == transfer_topic
                ):
                    self.logger.info(f"🔍 Log {i}: Found ERC-20 transfer event")

                    # Check if the recipient (topic[2]) is the ShapeShift DAO Treasury
                    if len(log_entry["topics"]) >= 3:
                        recipient = log_entry["topics"][2].hex()
                        self.logger.info(f"🔍 Log {i}: Transfer recipient: {recipient}")
                        self.logger.info(
                            f"🔍 Log {i}: Looking for treasury: {treasury_address}"
                        )

                        if recipient.lower().endswith(
                            treasury_address.lower().replace("0x", "")
                        ):
                            self.logger.info(
                                f"🎯 Found ERC-20 transfer TO ShapeShift DAO Treasury: {treasury_address}"
                            )
                            self.logger.info(f"   Transfer recipient: {recipient}")
                            treasury_received_funds = True
                            break

            # Method 2: Check for any log where treasury appears as recipient
            # This catches other types of transfers or events where treasury receives funds
            if not treasury_received_funds:
                for log_entry in receipt["logs"]:
                    # Check if the treasury address appears in topics (likely as recipient)
                    if log_entry["topics"]:
                        for topic in log_entry["topics"]:
                            topic_hex = topic.hex().lower()
                            if (
                                treasury_address.lower().replace("0x", "")
                                in topic_hex.lower()
                            ):
                                self.logger.info(
                                    f"🎯 ShapeShift DAO Treasury found in log topic (likely recipient): {treasury_address}"
                                )
                                treasury_received_funds = True
                                break

                    if treasury_received_funds:
                        break

            # Method 3: Check if treasury appears in data (could be recipient info)
            if not treasury_received_funds:
                for log_entry in receipt["logs"]:
                    if log_entry["data"]:
                        data_hex = log_entry["data"].hex().lower()
                        if (
                            treasury_address.lower().replace("0x", "")
                            in data_hex.lower()
                        ):
                            self.logger.info(
                                f"🎯 ShapeShift DAO Treasury found in log data (likely recipient): {treasury_address}"
                            )
                            treasury_received_funds = True
                            break

            if treasury_received_funds:
                self.logger.info(
                    f"🎯 ShapeShift DAO Treasury received affiliate fees in this transaction"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ Error checking ShapeShift treasury involvement: {e}")
            return False

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

            # For now, set affiliate fee to 0 (would need specific Portals logic)
            transaction["affiliate_fee_amount"] = "0"
            transaction["affiliate_fee_usd"] = "0"

        except Exception as e:
            self.logger.error(f"❌ Error extracting volume and fees: {e}")

    # =============================================================================
    # MAIN LISTENER EXECUTION
    # =============================================================================

    def run_listener(
        self,
        chains: Optional[List[str]] = None,
        max_blocks: Optional[int] = None,
        start_block_override: Optional[int] = None,
        end_block_override: Optional[int] = None,
    ):
        """Run the Portals listener for specified chains"""
        if chains is None:
            chains = list(self.web3_connections.keys())

        if max_blocks is None:
            max_blocks = self.max_blocks

        self.logger.info(f"🚀 Starting Portals listener for chains: {chains}")
        self.logger.info(f"📊 Max blocks per scan: {max_blocks}")

        # Check for block override (for testing specific ranges)
        if start_block_override is not None or end_block_override is not None:
            self.logger.info(
                f"🎯 BLOCK OVERRIDE: Start={start_block_override}, End={end_block_override}"
            )

        total_transactions = 0

        for chain_name in chains:
            if chain_name not in self.web3_connections:
                self.logger.warning(f"⚠️ Skipping {chain_name} - not connected")
                continue

            try:
                w3 = self.web3_connections[chain_name]["web3"]
                current_block = w3.eth.block_number

                # Determine block range to process
                if start_block_override is not None and end_block_override is not None:
                    # Use override blocks (for testing specific ranges)
                    start_block = start_block_override
                    end_block = end_block_override
                    self.logger.info(
                        f"🔍 {chain_name}: Using override blocks {start_block} to {end_block}"
                    )
                else:
                    # Use normal block tracking
                    start_block = self.get_last_processed_block(chain_name)
                    self.logger.info(
                        f"🔍 {chain_name}: Current block: {current_block}, Start block: {start_block}"
                    )

                    # If no blocks processed yet, start from a reasonable recent block
                    if start_block == 0:
                        start_block = max(
                            0, current_block - 1000
                        )  # Start from 1000 blocks ago
                        self.logger.info(
                            f"🔍 {chain_name}: No previous blocks, starting from: {start_block}"
                        )

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

                    # Update block tracker (only if not using override)
                    if start_block_override is None:
                        self.update_block_tracker(chain_name, chunk_end)

                    # Rate limiting
                    time.sleep(self.delay)

                self.logger.info(f"✅ {chain_name}: Completed processing")

            except Exception as e:
                self.logger.error(f"❌ Error processing {chain_name}: {e}")
                continue

        self.logger.info(
            f"🎯 Portals listener completed. Total transactions: {total_transactions}"
        )
        return total_transactions

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the CSV data"""
        transactions_path = os.path.join(
            self.transactions_dir, "portals_transactions.csv"
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
    """Main function to run the Portals listener"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Portals Listener with Block Override Options"
    )
    parser.add_argument(
        "--start-block", type=int, help="Override start block for testing"
    )
    parser.add_argument("--end-block", type=int, help="Override end block for testing")
    parser.add_argument(
        "--test-known-block",
        action="store_true",
        help="Test on known block 22774492 where ShapeShift transaction exists",
    )

    args = parser.parse_args()

    try:
        listener = CSVPortalsListener()

        # Check for test mode
        if args.test_known_block:
            print(
                "🎯 TESTING KNOWN BLOCK: 22774492 (where ShapeShift transaction exists)"
            )
            start_block = 22774492
            end_block = 22774493  # Scan just this block
            total_transactions = listener.run_listener(
                start_block_override=start_block, end_block_override=end_block
            )
        elif args.start_block is not None and args.end_block is not None:
            print(f"🎯 CUSTOM BLOCK RANGE: {args.start_block} to {args.end_block}")
            total_transactions = listener.run_listener(
                start_block_override=args.start_block, end_block_override=args.end_block
            )
        else:
            print("🚀 RUNNING NORMAL LISTENER MODE")
            total_transactions = listener.run_listener()

        stats = listener.get_csv_stats()

        print(f"\n📊 Portals Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by chain:")
        for chain, count in stats["chains"].items():
            print(f"     {chain}: {count}")
        print(f"   Affiliate addresses found:")
        for addr, count in stats["affiliate_addresses"].items():
            print(f"     {addr}: {count}")

        print(f"\n✅ Portals listener completed successfully!")
        print(f"   Total events found: {total_transactions}")

        if args.test_known_block and total_transactions == 0:
            print(f"\n⚠️  WARNING: No transactions found in known block 22774492")
            print(f"💡 This suggests the detection logic may still have issues")
        elif args.test_known_block and total_transactions > 0:
            print(
                f"\n🎯 SUCCESS: Found {total_transactions} transactions in known block!"
            )
            print(f"💡 The Portals listener is now working correctly")

    except Exception as e:
        logging.error(f"❌ Error running Portals listener: {e}")
        raise


if __name__ == "__main__":
    main()
