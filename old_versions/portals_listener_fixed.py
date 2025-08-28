#!/usr/bin/env python3
"""
Fixed Portals Affiliate Fee Listener
Updated to use Alchemy API and start from last processed block.
"""

import os
import sqlite3
import time
import json
from datetime import datetime
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


class FixedPortalsListener:
    def __init__(self, db_path: str = "databases/portals_transactions.db"):
        self.db_path = db_path
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY environment variable not set")
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

        # Chain configurations with Alchemy URLs
        self.chains = {
            "ethereum": {
                "name": "Ethereum",
                "chain_id": 1,
                "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "portals_contract": "0x0000000000000000000000000000000000000000",  # Will be detected
                "chunk_size": 1000,
                "delay": 1.0,
                "last_processed_block": 22774492,  # Start from last processed block
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "portals_contract": "0x0000000000000000000000000000000000000000",  # Will be detected
                "chunk_size": 2000,
                "delay": 0.5,
                "last_processed_block": 0,  # Start from beginning for Base
            },
        }

        # Portals event signatures
        self.event_signatures = {
            "swap": "0x4a25d94a00000000000000000000000000000000000000000000000000000000",
            "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        }

    def init_database(self):
        """Initialize the database with Portals transactions table"""
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
                event_type TEXT NOT NULL,
                owner TEXT,
                sell_token TEXT,
                buy_token TEXT,
                sell_amount TEXT,
                buy_amount TEXT,
                fee_amount TEXT,
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
        logger.info(f"✅ Portals database initialized: {self.db_path}")

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
        """Detect Portals tokens and trading pair from transaction"""
        result = {
            "sell_token": "",
            "buy_token": "",
            "sell_amount": "0",
            "buy_amount": "0",
            "sell_token_name": "",
            "buy_token_name": "",
            "affiliate_fee_usd": 0.0,
            "volume_usd": 0.0,
        }

        try:
            # Look for ERC-20 transfers to identify trading pairs
            transfers = []

            for log in receipt["logs"]:
                if (
                    log.get("topics")
                    and len(log["topics"]) == 3
                    and log["topics"][0].hex()
                    == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    from_addr = "0x" + log["topics"][1].hex()[-40:]
                    to_addr = "0x" + log["topics"][2].hex()[-40:]
                    token_addr = log["address"]

                    # Parse amount
                    amount = "0"
                    if len(log["data"]) >= 32:
                        try:
                            amount_int = int.from_bytes(log["data"][:32], "big")
                            amount = str(amount_int)
                        except:
                            pass

                    transfers.append(
                        {
                            "from": from_addr,
                            "to": to_addr,
                            "token": token_addr,
                            "amount": amount,
                        }
                    )

            # Determine trading pair from transfers
            if len(transfers) >= 2:
                # Usually the first transfer is the input, last is the output
                result["sell_token"] = transfers[0]["token"]
                result["sell_amount"] = transfers[0]["amount"]
                result["buy_token"] = transfers[-1]["token"]
                result["buy_amount"] = transfers[-1]["amount"]

        except Exception as e:
            logger.warning(f"Error detecting Portals tokens: {e}")

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
            start_block = chain_config["last_processed_block"]

            # If start_block is 0, use recent blocks
            if start_block == 0:
                start_block = latest_block - blocks_to_scan

            logger.info(
                f"🔍 Scanning {chain_config['name']} Portals blocks {start_block} to {latest_block}"
            )
            logger.info(f"📊 Total blocks to scan: {latest_block - start_block + 1}")

            # Limit the scan to avoid timeouts - scan only recent blocks
            if latest_block - start_block > 50000:
                start_block = latest_block - 50000
                logger.info(f"⚠️  Limiting scan to last 50,000 blocks to avoid timeout")

            events = []
            current_block = start_block
            chunk_size = 100  # Much smaller chunks

            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)

                try:
                    # Fetch all transactions in the block range
                    for block_num in range(current_block, end_block + 1):
                        try:
                            block = w3.eth.get_block(block_num, full_transactions=True)

                            for tx in block.transactions:
                                tx_hash = tx.hash.hex()

                                # Get transaction receipt
                                receipt = w3.eth.get_transaction_receipt(tx_hash)

                                # Check if ShapeShift affiliate is involved
                                affiliate_address = self.shapeshift_affiliates.get(
                                    chain_config["chain_id"]
                                )
                                if not affiliate_address:
                                    continue

                                # Look for transfers to ShapeShift affiliate address
                                has_affiliate_transfer = False
                                for log in receipt["logs"]:
                                    if (
                                        log.get("topics")
                                        and len(log["topics"]) == 3
                                        and log["topics"][0].hex()
                                        == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                                    ):
                                        to_address = "0x" + log["topics"][2].hex()[-40:]
                                        if (
                                            to_address.lower()
                                            == affiliate_address.lower()
                                        ):
                                            has_affiliate_transfer = True
                                            break

                                if has_affiliate_transfer:
                                    # Extract trading pair information
                                    pair_info = self.detect_portals_tokens(
                                        w3, receipt, chain_config
                                    )

                                    event_data = {
                                        "chain": chain_config["name"],
                                        "tx_hash": tx_hash,
                                        "block_number": block_num,
                                        "block_timestamp": block["timestamp"],
                                        "event_type": "swap",
                                        "owner": tx["from"],
                                        "sell_token": pair_info["sell_token"],
                                        "buy_token": pair_info["buy_token"],
                                        "sell_amount": pair_info["sell_amount"],
                                        "buy_amount": pair_info["buy_amount"],
                                        "fee_amount": "0",  # Will be calculated from affiliate transfer
                                        "affiliate_fee_usd": pair_info[
                                            "affiliate_fee_usd"
                                        ],
                                        "volume_usd": pair_info["volume_usd"],
                                        "sell_token_name": pair_info["sell_token_name"],
                                        "buy_token_name": pair_info["buy_token_name"],
                                    }

                                    events.append(event_data)
                                    logger.info(
                                        f"   ✅ Found ShapeShift Portals transaction: {tx_hash}"
                                    )
                        except Exception as e:
                            logger.warning(f"Error processing block {block_num}: {e}")
                            continue

                    if current_block % 1000 == 0:
                        logger.info(
                            f"   📊 Processed {current_block - start_block} blocks..."
                        )

                    current_block = end_block + 1
                    time.sleep(chain_config["delay"])

                except Exception as e:
                    logger.error(
                        f"Error fetching logs for blocks {current_block}-{end_block}: {e}"
                    )
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        logger.warning("Rate limit hit, waiting 10 seconds...")
                        time.sleep(10.0)  # Wait longer for rate limits
                    current_block = end_block + 1
                    continue

            # Update last processed block
            chain_config["last_processed_block"] = latest_block

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
                    (chain, tx_hash, block_number, block_timestamp, event_type, owner,
                     sell_token, buy_token, sell_amount, buy_amount, fee_amount,
                     affiliate_fee_usd, volume_usd, sell_token_name, buy_token_name)
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
                        event["affiliate_fee_usd"],
                        event["volume_usd"],
                        event["sell_token_name"],
                        event["buy_token_name"],
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

        cursor.execute(
            "SELECT COUNT(*) FROM portals_transactions WHERE event_type = 'swap'"
        )
        swap_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n📊 Portals Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Swap events: {swap_count}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 2000):
        """Run the Portals listener for all chains"""
        logger.info("🚀 Starting Portals affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_portals_events(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)

        logger.info(
            f"\n✅ Portals listener completed! Found {total_events} total events"
        )
        self.get_database_stats()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Fixed Portals Affiliate Fee Listener")
    parser.add_argument(
        "--blocks", type=int, default=2000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    listener = FixedPortalsListener()
    listener.run_listener(args.blocks)


if __name__ == "__main__":
    main()
