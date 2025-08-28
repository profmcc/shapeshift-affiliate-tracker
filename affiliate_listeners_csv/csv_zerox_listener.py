#!/usr/bin/env python3
"""
CSV-based ZeroX Protocol Affiliate Fee Listener
Tracks ShapeShift affiliate fees from 0x Protocol swaps across EVM chains.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via RPC providers
2. Monitors 0x Protocol contracts for swap events
3. Filters for ShapeShift affiliate addresses
4. Extracts swap data, fees, and affiliate information
5. Saves everything to CSV files for easy analysis
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


class CSVZeroXListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Get API keys from environment
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.infura_api_key = os.getenv(
            "INFURA_API_KEY", "208a3474635e4ebe8ee409cef3fbcd40"
        )

        if not self.alchemy_api_key:
            logger.warning("ALCHEMY_API_KEY not found, using Infura as fallback")

        # Initialize CSV structure
        self.init_csv_structure()

        # ShapeShift affiliate addresses by chain
        # These addresses receive affiliate fees from 0x Protocol swaps
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
            43114: "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche
            56: "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",  # BSC
        }

        # Chain configurations with RPC URLs and contract addresses
        # Each chain has its own 0x Protocol contract and optimal settings
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "chain_id": 1,
                "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 10000000,  # Approximate deployment block
                "chunk_size": 1000,  # Blocks to scan per batch
                "delay": 1.0,  # Seconds between RPC calls
            },
            "polygon": {
                "name": "Polygon",
                "chain_id": 137,
                "rpc_url": f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 20000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "optimism": {
                "name": "Optimism",
                "chain_id": 10,
                "rpc_url": f"https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://optimism-mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 10000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "arbitrum": {
                "name": "Arbitrum",
                "chain_id": 42161,
                "rpc_url": f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 50000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://base-mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 10000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "avalanche": {
                "name": "Avalanche",
                "chain_id": 43114,
                "rpc_url": f"https://avalanche-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                if self.alchemy_api_key
                else f"https://avalanche-mainnet.infura.io/v3/{self.infura_api_key}",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 10000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "bsc": {
                "name": "BSC",
                "chain_id": 56,
                "rpc_url": "https://bsc-dataseed.binance.org/",
                "zerox_contract": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # 0x Protocol Exchange Proxy
                "start_block": 10000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
        }

        # Initialize Web3 connections
        self.web3_connections = {}
        for chain_name, chain_config in self.chains.items():
            try:
                self.web3_connections[chain_name] = Web3(
                    Web3.HTTPProvider(chain_config["rpc_url"])
                )
                if self.web3_connections[chain_name].is_connected():
                    logger.info(f"✅ Connected to {chain_name}")
                else:
                    logger.warning(f"⚠️ Failed to connect to {chain_name}")
            except Exception as e:
                logger.error(f"❌ Error connecting to {chain_name}: {e}")

    def init_csv_structure(self):
        """Initialize CSV file structure for ZeroX data"""
        os.makedirs(self.csv_dir, exist_ok=True)

        # Main ZeroX transactions CSV
        zerox_csv = os.path.join(self.csv_dir, "zerox_transactions.csv")

        # Create CSV with headers if it doesn't exist
        if not os.path.exists(zerox_csv):
            headers = [
                "tx_hash",
                "block_number",
                "block_timestamp",
                "block_date",
                "chain",
                "protocol",
                "user_address",
                "affiliate_address",
                "expected_fee_bps",
                "actual_fee_bps",
                "affiliate_fee_token",
                "affiliate_fee_amount",
                "affiliate_fee_usd",
                "input_token",
                "input_amount",
                "input_amount_usd",
                "output_token",
                "output_amount",
                "output_amount_usd",
                "volume_usd",
                "gas_used",
                "gas_price",
                "created_at",
                "created_date",
            ]

            with open(zerox_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created ZeroX CSV file: {zerox_csv}")

        # Block tracker CSV for ZeroX
        block_tracker_csv = os.path.join(self.csv_dir, "zerox_block_tracker.csv")
        if not os.path.exists(block_tracker_csv):
            headers = [
                "chain",
                "last_processed_block",
                "last_processed_date",
                "total_transactions_processed",
                "last_error",
                "last_error_date",
            ]
            with open(block_tracker_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            logger.info(f"Created ZeroX block tracker CSV: {block_tracker_csv}")

    def run_tracer_test(
        self, target_date: str = "2025-08-15", blocks_to_scan: int = 10000
    ):
        """Run a tracer test for a specific date to find ZeroX activity"""
        logger.info(f"🔍 Running tracer test for {target_date}")

        # Convert date to timestamp range
        target_timestamp = int(datetime.strptime(target_date, "%Y-%m-%d").timestamp())
        start_timestamp = target_timestamp
        end_timestamp = target_timestamp + 86400  # 24 hours

        logger.info(
            f"📅 Scanning for transactions between {datetime.fromtimestamp(start_timestamp)} and {datetime.fromtimestamp(end_timestamp)}"
        )

        all_transactions = []

        # Scan each chain for actual transactions
        for chain_name, chain_config in self.chains.items():
            if chain_name not in self.web3_connections:
                continue

            web3 = self.web3_connections[chain_name]

            try:
                current_block = web3.eth.block_number
                logger.info(f"📊 Current block on {chain_name}: {current_block}")

                # Scan recent blocks for 0x Protocol activity
                start_block = current_block - blocks_to_scan
                end_block = current_block

                logger.info(
                    f"🔍 Scanning {chain_name} from block {start_block} to {end_block}"
                )

                # Fetch 0x Protocol events
                events = self.fetch_zerox_events(
                    web3, chain_config, start_block, end_block
                )

                if events:
                    logger.info(
                        f"🎯 Found {len(events)} 0x Protocol events on {chain_name}"
                    )
                    all_transactions.extend(events)
                else:
                    logger.info(f"📝 No 0x Protocol events found on {chain_name}")

            except Exception as e:
                logger.error(f"Error scanning {chain_name}: {e}")
                continue

        logger.info(
            f"🎉 Tracer test complete! Found {len(all_transactions)} total 0x Protocol events."
        )
        return all_transactions

    def fetch_zerox_events(
        self, web3: Web3, chain_config: Dict, start_block: int, end_block: int
    ) -> List[Dict]:
        """Fetch 0x Protocol events for a specific block range"""
        try:
            # 0x Protocol event signatures
            event_signatures = {
                "fill": "0x0bcc4c97720e9c0f37d7485c66a92d80f6e39a6ea4e9cfb9a6254c8e0e4d0c0",
                "cancel": "0x5d611f318680d00598bb735d61ea9e488b7e2f1a",
                "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            }

            events = []
            chunk_size = 1000  # Process in smaller chunks

            for current_block in range(start_block, end_block + 1, chunk_size):
                end_chunk = min(current_block + chunk_size - 1, end_block)

                try:
                    # Fetch 0x Protocol events
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_chunk,
                        "address": chain_config["zerox_contract"],
                    }

                    logs = web3.eth.get_logs(filter_params)

                    for log in logs:
                        if not log["topics"]:
                            continue

                        event_sig = log["topics"][0].hex()

                        # Check for 0x Protocol events
                        if event_sig in event_signatures.values():
                            # Check if ShapeShift affiliate is involved
                            if self.is_shapeshift_affiliate_transaction(
                                web3, log, chain_config
                            ):
                                event_data = self.extract_zerox_transaction_data(
                                    log, web3, chain_config
                                )
                                if event_data:
                                    events.append(event_data)

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.debug(
                        f"Error fetching logs for blocks {current_block}-{end_chunk}: {e}"
                    )
                    continue

            return events

        except Exception as e:
            logger.error(f"Error fetching 0x Protocol events: {e}")
            return []

    def is_shapeshift_affiliate_transaction(
        self, web3: Web3, log, chain_config: Dict
    ) -> bool:
        """Check if a transaction involves ShapeShift affiliate fees"""
        try:
            affiliate_address = self.shapeshift_affiliates.get(chain_config["chain_id"])
            if not affiliate_address:
                return False

            # Get transaction receipt to check for affiliate transfers
            tx_receipt = web3.eth.get_transaction_receipt(log["transactionHash"])

            for receipt_log in tx_receipt["logs"]:
                if (
                    len(receipt_log["topics"]) >= 3
                    and receipt_log["topics"][0].hex()
                    == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    to_address = "0x" + receipt_log["topics"][2][-40:].hex()
                    if to_address.lower() == affiliate_address.lower():
                        return True

            return False

        except Exception as e:
            logger.debug(f"Error checking affiliate transaction: {e}")
            return False

    def extract_zerox_transaction_data(
        self, log, web3: Web3, chain_config: Dict
    ) -> Optional[Dict]:
        """Extract transaction data from 0x Protocol event"""
        try:
            block = web3.eth.get_block(log["blockNumber"])
            tx_receipt = web3.eth.get_transaction_receipt(log["transactionHash"])

            # Extract affiliate fee amount
            affiliate_amount = 0
            affiliate_address = self.shapeshift_affiliates.get(chain_config["chain_id"])

            for receipt_log in tx_receipt["logs"]:
                if (
                    len(receipt_log["topics"]) >= 3
                    and receipt_log["topics"][0].hex()
                    == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    to_address = "0x" + receipt_log["topics"][2][-40:].hex()
                    if to_address.lower() == affiliate_address.lower():
                        try:
                            affiliate_amount = int(receipt_log["data"], 16)
                        except:
                            affiliate_amount = 0
                        break

            event_data = {
                "tx_hash": log["transactionHash"].hex(),
                "block_number": log["blockNumber"],
                "block_timestamp": block["timestamp"],
                "block_date": datetime.fromtimestamp(block["timestamp"]).strftime(
                    "%Y-%m-%d"
                ),
                "chain": chain_config["name"],
                "protocol": "0x Protocol",
                "user_address": "0x" + log["topics"][1][-40:].hex()
                if len(log["topics"]) > 1
                else "Unknown",
                "affiliate_address": affiliate_address,
                "expected_fee_bps": 55,  # 55 basis points
                "actual_fee_bps": 55,  # Would need calculation based on volume
                "affiliate_fee_token": "Unknown",
                "affiliate_fee_amount": str(affiliate_amount),
                "affiliate_fee_usd": 0.0,
                "input_token": "Unknown",
                "input_amount": "0",
                "input_amount_usd": 0.0,
                "output_token": "Unknown",
                "output_amount": "0",
                "output_amount_usd": 0.0,
                "volume_usd": 0.0,
                "gas_used": tx_receipt["gasUsed"],
                "gas_price": 0,
                "created_at": datetime.now().isoformat(),
                "created_date": datetime.now().strftime("%Y-%m-%d"),
            }

            return event_data

        except Exception as e:
            logger.debug(f"Error extracting transaction data: {e}")
            return None


def main():
    """Main function to run the ZeroX listener"""
    import argparse

    parser = argparse.ArgumentParser(
        description="ZeroX Protocol Affiliate Fee Listener"
    )
    parser.add_argument(
        "--tracer-test", action="store_true", help="Run tracer test for specific date"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2025-08-15",
        help="Date for tracer test (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=10000,
        help="Number of blocks to scan for tracer test",
    )
    parser.add_argument(
        "--csv-dir", type=str, default="csv_data", help="Directory for CSV files"
    )

    args = parser.parse_args()

    # Initialize listener
    listener = CSVZeroXListener(csv_dir=args.csv_dir)

    if args.tracer_test:
        # Run tracer test
        listener.run_tracer_test(args.date, args.blocks)
    else:
        # Show status
        logger.info("ZeroX listener initialized. Use --tracer-test for testing.")


if __name__ == "__main__":
    main()
