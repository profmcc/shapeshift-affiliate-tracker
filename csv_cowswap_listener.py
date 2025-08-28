#!/usr/bin/env python3
"""
CSV-based CoW Swap Affiliate Fee Listener
Tracks ShapeShift affiliate fees from CoW Swap trades across EVM chains.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via RPC providers
2. Monitors CoW Swap contracts for trade events
3. Filters for ShapeShift affiliate addresses
4. Extracts trade data, fees, and affiliate information
5. Saves everything to CSV files for easy analysis

CoW Swap (Coincidence of Wants) is a DEX aggregator that finds the best prices
across multiple DEXs and executes trades with MEV protection.
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

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CSVCowSwapListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Get API keys from environment
        # Temporarily disable Alchemy to test Infura fallback
        self.alchemy_api_key = None  # os.getenv('ALCHEMY_API_KEY')
        self.infura_api_key = os.getenv(
            "INFURA_API_KEY", "208a3474635e4ebe8ee409cef3fbcd40"
        )

        if self.alchemy_api_key:
            logger.info(
                "🔧 Alchemy API key found - will try Alchemy first, fallback to Infura"
            )
        else:
            logger.info("🔧 No Alchemy API key - using Infura only")

        # Initialize CSV structure
        self.init_csv_structure()

        # ShapeShift affiliate addresses by chain
        # These addresses receive affiliate fees from CoW Swap trades
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
        }

        # Chain configurations will be set up after methods are defined
        self.chains = {}

        # Set up chains after all methods are available
        logger.info("🔧 About to call _setup_chains")
        self._setup_chains()
        logger.info("🔧 Finished calling _setup_chains")

        # CoW Swap event signatures (keccak256 hashes of event signatures)
        # These identify specific events we want to monitor
        self.event_signatures = {
            "trade": "0xa07a543ab8a018198e99ca0184c93fe9050a79400a0a723441f84de1d972cc17",  # Trade event
            "order": "0xed99827efb37016f2275f98c4bcf71c7551c75d59e9b450f79fa32e60be672c2",  # Order event
            "invalidation": "0x40338ce1a7c49204f0099533b1e9a7ee0a3d261f84974ab7af36105b8c4e9db4",  # Order invalidation
            "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # ERC-20 transfer
        }

        # Token metadata cache to avoid repeated lookups
        self.token_cache = {}

    def _get_rpc_url(self, chain_name: str) -> str:
        """Get RPC URL for a specific chain - using Infura"""
        logger.info(f"🔧 Getting RPC URL for {chain_name} (Infura)")
        if chain_name == "ethereum":
            return f"https://mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain_name == "polygon":
            return f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain_name == "optimism":
            return f"https://optimism-mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain_name == "arbitrum":
            return f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain_name == "base":
            return f"https://base-mainnet.infura.io/v3/{self.infura_api_key}"

        # Fallback to Ethereum Infura
        return f"https://mainnet.infura.io/v3/{self.infura_api_key}"

    def _setup_chains(self):
        """Set up chain configurations with dynamic RPC URLs"""
        logger.info("🔧 Setting up chains with Infura RPC URLs")
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "chain_id": 1,
                "rpc_url": self._get_rpc_url("ethereum"),
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",  # CoW Swap settlement contract
                "start_block": 15000000,  # Approximate deployment block
                "chunk_size": 1000,  # Blocks to scan per batch
                "delay": 1.0,  # Seconds between RPC calls
            },
            "polygon": {
                "name": "Polygon",
                "chain_id": 137,
                "rpc_url": self._get_rpc_url("polygon"),
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "start_block": 25000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "optimism": {
                "name": "Optimism",
                "chain_id": 10,
                "rpc_url": self._get_rpc_url("optimism"),
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "start_block": 10000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "arbitrum": {
                "name": "Arbitrum",
                "chain_id": 42161,
                "rpc_url": self._get_rpc_url("arbitrum"),
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "start_block": 50000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": self._get_rpc_url("base"),
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "start_block": 1000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
        }

    def init_csv_structure(self):
        """Initialize CSV file structure for CoW Swap data"""
        os.makedirs(self.csv_dir, exist_ok=True)

        # Main CoW Swap transactions CSV
        cowswap_csv = os.path.join(self.csv_dir, "cowswap_transactions.csv")

        # Create CSV with headers if it doesn't exist
        if not os.path.exists(cowswap_csv):
            headers = [
                "chain",
                "tx_hash",
                "block_number",
                "block_timestamp",
                "block_time",
                "event_type",
                "owner",
                "trader",
                "sell_token",
                "buy_token",
                "sell_amount",
                "buy_amount",
                "fee_amount",
                "units_sold",
                "units_bought",
                "usd_value",
                "order_uid",
                "app_code",
                "app_data",
                "sell_token_name",
                "buy_token_name",
                "affiliate_fee_usd",
                "volume_usd",
                "affiliate_address",
                "affiliate_involved",
                "created_at",
                "created_date",
            ]

            with open(cowswap_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created CoW Swap CSV file: {cowswap_csv}")

        # Block tracker CSV for CoW Swap
        block_tracker_csv = os.path.join(self.csv_dir, "cowswap_block_tracker.csv")
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

            logger.info(f"Created CoW Swap block tracker CSV: {block_tracker_csv}")

    def get_web3_connection(self, chain_config: Dict) -> Optional[Web3]:
        """
        Get Web3 connection for a specific chain with fallback support

        Args:
            chain_config: Chain configuration dictionary

        Returns:
            Web3 connection object or None if connection fails
        """
        chain_name = chain_config["name"]

        # Try multiple RPC providers in order
        rpc_providers = [
            {"name": "Alchemy", "url": self._get_alchemy_url(chain_config["chain_id"])},
            {"name": "Infura", "url": self._get_infura_url(chain_config["chain_id"])},
        ]

        for provider in rpc_providers:
            if not provider["url"]:
                continue

            try:
                logger.info(f"🔗 Trying {provider['name']} for {chain_name}...")
                w3 = Web3(Web3.HTTPProvider(provider["url"]))

                if w3.is_connected():
                    logger.info(f"✅ Connected to {chain_name} via {provider['name']}")
                    return w3
                else:
                    logger.warning(
                        f"⚠️ Failed to connect to {chain_name} via {provider['name']}"
                    )

            except Exception as e:
                logger.warning(
                    f"⚠️ Error connecting to {chain_name} via {provider['name']}: {e}"
                )
                continue

        logger.error(f"❌ Failed to connect to {chain_name} with all providers")
        return None

    def _get_alchemy_url(self, chain_id: int) -> Optional[str]:
        """Get Alchemy RPC URL for a chain"""
        if not self.alchemy_api_key:
            return None

        alchemy_urls = {
            1: f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            137: f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            10: f"https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            42161: f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            8453: f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
        }

        return alchemy_urls.get(chain_id)

    def _get_infura_url(self, chain_id: int) -> str:
        """Get Infura RPC URL for a chain"""
        infura_urls = {
            1: f"https://mainnet.infura.io/v3/{self.infura_api_key}",
            137: f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}",
            10: f"https://optimism-mainnet.infura.io/v3/{self.infura_api_key}",
            42161: f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}",
            8453: f"https://base-mainnet.infura.io/v3/{self.infura_api_key}",
        }

        return infura_urls.get(
            chain_id, f"https://mainnet.infura.io/v3/{self.infura_api_key}"
        )

    def _get_logs_with_fallback(
        self, w3: Web3, filter_params: Dict, chain_config: Dict
    ) -> List:
        """Get logs with automatic fallback to different RPC providers"""
        # Try the current Web3 connection first
        try:
            return w3.eth.get_logs(filter_params)
        except Exception as e:
            if "400" in str(e) or "rate limit" in str(e).lower():
                logger.warning(
                    f"⚠️ Primary RPC failed ({str(e)[:100]}...), trying fallback..."
                )

                # Try Infura as fallback
                infura_url = self._get_infura_url(chain_config["chain_id"])
                try:
                    backup_w3 = Web3(Web3.HTTPProvider(infura_url))
                    if backup_w3.is_connected():
                        logger.info(
                            f"✅ Connected to {chain_config['name']} via Infura fallback"
                        )
                        return backup_w3.eth.get_logs(filter_params)
                except Exception as backup_e:
                    logger.error(f"❌ Infura fallback also failed: {backup_e}")

            # If all else fails, re-raise the original exception
            raise e

    def check_affiliate_involvement(
        self, receipt: Dict, affiliate_address: str
    ) -> bool:
        """
        Check if a CoW Swap transaction involves the ShapeShift affiliate address

        Args:
            receipt: Transaction receipt from blockchain
            affiliate_address: ShapeShift affiliate address to check for

        Returns:
            True if affiliate is involved, False otherwise
        """
        try:
            # Remove 0x prefix and convert to lowercase for comparison
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

                        # Also check the log data for affiliate address
                        if log["data"] and affiliate_clean in log["data"].hex().lower():
                            logger.info(f"   ✅ Found ShapeShift affiliate in log data")
                            return True

            return False

        except Exception as e:
            logger.error(f"Error checking affiliate involvement: {e}")
            return False

    def decode_cowswap_event(self, log: Dict, w3: Web3) -> Optional[Dict]:
        """
        Decode a CoW Swap event log to extract trade information

        Args:
            log: Event log from blockchain
            w3: Web3 connection object

        Returns:
            Dictionary with decoded event data or None if decoding fails
        """
        try:
            # Get the event topic (first topic identifies the event type)
            if not log["topics"]:
                return None

            event_topic = log["topics"][0].hex()

            # Check if this is a trade event
            if event_topic == self.event_signatures["trade"]:
                # Decode trade event data
                # The trade event contains: owner, sellToken, buyToken, sellAmount, buyAmount, feeAmount
                if len(log["topics"]) >= 4 and len(log["data"]) >= 64:
                    owner = "0x" + log["topics"][1][-20:].hex()
                    sell_token = "0x" + log["topics"][2][-20:].hex()
                    buy_token = "0x" + log["topics"][3][-20:].hex()

                    # Decode amounts from data field
                    sell_amount = int.from_bytes(log["data"][:32], "big")
                    buy_amount = int.from_bytes(log["data"][32:64], "big")
                    fee_amount = int.from_bytes(log["data"][64:96], "big")

                    return {
                        "event_type": "trade",
                        "owner": owner,
                        "trader": owner,  # In CoW Swap, owner is usually the trader
                        "sell_token": sell_token,
                        "buy_token": buy_token,
                        "sell_amount": sell_amount,
                        "buy_amount": buy_amount,
                        "fee_amount": fee_amount,
                        "units_sold": sell_amount,
                        "units_bought": buy_amount,
                    }

            return None

        except Exception as e:
            logger.error(f"Error decoding CoW Swap event: {e}")
            return None

    def get_token_metadata(self, w3: Web3, token_address: str) -> Dict:
        """
        Get token metadata (name, symbol, decimals) for a given token address

        Args:
            w3: Web3 connection object
            token_address: Token contract address

        Returns:
            Dictionary with token metadata
        """
        # Check cache first
        if token_address in self.token_cache:
            return self.token_cache[token_address]

        try:
            # Basic ERC-20 ABI for name, symbol, decimals
            abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function",
                },
            ]

            contract = w3.eth.contract(address=token_address, abi=abi)

            # Get token info
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()

            metadata = {"name": name, "symbol": symbol, "decimals": decimals}

            # Cache the result
            self.token_cache[token_address] = metadata
            return metadata

        except Exception as e:
            logger.warning(f"Could not get metadata for token {token_address}: {e}")
            # Return default metadata
            return {"name": "Unknown", "symbol": "UNK", "decimals": 18}

    def fetch_cowswap_events(
        self, chain_name: str, blocks_to_scan: int = 1000
    ) -> List[Dict]:
        """
        Fetch CoW Swap events for a specific chain

        Args:
            chain_name: Name of the chain to scan
            blocks_to_scan: Number of blocks to scan

        Returns:
            List of CoW Swap events with affiliate information
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
                    # Get all logs from CoW Swap contract with fallback support
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "address": chain_config["cowswap_contract"],
                    }

                    logs = self._get_logs_with_fallback(w3, filter_params, chain_config)

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
                            # Get block info
                            block = w3.eth.get_block(log["blockNumber"])

                            # Decode the CoW Swap event
                            event_data = self.decode_cowswap_event(log, w3)

                            if event_data:
                                # Get token metadata
                                sell_token_meta = self.get_token_metadata(
                                    w3, event_data["sell_token"]
                                )
                                buy_token_meta = self.get_token_metadata(
                                    w3, event_data["buy_token"]
                                )

                                # Create comprehensive event record
                                event_record = {
                                    "chain": chain_config["name"],
                                    "tx_hash": log["transactionHash"].hex(),
                                    "block_number": log["blockNumber"],
                                    "block_timestamp": block["timestamp"],
                                    "block_time": datetime.fromtimestamp(
                                        block["timestamp"]
                                    ).strftime("%Y-%m-%d %H:%M:%S"),
                                    "event_type": event_data["event_type"],
                                    "owner": event_data["owner"],
                                    "trader": event_data["trader"],
                                    "sell_token": event_data["sell_token"],
                                    "buy_token": event_data["buy_token"],
                                    "sell_amount": event_data["sell_amount"],
                                    "buy_amount": event_data["buy_amount"],
                                    "fee_amount": event_data["fee_amount"],
                                    "units_sold": event_data["units_sold"],
                                    "units_bought": event_data["units_bought"],
                                    "usd_value": 0.0,  # Will be calculated later
                                    "order_uid": "",  # Not available in basic trade event
                                    "app_code": "cowswap",
                                    "app_data": "",
                                    "sell_token_name": sell_token_meta["symbol"],
                                    "buy_token_name": buy_token_meta["symbol"],
                                    "affiliate_fee_usd": 0.0,  # Will be calculated later
                                    "volume_usd": 0.0,  # Will be calculated later
                                    "affiliate_address": shapeshift_affiliate,
                                    "affiliate_involved": True,
                                    "created_at": int(time.time()),
                                    "created_date": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                }

                                events.append(event_record)
                                logger.info(
                                    f"   ✅ Found ShapeShift affiliate CoW Swap event: {log['transactionHash'].hex()}"
                                )

                    if current_block % 10000 == 0:
                        logger.info(
                            f"   📊 Processed {current_block - start_block} blocks..."
                        )

                    current_block = end_block + 1
                    time.sleep(chain_config["delay"])

                except Exception as e:
                    logger.error(
                        f"Error fetching logs for blocks {current_block}-{end_block}: {e}"
                    )
                    current_block = end_block + 1
                    continue

            return events

        except Exception as e:
            logger.error(f"Error fetching CoW Swap events for {chain_name}: {e}")
            return []

    def save_events_to_csv(self, events: List[Dict]):
        """
        Save CoW Swap events to CSV file

        Args:
            events: List of event dictionaries to save
        """
        if not events:
            return

        csv_file = os.path.join(self.csv_dir, "cowswap_transactions.csv")

        # Append new events to CSV
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())

            for event in events:
                try:
                    writer.writerow(event)
                except Exception as e:
                    logger.error(f"Error saving event {event['tx_hash']}: {e}")

        logger.info(f"💾 Saved {len(events)} CoW Swap events to CSV: {csv_file}")

    def update_block_tracker(self, chain_name: str, last_block: int):
        """
        Update block tracker CSV for CoW Swap

        Args:
            chain_name: Name of the chain
            last_block: Last processed block number
        """
        csv_file = os.path.join(self.csv_dir, "cowswap_block_tracker.csv")

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
        """Get CSV statistics for CoW Swap data"""
        csv_file = os.path.join(self.csv_dir, "cowswap_transactions.csv")

        if not os.path.exists(csv_file):
            print("No CoW Swap CSV file found")
            return

        try:
            import pandas as pd

            df = pd.read_csv(csv_file)

            print(f"\n📊 CoW Swap CSV Statistics:")
            print(f"   Total transactions: {len(df)}")
            print(f"   Unique chains: {df['chain'].nunique()}")
            print(
                f"   Date range: {df['block_time'].min()} to {df['block_time'].max()}"
            )
            print(f"   Total affiliate fees: ${df['affiliate_fee_usd'].sum():.2f}")
            print(f"   Total volume: ${df['volume_usd'].sum():.2f}")

            # Show recent transactions
            if len(df) > 0:
                print(f"\n🔍 Recent CoW Swap Transactions:")
                recent = df.sort_values("block_timestamp", ascending=False).head(3)
                for _, row in recent.iterrows():
                    print(
                        f"   {row['chain']}: {row['sell_token_name']} → {row['buy_token_name']} - {row['tx_hash'][:10]}..."
                    )

        except Exception as e:
            print(f"Error reading CoW Swap CSV: {e}")

    def run_listener(self, blocks_to_scan: int = 1000):
        """
        Run the CoW Swap listener for all chains

        Args:
            blocks_to_scan: Number of blocks to scan per chain
        """
        logger.info("🚀 Starting CSV-based CoW Swap affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_cowswap_events(chain_name, blocks_to_scan)
            self.save_events_to_csv(events)

            # Update block tracker
            if events:
                last_block = max(event["block_number"] for event in events)
                self.update_block_tracker(chain_name, last_block)

            total_events += len(events)

        logger.info(
            f"\n✅ CoW Swap listener completed! Found {total_events} total events"
        )
        self.get_csv_stats()


def main():
    """Main function to run the CoW Swap listener"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV-based CoW Swap Affiliate Fee Listener"
    )
    parser.add_argument(
        "--blocks", type=int, default=1000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    try:
        listener = CSVCowSwapListener()
        listener.run_listener(args.blocks)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
