#!/usr/bin/env python3
"""
CSV-based Portals Affiliate Fee Listener
Detects ShapeShift affiliate fees from Portals transactions across multiple chains.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via Alchemy RPC providers
2. Monitors Portals router contracts for transaction events
3. Filters for ShapeShift affiliate address involvement
4. Extracts input/output token data and affiliate fee information
5. Saves everything to CSV files for easy analysis

Portals is a cross-chain bridge and swap protocol that allows users to
transfer assets between different blockchains with affiliate fee support.
"""

import os
import csv
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from web3 import Web3
from eth_abi import decode
import pandas as pd

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CSVPortalsListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Get Alchemy API key from environment
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")

        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in environment variables")

        # Initialize CSV structure
        self.init_csv_structure()

        # ShapeShift affiliate addresses by chain
        # These addresses receive affiliate fees from Portals transactions
        # Each chain has its own affiliate address for ShapeShift
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum Mainnet
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon PoS
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum One
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
        }

        # Chain configurations with Alchemy RPC URLs and Portals router addresses
        # Each chain has its own Portals router contract and optimal scanning settings
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 1,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",  # Portals router contract
                "start_block": 22700000,  # Approximate deployment block
                "chunk_size": 100,  # Blocks to scan per batch (smaller for Ethereum due to gas costs)
                "delay": 1.0,  # Seconds between RPC calls (rate limiting)
            },
            "polygon": {
                "name": "Polygon",
                "rpc_url": f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 137,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 45000000,
                "chunk_size": 200,  # Larger chunks for L2s
                "delay": 0.5,  # Faster processing for L2s
            },
            "arbitrum": {
                "name": "Arbitrum",
                "rpc_url": f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 42161,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 70000000,
                "chunk_size": 200,
                "delay": 0.5,
            },
            "optimism": {
                "name": "Optimism",
                "rpc_url": f"https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 10,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 85000000,
                "chunk_size": 200,
                "delay": 0.5,
            },
            "base": {
                "name": "Base",
                "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 8453,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 5000000,
                "chunk_size": 200,
                "delay": 0.5,
            },
        }

    def init_csv_structure(self):
        """Initialize CSV file structure for Portals data"""
        os.makedirs(self.csv_dir, exist_ok=True)

        # Main Portals transactions CSV
        portals_csv = os.path.join(self.csv_dir, "portals_transactions.csv")

        # Create CSV with headers if it doesn't exist
        if not os.path.exists(portals_csv):
            headers = [
                "chain",
                "tx_hash",
                "block_number",
                "block_timestamp",
                "block_date",
                "input_token",
                "input_amount",
                "output_token",
                "output_amount",
                "sender",
                "broadcaster",
                "recipient",
                "partner",
                "affiliate_token",
                "affiliate_amount",
                "affiliate_fee_usd",
                "volume_usd",
                "created_at",
                "created_date",
            ]

            with open(portals_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created Portals CSV file: {portals_csv}")

        # Block tracker CSV for Portals
        block_tracker_csv = os.path.join(self.csv_dir, "portals_block_tracker.csv")
        if not os.path.exists(block_tracker_csv):
            headers = [
                "chain",
                "last_processed_block",
                "last_processed_date",
                "total_blocks_processed",
            ]
            with open(block_tracker_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created Portals block tracker CSV: {block_tracker_csv}")

    def get_web3_connection(self, chain_config: Dict) -> Optional[Web3]:
        """
        Get Web3 connection for a specific chain

        Args:
            chain_config: Chain configuration dictionary

        Returns:
            Web3 connection object or None if connection fails
        """
        try:
            w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
            if w3.is_connected():
                logger.info(f"✅ Connected to {chain_config['name']}")
                return w3
            else:
                logger.error(f"❌ Failed to connect to {chain_config['name']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error connecting to {chain_config['name']}: {e}")
            return None

    def check_affiliate_involvement(
        self, receipt: Dict, affiliate_address: str
    ) -> bool:
        """
        Check if a Portals transaction involves the ShapeShift affiliate address

        Args:
            receipt: Transaction receipt from blockchain
            affiliate_address: ShapeShift affiliate address to check for

        Returns:
            True if affiliate is involved, False otherwise
        """
        try:
            # Remove 0x prefix and convert to lowercase for comparison
            # This makes the comparison more robust against case differences
            affiliate_clean = affiliate_address.lower().replace("0x", "")

            # Check all transaction logs for affiliate address
            for log in receipt["logs"]:
                if log["topics"]:
                    for topic in log["topics"]:
                        topic_hex = topic.hex().lower()
                        # Check if the affiliate address (without 0x) is in the topic
                        if affiliate_clean in topic_hex:
                            logger.info(
                                f"   ✅ Found ShapeShift affiliate in topic: {topic.hex()}"
                            )
                            return True

            return False

        except Exception as e:
            logger.error(f"Error checking affiliate involvement: {e}")
            return False

    def detect_portals_tokens(
        self, w3: Web3, receipt: Dict, chain_config: Dict
    ) -> Dict:
        """
        Detect input, output, and affiliate tokens in Portals transactions

        Args:
            w3: Web3 connection object
            receipt: Transaction receipt from blockchain
            chain_config: Chain configuration dictionary

        Returns:
            Dictionary with token information (input, output, affiliate tokens and amounts)
        """
        result = {
            "input_token": None,
            "output_token": None,
            "affiliate_token": None,
            "input_amount": None,
            "output_amount": None,
            "affiliate_amount": None,
        }

        # Get ShapeShift affiliate address for this chain
        shapeshift_affiliate = self.shapeshift_affiliates.get(chain_config["chain_id"])

        # ERC-20 Transfer event signature (keccak256 hash of Transfer(address,address,uint256))
        # This is the standard event emitted when ERC-20 tokens are transferred
        transfer_topic = (
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        # Track all transfers in the transaction
        transfers = []
        affiliate_transfers = []

        for log in receipt["logs"]:
            if not log["topics"] or len(log["topics"]) < 3:
                continue

            # Check if this is an ERC-20 transfer event
            if log["topics"][0].hex() == transfer_topic:
                # Extract from and to addresses from topics
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()

                # Decode amount from log data
                amount = 0
                if len(log["data"]) >= 32:
                    try:
                        amount = int.from_bytes(log["data"][:32], "big")
                    except:
                        pass

                # Create transfer record
                transfer = {
                    "token": log["address"],  # Token contract address
                    "from": from_addr,  # Sender address
                    "to": to_addr,  # Recipient address
                    "amount": amount,  # Transfer amount
                }
                transfers.append(transfer)

                # Check if this transfer involves ShapeShift affiliate
                if (
                    from_addr.lower() == shapeshift_affiliate.lower()
                    or to_addr.lower() == shapeshift_affiliate.lower()
                ):
                    affiliate_transfers.append(transfer)

        # Determine input/output tokens based on transfer patterns
        # Usually the first transfer is input, last is output
        if len(transfers) >= 2:
            result["input_token"] = transfers[0]["token"]
            result["input_amount"] = str(transfers[0]["amount"])
            result["output_token"] = transfers[-1]["token"]
            result["output_amount"] = str(transfers[-1]["amount"])

        # Set affiliate token and amount
        if affiliate_transfers:
            # Take the first affiliate transfer (there might be multiple)
            affiliate_transfer = affiliate_transfers[0]
            result["affiliate_token"] = affiliate_transfer["token"]
            result["affiliate_amount"] = str(affiliate_transfer["amount"])

        return result

    def fetch_portals_events(
        self, chain_name: str, blocks_to_scan: int = 1000
    ) -> List[Dict]:
        """
        Fetch Portals events for a specific chain

        Args:
            chain_name: Name of the chain to scan
            blocks_to_scan: Number of blocks to scan

        Returns:
            List of Portals events with affiliate information
        """
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)

        if not w3:
            return []

        try:
            latest_block = w3.eth.block_number
            start_block = max(
                chain_config["start_block"], latest_block - blocks_to_scan
            )

            logger.info(
                f"🔍 Scanning {chain_config['name']} blocks {start_block} to {latest_block}"
            )

            events = []
            current_block = start_block
            chunk_size = chain_config["chunk_size"]

            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)

                try:
                    # Get all logs from Portals router contract
                    # No topic filter to catch all events (we'll filter them later)
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "address": chain_config["portals_router"],
                    }

                    logs = w3.eth.get_logs(filter_params)

                    for log in logs:
                        # Check if this involves ShapeShift affiliate
                        tx_receipt = w3.eth.get_transaction_receipt(
                            log["transactionHash"]
                        )
                        shapeshift_affiliate = self.shapeshift_affiliates.get(
                            chain_config["chain_id"]
                        )

                        # Use the improved affiliate detection
                        affiliate_involved = self.check_affiliate_involvement(
                            tx_receipt, shapeshift_affiliate
                        )

                        if affiliate_involved:
                            # Get block info for timestamp
                            block = w3.eth.get_block(log["blockNumber"])

                            # Detect tokens and amounts
                            token_info = self.detect_portals_tokens(
                                w3, tx_receipt, chain_config
                            )

                            # Create comprehensive event record
                            event_data = {
                                "chain": chain_config["name"],
                                "tx_hash": log["transactionHash"].hex(),
                                "block_number": log["blockNumber"],
                                "block_timestamp": block["timestamp"],
                                "block_date": datetime.fromtimestamp(
                                    block["timestamp"]
                                ).strftime("%Y-%m-%d %H:%M:%S"),
                                "input_token": token_info["input_token"],
                                "input_amount": token_info["input_amount"],
                                "output_token": token_info["output_token"],
                                "output_amount": token_info["output_amount"],
                                "sender": None,  # Will be extracted later if needed
                                "broadcaster": None,  # Portals-specific field
                                "recipient": None,  # Will be extracted later if needed
                                "partner": shapeshift_affiliate,  # ShapeShift affiliate address
                                "affiliate_token": token_info["affiliate_token"],
                                "affiliate_amount": token_info["affiliate_amount"],
                                "affiliate_fee_usd": 0.0,  # Will be calculated later
                                "volume_usd": 0.0,  # Will be calculated later
                                "created_at": int(time.time()),
                                "created_date": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }

                            events.append(event_data)
                            logger.info(
                                f"   ✅ Found ShapeShift affiliate event: {log['transactionHash'].hex()}"
                            )

                    # Progress logging
                    if current_block % 10000 == 0:
                        logger.info(
                            f"   📊 Processed {current_block - start_block} blocks..."
                        )

                    current_block = end_block + 1
                    time.sleep(chain_config["delay"])  # Rate limiting

                except Exception as e:
                    logger.error(
                        f"Error fetching logs for blocks {current_block}-{end_block}: {e}"
                    )
                    current_block = end_block + 1
                    continue

            return events

        except Exception as e:
            logger.error(f"Error fetching Portals events for {chain_name}: {e}")
            return []

    def save_events_to_csv(self, events: List[Dict]):
        """
        Save Portals events to CSV file

        Args:
            events: List of event dictionaries to save
        """
        if not events:
            return

        csv_file = os.path.join(self.csv_dir, "portals_transactions.csv")

        # Append new events to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())

            for event in events:
                try:
                    writer.writerow(event)
                except Exception as e:
                    logger.error(f"Error saving event {event['tx_hash']}: {e}")

        logger.info(f"💾 Saved {len(events)} Portals events to CSV: {csv_file}")

    def update_block_tracker(self, chain_name: str, last_block: int):
        """
        Update block tracker CSV for Portals

        Args:
            chain_name: Name of the chain
            last_block: Last processed block number
        """
        csv_file = os.path.join(self.csv_dir, "portals_block_tracker.csv")

        # Read existing data
        existing_data = []
        if os.path.exists(csv_file):
            with open(csv_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_data = list(reader)

        # Update or add entry for this chain
        updated = False
        for row in existing_data:
            if row["chain"] == chain_name:
                row["last_processed_block"] = str(last_block)
                row["last_processed_date"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                row["total_blocks_processed"] = str(
                    int(row.get("total_blocks_processed", 0)) + 1000
                )
                updated = True
                break

        if not updated:
            existing_data.append(
                {
                    "chain": chain_name,
                    "last_processed_block": str(last_block),
                    "last_processed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_blocks_processed": "1000",
                }
            )

        # Write back to CSV
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            if existing_data:
                writer = csv.DictWriter(f, fieldnames=existing_data[0].keys())
                writer.writeheader()
                writer.writerows(existing_data)

    def get_csv_stats(self):
        """Get CSV statistics for Portals data"""
        csv_file = os.path.join(self.csv_dir, "portals_transactions.csv")

        if not os.path.exists(csv_file):
            print("No Portals CSV file found")
            return

        try:
            df = pd.read_csv(csv_file)

            print(f"\n📊 Portals CSV Statistics:")
            print(f"   Total transactions: {len(df)}")
            print(f"   Unique chains: {df['chain'].nunique()}")
            print(
                f"   Date range: {df['block_date'].min()} to {df['block_date'].max()}"
            )

            # Show recent transactions
            if len(df) > 0:
                print(f"\n🔍 Recent Portals Transactions:")
                recent = df.sort_values("block_timestamp", ascending=False).head(3)
                for _, row in recent.iterrows():
                    print(
                        f"   {row['chain']}: {row['tx_hash'][:10]}... - {row['block_date']}"
                    )

        except Exception as e:
            print(f"Error reading Portals CSV: {e}")

    def run_listener(self, blocks_to_scan: int = 1000):
        """
        Run the Portals listener for all chains

        Args:
            blocks_to_scan: Number of blocks to scan per chain
        """
        logger.info("🚀 Starting CSV-based Portals affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_portals_events(chain_name, blocks_to_scan)
            self.save_events_to_csv(events)

            # Update block tracker
            if events:
                last_block = max(event["block_number"] for event in events)
                self.update_block_tracker(chain_name, last_block)

            total_events += len(events)

        logger.info(
            f"\n✅ Portals listener completed! Found {total_events} total events"
        )
        self.get_csv_stats()


def main():
    """Main function to run the Portals listener"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV-based Portals Affiliate Fee Listener"
    )
    parser.add_argument(
        "--blocks", type=int, default=1000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    try:
        listener = CSVPortalsListener()
        listener.run_listener(args.blocks)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
