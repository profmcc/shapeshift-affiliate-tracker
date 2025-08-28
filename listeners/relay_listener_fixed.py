#!/usr/bin/env python3
"""
Fixed Relay Affiliate Fee Listener
Safely handles data parsing and avoids infinite loops.
"""

import os
import sqlite3
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from web3 import Web3
from eth_abi import decode
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FixedRelayListener:
    def __init__(self, config_path: str = "listeners/relay_listener_config.yaml"):
        self.config = self._load_config(config_path)
        self.affiliate_address = self.config["affiliate_address"].lower()
        self.claiming_address = self.config["claiming_address"].lower()
        self.db_path = self.config["db"]["path"]

        # Event signatures for Relay
        self.event_signatures = {
            "solver_call": "0x93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324",
            "cleanup": "0xd35467972d1fda5b63c735f59d3974fa51785a41a92aa3ed1b70832836f8dba6",
        }

        self._init_database()
        logger.info("Fixed Relay Listener initialized")
        logger.info(f"Affiliate address: {self.affiliate_address}")
        logger.info(f"Claiming address: {self.claiming_address}")
        logger.info(f"Event signatures: {list(self.event_signatures.values())}")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Replace environment variables in RPC URLs
            alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
            if not alchemy_api_key:
                raise ValueError("ALCHEMY_API_KEY environment variable not set")

            for chain in config["chains"]:
                rpc_url = chain["rpc_url"]
                if "${ALCHEMY_API_KEY}" in rpc_url:
                    chain["rpc_url"] = rpc_url.replace(
                        "${ALCHEMY_API_KEY}", alchemy_api_key
                    )

            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _init_database(self):
        """Initialize the database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relay_affiliate_fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT NOT NULL,
                log_index INTEGER NOT NULL,
                chain TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                affiliate_address TEXT NOT NULL,
                amount TEXT NOT NULL,
                token_address TEXT NOT NULL,
                solver_call_data TEXT,
                from_token TEXT,
                to_token TEXT,
                from_amount TEXT,
                to_amount TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, log_index, chain)
            )
        """
        )

        conn.commit()
        conn.close()

    def _get_chain_config(self, chain_name: str) -> Optional[Dict]:
        """Get chain configuration"""
        for chain in self.config["chains"]:
            if chain["name"] == chain_name:
                return chain
        return None

    def _save_affiliate_fees(self, fees: List[Tuple]):
        """Save affiliate fees to database"""
        if not fees:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for fee in fees:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO relay_affiliate_fees 
                    (tx_hash, log_index, chain, block_number, timestamp, event_type,
                     affiliate_address, amount, token_address, solver_call_data,
                     from_token, to_token, from_amount, to_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    fee,
                )
            except Exception as e:
                logger.error(f"Error saving fee: {e}")

        conn.commit()
        conn.close()

    def _safe_parse_amount(self, data: bytes) -> str:
        """Safely parse amount from transfer data"""
        try:
            if not data or len(data) == 0:
                return "0"

            # Ensure data is at least 32 bytes
            if len(data) < 32:
                # Pad with zeros if needed
                padded_data = data + b"\x00" * (32 - len(data))
            else:
                padded_data = data[:32]

            # Parse as big-endian integer
            amount = int.from_bytes(padded_data, "big")
            return str(amount)
        except Exception as e:
            logger.warning(f"Error parsing amount: {e}")
            return "0"

    def _extract_trading_pair(self, w3: Web3, receipt: Dict) -> Dict:
        """Extract trading pair information from transaction"""
        result = {
            "from_token": "",
            "to_token": "",
            "from_amount": "0",
            "to_amount": "0",
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
                ):  # Fixed: removed 0x prefix
                    from_addr = "0x" + log["topics"][1].hex()[-40:]
                    to_addr = "0x" + log["topics"][2].hex()[-40:]
                    token_addr = log["address"]
                    amount = self._safe_parse_amount(log["data"])

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
                result["from_token"] = transfers[0]["token"]
                result["from_amount"] = transfers[0]["amount"]
                result["to_token"] = transfers[-1]["token"]
                result["to_amount"] = transfers[-1]["amount"]

        except Exception as e:
            logger.warning(f"Error extracting trading pair: {e}")

        return result

    def _process_transaction(
        self, w3: Web3, tx_hash: str, chain_name: str
    ) -> List[Tuple]:
        """Process a single transaction to find affiliate fees"""
        fees = []

        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return []

            block = w3.eth.get_block(receipt["blockNumber"])
            timestamp = block["timestamp"]

            # Extract trading pair
            pair_info = self._extract_trading_pair(w3, receipt)

            # Check for ERC-20 transfers to affiliate address
            for idx, log in enumerate(receipt["logs"]):
                if (
                    log.get("topics")
                    and len(log["topics"]) == 3
                    and log["topics"][0].hex()
                    == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):  # Fixed: removed 0x prefix
                    to_address = "0x" + log["topics"][2].hex()[-40:]

                    if to_address.lower() == self.affiliate_address:
                        token_address = log["address"]
                        amount = self._safe_parse_amount(log["data"])
                        log_index = log.get("logIndex", idx)

                        fee_data = (
                            tx_hash,
                            log_index,
                            chain_name,
                            receipt["blockNumber"],
                            timestamp,
                            "ERC20AffiliateFee",
                            self.affiliate_address,
                            amount,
                            token_address,
                            "",  # No solver call data
                            pair_info["from_token"],
                            pair_info["to_token"],
                            pair_info["from_amount"],
                            pair_info["to_amount"],
                        )
                        fees.append(fee_data)
                        logger.info(
                            f"Found ERC-20 affiliate fee: {amount} of {token_address}"
                        )

            # Check for native currency transfer
            tx = w3.eth.get_transaction(tx_hash)
            if (
                tx
                and tx.get("to")
                and tx["to"].lower() == self.affiliate_address
                and tx.get("value", 0) > 0
            ):
                amount = str(tx["value"])
                token_address = "0x0000000000000000000000000000000000000000"

                fee_data = (
                    tx_hash,
                    -1,
                    chain_name,
                    receipt["blockNumber"],
                    timestamp,
                    "NativeAffiliateFee",
                    self.affiliate_address,
                    amount,
                    token_address,
                    "",
                    pair_info["from_token"],
                    pair_info["to_token"],
                    pair_info["from_amount"],
                    pair_info["to_amount"],
                )
                fees.append(fee_data)
                logger.info(f"Found native affiliate fee: {amount} wei")

        except Exception as e:
            logger.error(f"Error processing transaction {tx_hash}: {e}")

        return fees

    def scan_chain(
        self,
        chain_name: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        blocks: int = 1000,
    ) -> int:
        """Scan a chain for Relay transactions with progress tracking"""
        chain_config = self._get_chain_config(chain_name)
        if not chain_config:
            logger.error(f"Chain config not found for {chain_name}")
            return 0

        try:
            w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
            if not w3.is_connected():
                logger.error(f"Failed to connect to {chain_name}")
                return 0

            if start_block is None:
                # Use recent blocks instead of starting from the beginning
                latest_block = w3.eth.block_number
                start_block = max(chain_config["start_block"], latest_block - blocks)
            if end_block is None:
                end_block = w3.eth.block_number

            logger.info(
                f"Scanning {chain_name} from block {start_block} to {end_block}"
            )
            logger.info(f"Total blocks to scan: {end_block - start_block + 1}")

            total_fees = 0
            chunk_size = 50  # Even smaller chunks for testing
            total_chunks = (end_block - start_block + 1) // chunk_size + 1
            current_chunk = 0

            for current_block in range(start_block, end_block + 1, chunk_size):
                chunk_end = min(current_block + chunk_size - 1, end_block)
                current_chunk += 1

                # Progress update every 5 chunks
                if current_chunk % 5 == 0:
                    progress = (current_chunk / total_chunks) * 100
                    logger.info(
                        f"   📊 Progress: {progress:.1f}% ({current_chunk}/{total_chunks} chunks)"
                    )

                try:
                    # Get all logs from Relay routers with timeout
                    for router_address in chain_config["router_addresses"]:
                        filter_params = {
                            "fromBlock": current_block,
                            "toBlock": chunk_end,
                            "address": router_address,
                        }

                        # Add timeout to the request
                        logs = w3.eth.get_logs(filter_params)
                        logger.debug(
                            f"   Found {len(logs)} logs from router {router_address[:10]}..."
                        )

                        for log in logs:
                            # Check if this involves affiliate address
                            tx_receipt = w3.eth.get_transaction_receipt(
                                log["transactionHash"]
                            )

                            # Look for affiliate address in logs
                            affiliate_involved = False
                            for receipt_log in tx_receipt["logs"]:
                                if receipt_log.get("topics"):
                                    for topic in receipt_log["topics"]:
                                        if (
                                            self.affiliate_address
                                            in topic.hex().lower()
                                        ):
                                            affiliate_involved = True
                                            break
                                    if affiliate_involved:
                                        break

                            if affiliate_involved:
                                fees = self._process_transaction(
                                    w3, log["transactionHash"].hex(), chain_name
                                )
                                self._save_affiliate_fees(fees)
                                total_fees += len(fees)
                                logger.info(
                                    f"   ✅ Found {len(fees)} affiliate fees in transaction {log['transactionHash'].hex()[:10]}..."
                                )

                    # Add delay to avoid rate limiting
                    time.sleep(1.0)  # Increased from 0.1 to 1.0 seconds

                except Exception as e:
                    logger.error(
                        f"Error scanning blocks {current_block}-{chunk_end}: {e}"
                    )
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        logger.warning("Rate limit hit, waiting 5 seconds...")
                        time.sleep(5.0)  # Wait longer for rate limits
                    continue

            logger.info(f"Found {total_fees} affiliate fees on {chain_name}")
            return total_fees

        except Exception as e:
            logger.error(f"Error scanning {chain_name}: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM relay_affiliate_fees")
        total_fees = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chain) FROM relay_affiliate_fees")
        unique_chains = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(CAST(amount AS REAL)) FROM relay_affiliate_fees")
        total_amount = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_fees": total_fees,
            "unique_chains": unique_chains,
            "total_amount": total_amount,
        }


