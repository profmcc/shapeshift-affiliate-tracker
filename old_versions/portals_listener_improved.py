#!/usr/bin/env python3
"""
Improved Portals Affiliate Fee Listener
Properly detects Portals affiliate fees and token information.
"""

import os
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from web3 import Web3
from eth_abi import decode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ImprovedPortalsListener:
    def __init__(self, db_path: str = "databases/portals_transactions.db"):
        self.db_path = db_path
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.init_database()

        # ShapeShift affiliate addresses by chain
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
        }

        # Chain configurations with Alchemy URLs
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 1,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 22700000,
                "chunk_size": 100,
                "delay": 1.0,
            },
            "polygon": {
                "name": "Polygon",
                "rpc_url": f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chain_id": 137,
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "start_block": 45000000,
                "chunk_size": 200,
                "delay": 0.5,
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

    def init_database(self):
        """Initialize the database with portals transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portals_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_timestamp INTEGER NOT NULL,
                input_token TEXT,
                input_amount TEXT,
                output_token TEXT,
                output_amount TEXT,
                sender TEXT,
                broadcaster TEXT,
                recipient TEXT,
                partner TEXT,
                affiliate_token TEXT,
                affiliate_amount TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain)
            )
        """
        )

        conn.commit()
        conn.close()

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

    def detect_portals_tokens(
        self, w3: Web3, receipt: Dict, chain_config: Dict
    ) -> Dict:
        """Detect input, output, and affiliate tokens in Portals transactions"""
        result = {
            "input_token": None,
            "output_token": None,
            "affiliate_token": None,
            "input_amount": None,
            "output_amount": None,
            "affiliate_amount": None,
        }

        shapeshift_affiliate = self.shapeshift_affiliates.get(chain_config["chain_id"])

        # ERC-20 Transfer event signature
        transfer_topic = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        # Track all transfers
        transfers = []
        affiliate_transfers = []

        for log in receipt["logs"]:
            if not log["topics"] or len(log["topics"]) < 3:
                continue

            if log["topics"][0].hex() == transfer_topic:
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()

                # Decode amount
                amount = 0
                if len(log["data"]) >= 32:
                    try:
                        amount = int.from_bytes(log["data"][:32], "big")
                    except:
                        pass

                transfer = {
                    "token": log["address"],
                    "from": from_addr,
                    "to": to_addr,
                    "amount": amount,
                }
                transfers.append(transfer)

                # Check if this involves ShapeShift affiliate
                if (
                    from_addr.lower() == shapeshift_affiliate.lower()
                    or to_addr.lower() == shapeshift_affiliate.lower()
                ):
                    affiliate_transfers.append(transfer)

        # Determine input/output tokens based on transfer patterns
        if len(transfers) >= 2:
            # Usually the first transfer is input, last is output
            result["input_token"] = transfers[0]["token"]
            result["input_amount"] = str(transfers[0]["amount"])
            result["output_token"] = transfers[-1]["token"]
            result["output_amount"] = str(transfers[-1]["amount"])

        # Set affiliate token and amount
        if affiliate_transfers:
            affiliate_transfer = affiliate_transfers[
                0
            ]  # Take the first affiliate transfer
            result["affiliate_token"] = affiliate_transfer["token"]
            result["affiliate_amount"] = str(affiliate_transfer["amount"])

        return result

    def fetch_portals_events(
        self, chain_name: str, blocks_to_scan: int = 2000
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
                    # Get all logs from Portals router (no topic filter to catch all events)
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

                        # Look for affiliate address in transaction logs
                        affiliate_involved = False
                        for receipt_log in tx_receipt["logs"]:
                            if receipt_log["topics"]:
                                for topic in receipt_log["topics"]:
                                    if (
                                        shapeshift_affiliate.lower()
                                        in topic.hex().lower()
                                    ):
                                        affiliate_involved = True
                                        break
                                if affiliate_involved:
                                    break

                        # Also check data for affiliate address
                        if not affiliate_involved and log["data"]:
                            if (
                                shapeshift_affiliate.lower()
                                in log["data"].hex().lower()
                            ):
                                affiliate_involved = True

                        if affiliate_involved:
                            block = w3.eth.get_block(log["blockNumber"])

                            # Detect tokens and amounts
                            token_info = self.detect_portals_tokens(
                                w3, tx_receipt, chain_config
                            )

                            event_data = {
                                "chain": chain_config["name"],
                                "tx_hash": log["transactionHash"].hex(),
                                "block_number": log["blockNumber"],
                                "block_timestamp": block["timestamp"],
                                "input_token": token_info["input_token"],
                                "input_amount": token_info["input_amount"],
                                "output_token": token_info["output_token"],
                                "output_amount": token_info["output_amount"],
                                "sender": None,
                                "broadcaster": None,
                                "recipient": None,
                                "partner": shapeshift_affiliate,
                                "affiliate_token": token_info["affiliate_token"],
                                "affiliate_amount": token_info["affiliate_amount"],
                                "affiliate_fee_usd": 0.0,  # Will be calculated later
                                "volume_usd": 0.0,  # Will be calculated later
                            }

                            events.append(event_data)
                            logger.info(
                                f"   ✅ Found ShapeShift affiliate event: {log['transactionHash'].hex()}"
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
                    INSERT OR IGNORE INTO portals_transactions 
                    (chain, tx_hash, block_number, block_timestamp, input_token, input_amount,
                     output_token, output_amount, sender, broadcaster, recipient, partner,
                     affiliate_token, affiliate_amount, affiliate_fee_usd, volume_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event["chain"],
                        event["tx_hash"],
                        event["block_number"],
                        event["block_timestamp"],
                        event["input_token"],
                        event["input_amount"],
                        event["output_token"],
                        event["output_amount"],
                        event["sender"],
                        event["broadcaster"],
                        event["recipient"],
                        event["partner"],
                        event["affiliate_token"],
                        event["affiliate_amount"],
                        event["affiliate_fee_usd"],
                        event["volume_usd"],
                    ),
                )
            except Exception as e:
                logger.error(f"Error saving event {event['tx_hash']}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"💾 Saved {len(events)} Portals events to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM portals_transactions")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chain) FROM portals_transactions")
        unique_chains = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(affiliate_fee_usd) FROM portals_transactions")
        total_fees = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(volume_usd) FROM portals_transactions")
        total_volume = cursor.fetchone()[0] or 0

        conn.close()

        print(f"\n📊 Portals Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the Portals listener for all chains"""
        logger.info("🚀 Starting Improved Portals affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_portals_events(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)

        logger.info(
            f"\n✅ Improved Portals listener completed! Found {total_events} total events"
        )
        self.get_database_stats()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Improved Portals Affiliate Fee Listener"
    )
    parser.add_argument(
        "--blocks", type=int, default=2000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    listener = ImprovedPortalsListener()
    listener.run_listener(args.blocks)


if __name__ == "__main__":
    main()
