#!/usr/bin/env python3
"""
CSV-based Portals Affiliate Fee Listener
Tracks ShapeShift affiliate fees from Portals cross-chain swaps.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via RPC providers
2. Monitors Portals router contracts for Portal events
3. Filters for ShapeShift affiliate address (0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be)
4. Extracts swap data, fees, and affiliate information
5. Saves everything to CSV files for easy analysis

Portals is a cross-chain DEX aggregator that enables swaps across different blockchains.
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


class CSVPortalsListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir

        # Get API keys from environment
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
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

        # ShapeShift affiliate address (confirmed from Etherscan transaction)
        self.shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

        # Chain configurations with RPC URLs and contract addresses
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "chain_id": 1,
                "rpc_url": self._get_rpc_url("ethereum"),
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",  # Portals.fi: Router
                "start_block": 18000000,  # Approximate deployment block
                "chunk_size": 1000,  # Blocks to scan per batch
                "delay": 1.0,  # Seconds between RPC calls
            },
            "polygon": {
                "name": "Polygon",
                "chain_id": 137,
                "rpc_url": self._get_rpc_url("polygon"),
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 50000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "optimism": {
                "name": "Optimism",
                "chain_id": 10,
                "rpc_url": self._get_rpc_url("optimism"),
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 30000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "arbitrum": {
                "name": "Arbitrum",
                "chain_id": 42161,
                "rpc_url": self._get_rpc_url("arbitrum"),
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 100000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": self._get_rpc_url("base"),
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 1000000,
                "chunk_size": 2000,
                "delay": 0.5,
            },
        }

        # Portals event signatures
        self.event_signatures = {
            "portal": "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03",  # Portal event
            "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # ERC-20 transfer
        }

        # Token metadata cache to avoid repeated lookups
        self.token_cache = {}

    def _get_rpc_url(self, chain_name: str) -> str:
        """Get RPC URL for a specific chain with fallback support"""
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
                "block_time",
                "event_type",
                "sender",
                "broadcaster",
                "recipient",
                "partner",
                "input_token",
                "input_amount",
                "input_amount_usd",
                "output_token",
                "output_amount",
                "output_amount_usd",
                "affiliate_fee_token",
                "affiliate_fee_amount",
                "affiliate_fee_usd",
                "volume_usd",
                "gas_used",
                "gas_price",
                "expected_fee_bps",
                "actual_fee_bps",
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
        """Get Web3 connection for a specific chain with fallback support"""
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

    def decode_portal_event(self, log: Dict, w3: Web3) -> Optional[Dict]:
        """Decode a Portals Portal event log to extract swap information"""
        try:
            # Check if this is a Portal event
            if not log["topics"] or len(log["topics"]) < 4:
                return None

            event_topic = log["topics"][0].hex()
            if event_topic != self.event_signatures["portal"]:
                return None

            # Decode Portal event data
            # Portal (address inputToken, uint256 inputAmount, address outputToken, uint256 outputAmount,
            #         address sender, address broadcaster, address recipient, address partner)
            if len(log["data"]) >= 256:  # 8 * 32 bytes
                # Decode the data field
                decoded_data = decode(
                    [
                        "address",
                        "uint256",
                        "address",
                        "uint256",
                        "address",
                        "address",
                        "address",
                        "address",
                    ],
                    bytes.fromhex(log["data"][2:]),  # Remove 0x prefix
                )

                (
                    input_token,
                    input_amount,
                    output_token,
                    output_amount,
                    sender,
                    broadcaster,
                    recipient,
                    partner,
                ) = decoded_data

                # Check if this involves ShapeShift affiliate
                if partner.lower() == self.shapeshift_affiliate.lower():
                    return {
                        "event_type": "portal",
                        "sender": sender,
                        "broadcaster": broadcaster,
                        "recipient": recipient,
                        "partner": partner,
                        "input_token": input_token,
                        "input_amount": input_amount,
                        "output_token": output_token,
                        "output_amount": output_amount,
                    }

            return None

        except Exception as e:
            logger.error(f"Error decoding Portal event: {e}")
            return None

    def get_token_metadata(self, w3: Web3, token_address: str) -> Dict:
        """Get token metadata (name, symbol, decimals) for a given token address"""
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

    def calculate_affiliate_fee(
        self,
        input_amount: int,
        user_output: int,
        input_decimals: int,
        output_decimals: int,
    ) -> Tuple[int, float]:
        """Calculate affiliate fee from input and user output amounts"""
        try:
            # Convert to human readable amounts
            input_human = input_amount / (10**input_decimals)
            output_human = user_output / (10**output_decimals)

            # Calculate fee (difference between input and what user receives)
            fee_amount = input_human - output_human

            # Calculate fee rate in basis points
            if input_human > 0:
                fee_bps = (fee_amount / input_human) * 10000
            else:
                fee_bps = 0

            return fee_amount, fee_bps

        except Exception as e:
            logger.error(f"Error calculating affiliate fee: {e}")
            return 0, 0

    def fetch_portals_events(
        self, chain_name: str, blocks_to_scan: int = 1000
    ) -> List[Dict]:
        """Fetch Portals events for a specific chain"""
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
                    # Get all logs from Portals router contract with fallback support
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "address": chain_config["portals_router"],
                    }

                    logs = self._get_logs_with_fallback(w3, filter_params, chain_config)

                    for log in logs:
                        # Decode the Portal event
                        event_data = self.decode_portal_event(log, w3)

                        if event_data:
                            # Get block info
                            block = w3.eth.get_block(log["blockNumber"])

                            # Get token metadata
                            input_token_meta = self.get_token_metadata(
                                w3, event_data["input_token"]
                            )
                            output_token_meta = self.get_token_metadata(
                                w3, event_data["output_token"]
                            )

                            # Calculate affiliate fee
                            fee_amount, fee_bps = self.calculate_affiliate_fee(
                                event_data["input_amount"],
                                event_data["output_amount"],
                                input_token_meta["decimals"],
                                output_token_meta["decimals"],
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
                                "sender": event_data["sender"],
                                "broadcaster": event_data["broadcaster"],
                                "recipient": event_data["recipient"],
                                "partner": event_data["partner"],
                                "input_token": event_data["input_token"],
                                "input_amount": event_data["input_amount"],
                                "input_amount_usd": 0.0,  # Will be calculated later
                                "output_token": event_data["output_token"],
                                "output_amount": event_data["output_amount"],
                                "output_amount_usd": 0.0,  # Will be calculated later
                                "affiliate_fee_token": input_token_meta["symbol"],
                                "affiliate_fee_amount": fee_amount,
                                "affiliate_fee_usd": 0.0,  # Will be calculated later
                                "volume_usd": 0.0,  # Will be calculated later
                                "gas_used": 0,  # Will be filled from transaction receipt
                                "gas_price": 0,  # Will be filled from transaction receipt
                                "expected_fee_bps": 55,  # Expected 55 basis points
                                "actual_fee_bps": int(fee_bps),
                                "created_at": int(time.time()),
                                "created_date": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }

                            events.append(event_record)
                            logger.info(
                                f"   ✅ Found ShapeShift affiliate Portals event: {log['transactionHash'].hex()}"
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
            logger.error(f"Error fetching Portals events for {chain_name}: {e}")
            return []

    def save_events_to_csv(self, events: List[Dict]):
        """Save Portals events to CSV file"""
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
        """Update block tracker CSV for Portals"""
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
            import pandas as pd

            df = pd.read_csv(csv_file)

            print(f"\n📊 Portals CSV Statistics:")
            print(f"   Total transactions: {len(df)}")
            print(f"   Unique chains: {df['chain'].nunique()}")
            print(
                f"   Date range: {df['block_time'].min()} to {df['block_time'].max()}"
            )
            print(f"   Total affiliate fees: ${df['affiliate_fee_usd'].sum():.2f}")
            print(f"   Total volume: ${df['volume_usd'].sum():.2f}")
            print(f"   Average fee rate: {df['actual_fee_bps'].mean():.2f} BPS")

            # Show recent transactions
            if len(df) > 0:
                print(f"\n🔍 Recent Portals Transactions:")
                recent = df.sort_values("block_timestamp", ascending=False).head(3)
                for _, row in recent.iterrows():
                    print(
                        f"   {row['chain']}: {row['input_token']} → {row['output_token']} - {row['tx_hash'][:10]}..."
                    )

        except Exception as e:
            print(f"Error reading Portals CSV: {e}")

    def run_listener(self, blocks_to_scan: int = 1000):
        """Run the Portals listener for all chains"""
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
