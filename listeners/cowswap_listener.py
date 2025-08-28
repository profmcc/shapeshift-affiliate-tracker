#!/usr/bin/env python3
"""
CowSwap Affiliate Fee Listener - Consolidated Version
Tracks ShapeShift affiliate fees from CowSwap trades across EVM chains.
"""

import os
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from web3 import Web3
from eth_abi import decode

# Add shared directory to path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.block_tracker import BlockTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CowSwapListener:
    def __init__(self, db_path: str = "databases/cowswap_transactions.db"):
        self.db_path = db_path
        self.infura_api_key = os.getenv(
            "INFURA_API_KEY", "208a3474635e4ebe8ee409cef3fbcd40"
        )
        self.init_database()

        # Initialize block tracker
        self.block_tracker = BlockTracker()

        # ShapeShift affiliate addresses by chain
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
        }

        # Chain configurations
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "chain_id": 1,
                "rpc_url": f"https://mainnet.infura.io/v3/{self.infura_api_key}",
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "chunk_size": 1000,
                "delay": 1.0,
            },
            "polygon": {
                "name": "Polygon",
                "chain_id": 137,
                "rpc_url": f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}",
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "optimism": {
                "name": "Optimism",
                "chain_id": 10,
                "rpc_url": f"https://optimism-mainnet.infura.io/v3/{self.infura_api_key}",
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "arbitrum": {
                "name": "Arbitrum",
                "chain_id": 42161,
                "rpc_url": f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}",
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "chunk_size": 2000,
                "delay": 0.5,
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": f"https://base-mainnet.infura.io/v3/{self.infura_api_key}",
                "cowswap_contract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                "chunk_size": 2000,
                "delay": 0.5,
            },
        }

        # CowSwap event signatures
        self.event_signatures = {
            "trade": "0xa07a543ab8a018198e99ca0184c93fe9050a79400a0a723441f84de1d972cc17",
            "order": "0xed99827efb37016f2275f98c4bcf71c7551c75d59e9b450f79fa32e60be672c2",
            "invalidation": "0x40338ce1a7c49204f0099533b1e9a7ee0a3d261f84974ab7af36105b8c4e9db4",
            "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        }

    def init_database(self):
        """Initialize the database with CowSwap transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cowswap_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                owner TEXT,
                sell_token TEXT,
                buy_token TEXT,
                sell_amount TEXT,
                buy_amount TEXT,
                fee_amount TEXT,
                order_uid TEXT,
                app_data TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                sell_token_name TEXT,
                buy_token_name TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain, event_type)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info(f"✅ CowSwap database initialized: {self.db_path}")

    def get_web3_connection(self, chain_config: Dict) -> Optional[Web3]:
        """Get Web3 connection for a chain"""
        try:
            w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
            if w3.is_connected():
                return w3
            else:
                logger.error(f"Failed to connect to {chain_config['name']}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to {chain_config['name']}: {e}")
            return None

    def fetch_cowswap_events(
        self, chain_name: str, blocks_to_scan: int = 2000
    ) -> List[Dict]:
        """Fetch CowSwap events for a specific chain"""
        chain_config = self.chains[chain_name]
        w3 = self.get_web3_connection(chain_config)

        if not w3:
            return []

        try:
            latest_block = w3.eth.block_number
            start_block = self.block_tracker.get_last_scanned_block(
                "cowswap", chain_name, latest_block - blocks_to_scan
            )

            logger.info(
                f"🔍 Scanning {chain_config['name']} CowSwap blocks {start_block} to {latest_block}"
            )

            events = []
            current_block = start_block
            chunk_size = chain_config["chunk_size"]

            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)

                try:
                    # Fetch all CowSwap events
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "address": chain_config["cowswap_contract"],
                    }

                    logs = w3.eth.get_logs(filter_params)

                    for log in logs:
                        if not log["topics"]:
                            continue

                        event_sig = log["topics"][0].hex()

                        # Process different CowSwap events
                        if event_sig in self.event_signatures.values():
                            block = w3.eth.get_block(log["blockNumber"])

                            event_data = self.parse_cowswap_event(log, w3, chain_config)
                            if event_data:
                                event_data["chain"] = chain_config["name"]
                                event_data["block_timestamp"] = block["timestamp"]
                                events.append(event_data)

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

            # Update last scanned block
            self.block_tracker.update_last_scanned_block(
                "cowswap", chain_name, latest_block
            )

            return events

        except Exception as e:
            logger.error(f"Error fetching CowSwap events for {chain_name}: {e}")
            return []

    def parse_cowswap_event(self, log, w3: Web3, chain_config: Dict) -> Optional[Dict]:
        """Parse a CowSwap event"""
        try:
            event_sig = log["topics"][0].hex()
            affiliate_address = self.shapeshift_affiliates.get(chain_config["chain_id"])

            # Check if ShapeShift is involved (simplified check)
            tx_receipt = w3.eth.get_transaction_receipt(log["transactionHash"])

            # Look for transfers to ShapeShift affiliate address
            has_affiliate_transfer = False
            for receipt_log in tx_receipt["logs"]:
                if (
                    len(receipt_log["topics"]) >= 3
                    and receipt_log["topics"][0].hex()
                    == self.event_signatures["erc20_transfer"]
                ):
                    to_address = "0x" + receipt_log["topics"][2][-40:].hex()
                    if to_address.lower() == affiliate_address.lower():
                        has_affiliate_transfer = True
                        break

            if not has_affiliate_transfer:
                return None

            # Determine event type
            event_type = "unknown"
            if event_sig == self.event_signatures["trade"]:
                event_type = "trade"
            elif event_sig == self.event_signatures["order"]:
                event_type = "order"
            elif event_sig == self.event_signatures["invalidation"]:
                event_type = "invalidation"

            # Basic event data structure
            event_data = {
                "tx_hash": log["transactionHash"].hex(),
                "block_number": log["blockNumber"],
                "event_type": event_type,
                "owner": None,
                "sell_token": None,
                "buy_token": None,
                "sell_amount": None,
                "buy_amount": None,
                "fee_amount": None,
                "order_uid": None,
                "app_data": None,
                "affiliate_fee_usd": 0.0,
                "volume_usd": 0.0,
            }

            # Try to decode event data (simplified)
            if len(log["topics"]) > 1:
                try:
                    # Basic decoding - would need proper ABI for full decoding
                    if event_type == "trade" and len(log["data"]) > 0:
                        # Simplified trade data extraction
                        data = log["data"]
                        event_data["sell_amount"] = (
                            str(int(data[2:66], 16)) if len(data) > 66 else None
                        )
                        event_data["buy_amount"] = (
                            str(int(data[66:130], 16)) if len(data) > 130 else None
                        )
                except Exception as e:
                    logger.debug(f"Error decoding event data: {e}")

            logger.info(
                f"   ✅ Found ShapeShift CowSwap {event_type}: {log['transactionHash'].hex()}"
            )
            return event_data

        except Exception as e:
            logger.error(f"Error parsing CowSwap event: {e}")
            return None

    def save_events_to_db(self, events: List[Dict]):
        """Save events to database"""
        if not events:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for event in events:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO cowswap_transactions 
                    (chain, tx_hash, block_number, block_timestamp, event_type, owner,
                     sell_token, buy_token, sell_amount, buy_amount, fee_amount,
                     order_uid, app_data, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event["chain"],
                        event["tx_hash"],
                        event["block_number"],
                        event["block_timestamp"],
                        event["event_type"],
                        event["owner"],
                        event["sell_token"],
                        event["buy_token"],
                        event["sell_amount"],
                        event["buy_amount"],
                        event["fee_amount"],
                        event["order_uid"],
                        event["app_data"],
                        event["affiliate_fee_usd"],
                        event["volume_usd"],
                    ),
                )

            except Exception as e:
                logger.error(f"Error saving event {event['tx_hash']}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"💾 Saved {len(events)} CowSwap events to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM cowswap_transactions")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chain) FROM cowswap_transactions")
        unique_chains = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM cowswap_transactions")
        total_fees = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(volume_usd) FROM cowswap_transactions")
        total_volume = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT COUNT(*) FROM cowswap_transactions WHERE event_type = 'trade'"
        )
        trade_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n📊 CowSwap Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Trade events: {trade_count}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the CowSwap listener for all chains"""
        logger.info("🚀 Starting CowSwap affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_cowswap_events(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)

        logger.info(
            f"\n✅ CowSwap listener completed! Found {total_events} total events"
        )
        self.get_database_stats()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="CowSwap Affiliate Fee Listener")
    parser.add_argument(
        "--blocks", type=int, default=2000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    listener = CowSwapListener()
    listener.run_listener(args.blocks)


if __name__ == "__main__":
    main()
