#!/usr/bin/env python3
"""
CSV-Based Relay Listener - Monitor Relay transactions for ShapeShift affiliate fees
Uses centralized configuration for addresses and settings
"""

import os
import csv
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from web3 import Web3
from web3.exceptions import BlockNotFound, TransactionNotFound

# Import centralized configuration
from shared.config_loader import (
    get_config,
    get_shapeshift_address,
    get_contract_address,
    get_chain_config,
    get_storage_path,
    get_listener_config,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVRelayListener:
    """CSV-based listener for Relay transactions with ShapeShift affiliate fees"""

    def __init__(self):
        """Initialize the Relay listener with centralized configuration"""
        self.config = get_config()

        # Get API key from config
        self.alchemy_api_key = self.config.get_alchemy_api_key()
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in configuration")

        # Get ShapeShift affiliate addresses from config
        self.shapeshift_affiliates = self.config.get_all_shapeshift_addresses()
        if not self.shapeshift_affiliates:
            raise ValueError("No ShapeShift affiliate addresses found in configuration")

        logger.info(
            f"Loaded {len(self.shapeshift_affiliates)} ShapeShift affiliate addresses"
        )

        # Get storage paths from config
        self.csv_dir = self.config.get_storage_path("csv_directory")
        self.relay_csv = self.config.get_storage_path("file_pattern", "relay")
        self.block_tracker_csv = self.config.get_storage_path(
            "file_pattern", "block_tracker"
        ).format(protocol="relay")

        # Get listener configuration
        self.listener_config = self.config.get_listener_config("relay")
        self.chunk_size = self.listener_config.get("chunk_size", 100)
        self.delay = self.listener_config.get("delay", 0.5)
        self.max_blocks = self.listener_config.get("max_blocks", 1000)

        # Get event signatures from config
        self.affiliate_fee_event = self.config.get_event_signature(
            "relay", "affiliate_fee"
        )
        self.transfer_event = self.config.get_event_signature("relay", "transfer")

        # Get threshold from config
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")

        # Initialize Web3 connections for supported chains
        self.web3_connections = {}
        self._initialize_web3_connections()

        # Initialize CSV structure
        self.init_csv_structure()

        logger.info("CSVRelayListener initialized successfully")

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
                        self.web3_connections[chain_name] = {
                            "web3": w3,
                            "config": chain_config,
                            "router_address": self.config.get_contract_address(
                                "relay", chain_name
                            ),
                        }
                        logger.info(
                            f"Connected to {chain_name}: {chain_config['name']}"
                        )
                    else:
                        logger.warning(f"Failed to connect to {chain_name}")

            except Exception as e:
                logger.error(f"Error initializing {chain_name}: {e}")

        if not self.web3_connections:
            raise ValueError("No Web3 connections established")

        logger.info(f"Initialized {len(self.web3_connections)} chain connections")

    def init_csv_structure(self):
        """Initialize CSV file structure for Relay data"""
        os.makedirs(self.csv_dir, exist_ok=True)

        # Main Relay transactions CSV
        relay_csv_path = os.path.join(self.csv_dir, self.relay_csv)
        if not os.path.exists(relay_csv_path):
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
                "created_at",
            ]

            with open(relay_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created Relay transactions CSV: {relay_csv_path}")

        # Block tracker CSV for Relay
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)
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
            logger.info(f"Created Relay block tracker CSV: {block_tracker_path}")

    def get_last_processed_block(self, chain: str) -> int:
        """Get the last processed block for a specific chain"""
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)

        if not os.path.exists(block_tracker_path):
            return 0

        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["chain"] == chain:
                        return int(row["last_processed_block"])
        except Exception as e:
            logger.error(f"Error reading block tracker for {chain}: {e}")

        # Return start block from config if no tracker found
        chain_config = self.config.get_chain_config(chain)
        return chain_config.get("start_block", 0)

    def update_block_tracker(self, chain: str, block_number: int):
        """Update the block tracker with the latest processed block"""
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)

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

    def save_events_to_csv(self, events: List[Dict[str, Any]]):
        """Save affiliate events to CSV file"""
        if not events:
            return

        relay_csv_path = os.path.join(self.csv_dir, self.relay_csv)

        # Append new events
        with open(relay_csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())
            writer.writerows(events)

        logger.info(f"Saved {len(events)} Relay affiliate events to CSV")

    def process_chain(
        self, chain_name: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """Process a specific chain for Relay affiliate events"""
        if chain_name not in self.web3_connections:
            logger.warning(f"Chain {chain_name} not connected, skipping")
            return []

        connection = self.web3_connections[chain_name]
        w3 = connection["web3"]
        router_address = connection["router_address"]

        if not router_address:
            logger.warning(f"No router address configured for {chain_name}, skipping")
            return []

        logger.info(f"Processing {chain_name} from block {start_block} to {end_block}")

        events = []

        try:
            # Get logs from Relay router
            filter_params = {
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": router_address,
            }

            logs = w3.eth.get_logs(filter_params)
            logger.info(f"Found {len(logs)} logs on {chain_name}")

            for log in logs:
                try:
                    # Check if this log contains affiliate information
                    event = self._parse_relay_log(w3, log, chain_name)
                    if event:
                        events.append(event)

                except Exception as e:
                    logger.error(f"Error parsing log on {chain_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing {chain_name}: {e}")

        return events

    def _parse_relay_log(self, w3: Web3, log: Dict, chain_name: str) -> Dict[str, Any]:
        """Parse a Relay log entry for affiliate information"""
        try:
            tx_hash = log["transactionHash"].hex()
            block_number = log["blockNumber"]

            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            tx = w3.eth.get_transaction(tx_hash)

            # Check if any ShapeShift affiliate is involved
            affiliate_found = None
            for affiliate in self.shapeshift_affiliates:
                if self._check_affiliate_involvement(receipt, affiliate):
                    affiliate_found = affiliate
                    break

            if not affiliate_found:
                return None

            # Get block timestamp
            block = w3.eth.get_block(block_number)
            timestamp = block["timestamp"]

            # Create event record
            event = {
                "tx_hash": tx_hash,
                "chain": chain_name,
                "block_number": block_number,
                "timestamp": timestamp,
                "from_address": tx["from"],
                "to_address": tx["to"],
                "affiliate_address": affiliate_found,
                "affiliate_fee_amount": "0",  # Will need to parse from logs
                "affiliate_fee_token": "0x0000000000000000000000000000000000000000",
                "affiliate_fee_usd": "0",
                "volume_amount": "0",  # Will need to parse from logs
                "volume_token": "0x0000000000000000000000000000000000000000",
                "volume_usd": "0",
                "gas_used": receipt["gasUsed"],
                "gas_price": tx["gasPrice"],
                "created_at": int(time.time()),
            }

            # Try to extract volume and fee information
            self._extract_volume_and_fees(w3, receipt, event)

            return event

        except Exception as e:
            logger.error(f"Error parsing Relay log: {e}")
            return None

    def _check_affiliate_involvement(
        self, receipt: Dict, affiliate_address: str
    ) -> bool:
        """Check if a receipt contains affiliate involvement"""
        # Check if affiliate address appears in any log
        affiliate_lower = affiliate_address.lower()

        for log_entry in receipt["logs"]:
            # Check topics
            if log_entry["topics"]:
                for topic in log_entry["topics"]:
                    if affiliate_lower.replace("0x", "") in topic.hex().lower():
                        return True

            # Check data
            if log_entry["data"]:
                if affiliate_lower.replace("0x", "") in log_entry["data"].hex().lower():
                    return True

        return False

    def _extract_volume_and_fees(self, w3: Web3, receipt: Dict, event: Dict):
        """Extract volume and fee information from transaction receipt"""
        try:
            # Look for ERC-20 transfer events
            transfer_topic = self.transfer_event

            total_volume = 0
            affiliate_fee = 0

            for log_entry in receipt["logs"]:
                if (
                    log_entry["topics"]
                    and log_entry["topics"][0].hex() == transfer_topic
                ):
                    # This is a transfer event
                    if len(log_entry["data"]) >= 32:
                        amount_hex = log_entry["data"].hex()
                        amount = int(amount_hex, 16)

                        # Very rough USD estimation (would need price feeds for accuracy)
                        estimated_usd = amount / (10**18) * 50  # Rough estimate
                        total_volume += estimated_usd

            # Update event with extracted data
            event["volume_amount"] = str(total_volume)
            event["volume_usd"] = str(total_volume)
            event["affiliate_fee_amount"] = str(affiliate_fee)
            event["affiliate_fee_usd"] = str(affiliate_fee)

        except Exception as e:
            logger.error(f"Error extracting volume and fees: {e}")

    def run_listener(self, chains: List[str] = None, max_blocks: int = None):
        """Run the Relay listener for specified chains"""
        if chains is None:
            chains = list(self.web3_connections.keys())

        if max_blocks is None:
            max_blocks = self.max_blocks

        logger.info(f"Starting Relay listener for chains: {chains}")
        logger.info(f"Max blocks per scan: {max_blocks}")

        total_events = 0

        for chain_name in chains:
            if chain_name not in self.web3_connections:
                logger.warning(f"Skipping {chain_name} - not connected")
                continue

            try:
                # Get last processed block
                start_block = self.get_last_processed_block(chain_name)

                # Get current block
                w3 = self.web3_connections[chain_name]["web3"]
                current_block = w3.eth.block_number

                # Calculate end block
                end_block = min(start_block + max_blocks, current_block)

                if start_block >= end_block:
                    logger.info(f"{chain_name}: No new blocks to process")
                    continue

                logger.info(
                    f"{chain_name}: Processing blocks {start_block} to {end_block}"
                )

                # Process blocks in chunks
                for chunk_start in range(start_block, end_block, self.chunk_size):
                    chunk_end = min(chunk_start + self.chunk_size, end_block)

                    events = self.process_chain(chain_name, chunk_start, chunk_end)
                    if events:
                        self.save_events_to_csv(events)
                        total_events += len(events)

                    # Update block tracker
                    self.update_block_tracker(chain_name, chunk_end)

                    # Rate limiting
                    time.sleep(self.delay)

                logger.info(f"{chain_name}: Completed processing")

            except Exception as e:
                logger.error(f"Error processing {chain_name}: {e}")
                continue

        logger.info(f"Relay listener completed. Total events found: {total_events}")
        return total_events

    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the CSV data"""
        relay_csv_path = os.path.join(self.csv_dir, self.relay_csv)

        if not os.path.exists(relay_csv_path):
            return {"total_transactions": 0, "chains": {}}

        try:
            with open(relay_csv_path, "r", newline="", encoding="utf-8") as f:
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

                # Count by chain
                if chain not in stats["chains"]:
                    stats["chains"][chain] = 0
                stats["chains"][chain] += 1

                # Count by affiliate address
                if affiliate not in stats["affiliate_addresses"]:
                    stats["affiliate_addresses"][affiliate] = 0
                stats["affiliate_addresses"][affiliate] += 1

            return stats

        except Exception as e:
            logger.error(f"Error getting CSV stats: {e}")
            return {"total_transactions": 0, "chains": {}}


def main():
    """Main function to run the Relay listener"""
    try:
        listener = CSVRelayListener()

        # Run listener for all supported chains
        total_events = listener.run_listener()

        # Print statistics
        stats = listener.get_csv_stats()
        print(f"\n📊 Relay Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by chain:")
        for chain, count in stats["chains"].items():
            print(f"     {chain}: {count}")
        print(f"   Affiliate addresses found:")
        for addr, count in stats["affiliate_addresses"].items():
            print(f"     {addr}: {count}")

        print(f"\n✅ Relay listener completed successfully!")
        print(f"   Total events found: {total_events}")

    except Exception as e:
        logger.error(f"Error running Relay listener: {e}")
        raise


if __name__ == "__main__":
    main()