def main():
    """Main function"""
    import argparse
    import signal
    import sys

    def timeout_handler(signum, frame):
        logger.error("⏰ Timeout reached! Stopping listener...")
        sys.exit(1)

    # Set timeout for the entire operation (15 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(900)  # 15 minutes timeout

    parser = argparse.ArgumentParser(description="Fixed Relay Affiliate Fee Listener")
    parser.add_argument("--chain", type=str, help="Specific chain to scan")
    parser.add_argument(
        "--blocks", type=int, default=1000, help="Number of blocks to scan"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run in test mode (scan only 10 blocks)"
    )
    args = parser.parse_args()

    try:
        listener = FixedRelayListener()

        if args.chain:
            # Scan specific chain
            logger.info(f"🔍 Starting scan for {args.chain} chain...")
            listener.scan_chain(args.chain, blocks=args.blocks)
        else:
            # Scan all chains
            logger.info("🔍 Starting scan for all chains...")
            for chain in listener.config["chains"]:
                logger.info(f"   📡 Scanning {chain['name']}...")
                try:
                    listener.scan_chain(chain["name"], blocks=args.blocks)
                except Exception as e:
                    logger.error(f"❌ Error scanning {chain['name']}: {e}")
                    continue

        # Cancel timeout
        signal.alarm(0)

        stats = listener.get_stats()
        print(f"\n📊 Relay Database Statistics:")
        print(f"   Total fees: {stats['total_fees']}")
        print(f"   Unique chains: {stats['unique_chains']}")
        print(f"   Total amount: {stats['total_amount']}")

    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        signal.alarm(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        signal.alarm(0)
        sys.exit(1)


if __name__ == "__main__":
    main()
