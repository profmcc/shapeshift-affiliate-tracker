#!/usr/bin/env python3
"""
ShapeShift Relay Affiliate Fee Tracker

Tracks affiliate fees from Relay transactions across multiple EVM chains.
Supports multiple router addresses per chain and proper event parsing.
"""

import yaml
import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from web3._utils.events import get_event_data, event_abi_to_log_topic
import os
import sys
import argparse
from dotenv import load_dotenv

# Add shared directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.custom_logging import setup_logger, get_logger
from shared.block_tracker import BlockTracker

load_dotenv()
setup_logger("relay_listener")
logger = get_logger(__name__)


class RelayListener:
    def __init__(self, config_path: str = "listeners/relay_listener_config.yaml"):
        """Initialize the Relay Listener"""
        self.config = self._load_config(config_path)
        self._init_database()

        # Initialize block tracker
        self.block_tracker = BlockTracker()

        # Load the ABI
        with open("shared/abis/relay/ERC20Router.json", "r") as f:
            self.abi = json.load(f)

        # Build event signature map
        self.event_signatures = {}
        for item in self.abi:
            if item.get("type") == "event":
                event_name = item["name"]
                # Create a minimal ABI for the event
                event_abi = {
                    "type": "event",
                    "name": event_name,
                    "inputs": item.get("inputs", []),
                }
                # Generate topic hash
                topic = event_abi_to_log_topic(event_abi)
                self.event_signatures[topic.hex().lower()] = event_abi

        # Get affiliate and claiming addresses
        self.affiliate_address = self.config["affiliate_address"].lower()
        self.claiming_address = self.config["claiming_address"].lower()

        logger.info(f"Relay Listener initialized")
        logger.info(f"Affiliate address: {self.affiliate_address}")
        logger.info(f"Claiming address: {self.claiming_address}")
        logger.info(f"Event signatures: {list(self.event_signatures.keys())}")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Replace environment variables in RPC URLs
        for chain in config["chains"]:
            rpc_url = chain["rpc_url"]
            if "${ALCHEMY_API_KEY}" in rpc_url:
                chain["rpc_url"] = rpc_url.replace(
                    "${ALCHEMY_API_KEY}", os.getenv("ALCHEMY_API_KEY", "")
                )
                if not chain["rpc_url"] or "${ALCHEMY_API_KEY}" in chain["rpc_url"]:
                    raise ValueError("ALCHEMY_API_KEY environment variable not set")

        return config

    def _load_abi(self) -> List[Dict]:
        """Load the ERC20Router ABI"""
        abi_path = "shared/abis/relay/ERC20Router.json"
        with open(abi_path, "r") as f:
            return json.load(f)

    def _init_database(self):
        """Initialize the database and create tables"""
        db_path = self.config["db"]["path"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create relay_affiliate_fees table for tracking actual affiliate fee events
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relay_affiliate_fees (
                tx_hash TEXT,
                log_index INTEGER,
                chain TEXT,
                block_number INTEGER,
                timestamp INTEGER,
                event_type TEXT,
                affiliate_address TEXT,
                amount TEXT,
                token_address TEXT,
                solver_call_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tx_hash, log_index)
            )
        """
        )

        # Add new columns for trading pair analysis if they don't exist
        try:
            cursor.execute(
                "ALTER TABLE relay_affiliate_fees ADD COLUMN from_token TEXT"
            )
            cursor.execute("ALTER TABLE relay_affiliate_fees ADD COLUMN to_token TEXT")
            cursor.execute(
                "ALTER TABLE relay_affiliate_fees ADD COLUMN from_amount TEXT"
            )
            cursor.execute("ALTER TABLE relay_affiliate_fees ADD COLUMN to_amount TEXT")
            cursor.execute(
                "ALTER TABLE relay_affiliate_fees ADD COLUMN volume_usd REAL"
            )
            cursor.execute(
                "ALTER TABLE relay_affiliate_fees ADD COLUMN affiliate_fee_usd REAL"
            )
        except sqlite3.OperationalError:
            # Columns already exist
            pass

        # Create relay_claiming_transactions table for tracking actual fee payouts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relay_claiming_transactions (
                tx_hash TEXT,
                chain TEXT,
                block_number INTEGER,
                timestamp INTEGER,
                claiming_address TEXT,
                amount TEXT,
                token_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tx_hash)
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relay_affiliate_fees_chain_block ON relay_affiliate_fees(chain, block_number)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relay_affiliate_fees_affiliate_addr ON relay_affiliate_fees(affiliate_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relay_claiming_tx_chain_block ON relay_claiming_transactions(chain, block_number)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relay_claiming_tx_claiming_addr ON relay_claiming_transactions(claiming_address)"
        )

        conn.commit()
        conn.close()

    def _get_chain_config(self, chain_name: str) -> Optional[Dict]:
        """Get configuration for a specific chain"""
        for chain in self.config["chains"]:
            if chain["name"] == chain_name:
                return chain
        return None

    def _save_affiliate_fees(self, fees: List[Tuple]):
        """Save affiliate fee events to database"""
        if not fees:
            return

        conn = sqlite3.connect(self.config["db"]["path"])
        cursor = conn.cursor()

        try:
            cursor.executemany(
                """
                INSERT OR IGNORE INTO relay_affiliate_fees 
                (tx_hash, log_index, chain, block_number, timestamp, event_type, affiliate_address, amount, token_address, solver_call_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                fees,
            )

            conn.commit()
            logger.info(f"💾 Saved {len(fees)} Relay affiliate fees to database")
        except Exception as e:
            logger.error(f"Error saving affiliate fee events: {e}")
        finally:
            conn.close()

    def _parse_solver_call_data_for_fees(self, data: bytes) -> List[int]:
        """Parse solver call data to extract affiliate fees in gwei"""
        fees = []

        if len(data) < 4:
            return fees

        try:
            # Look for common function selectors that might contain fee data
            # These are typical function calls in Relay solver data

            # Check for exec function calls
            exec_selector = b"\x22\x13\xbc\x0b"  # exec function
            if data.startswith(exec_selector):
                # Parse exec(target, value, data)
                if len(data) >= 68:
                    target = "0x" + data[4:24].hex()
                    value = int.from_bytes(data[24:56], "big")

                    # The value field might contain the affiliate fee in gwei
                    if value > 0:
                        fees.append(value)
                        logger.info(
                            f"Found potential affiliate fee in exec value: {value} gwei"
                        )

                    # Parse the data section for additional fee information
                    data_offset = int.from_bytes(data[56:68], "big")
                    if data_offset > 0 and len(data) > data_offset:
                        call_data = data[data_offset:]
                        fees.extend(self._extract_fees_from_call_data(call_data))

            # Check for cleanupErc20s function calls
            cleanup_selector = b"\x3b\x22\x53\xc8"  # cleanupErc20s function
            if data.startswith(cleanup_selector):
                if len(data) >= 68:
                    offset = int.from_bytes(data[4:36], "big")
                    if offset > 0 and len(data) > offset:
                        cleanup_data = data[offset:]
                        fees.extend(self._extract_fees_from_cleanup_data(cleanup_data))

            # Check for transfer function calls
            transfer_selector = b"\xa9\x05\x9c\xbb"  # transfer(address,uint256)
            if data.startswith(transfer_selector):
                if len(data) >= 68:
                    to_address = "0x" + data[4:24].hex()
                    amount = int.from_bytes(data[24:56], "big")
                    if amount > 0:
                        fees.append(amount)
                        logger.info(
                            f"Found potential affiliate fee in transfer: {amount} gwei"
                        )

            # Check for transferFrom function calls
            transfer_from_selector = (
                b"\x23\xb8\x72\xdd"  # transferFrom(address,address,uint256)
            )
            if data.startswith(transfer_from_selector):
                if len(data) >= 100:
                    from_address = "0x" + data[4:24].hex()
                    to_address = "0x" + data[24:44].hex()
                    amount = int.from_bytes(data[44:76], "big")
                    if amount > 0:
                        fees.append(amount)
                        logger.info(
                            f"Found potential affiliate fee in transferFrom: {amount} gwei"
                        )

            # Look for any 32-byte values that might represent fees
            # This catches fees that might be encoded in other ways
            for i in range(0, len(data) - 31, 32):
                if i + 32 <= len(data):
                    value = int.from_bytes(data[i : i + 32], "big")
                    # Filter for reasonable fee values (between 1 gwei and 1 ETH)
                    if 1 <= value <= 10**18:
                        fees.append(value)
                        logger.info(
                            f"Found potential fee value at offset {i}: {value} gwei"
                        )

        except Exception as e:
            logger.error(f"Error parsing solver call data: {e}")

        return fees

    def _extract_fees_from_call_data(self, call_data: bytes) -> List[int]:
        """Extract fee information from nested call data"""
        fees = []

        if len(call_data) < 4:
            return fees

        try:
            # Look for function selectors in the call data
            for i in range(0, len(call_data) - 3):
                # Check if this looks like a function selector
                potential_selector = call_data[i : i + 4]

                # Common selectors that might contain fee data
                if potential_selector in [
                    b"\xa9\x05\x9c\xbb",  # transfer
                    b"\x23\xb8\x72\xdd",  # transferFrom
                    b"\x22\x13\xbc\x0b",  # exec
                    b"\x3b\x22\x53\xc8",
                ]:  # cleanupErc20s
                    # Extract the amount parameter (usually 32 bytes after the selector)
                    if i + 36 <= len(call_data):
                        amount = int.from_bytes(call_data[i + 4 : i + 36], "big")
                        if amount > 0:
                            fees.append(amount)
                            logger.info(f"Found fee in nested call data: {amount} gwei")

        except Exception as e:
            logger.error(f"Error extracting fees from call data: {e}")

        return fees

    def _extract_fees_from_cleanup_data(self, cleanup_data: bytes) -> List[int]:
        """Extract fee information from cleanupErc20s data"""
        fees = []

        try:
            if len(cleanup_data) >= 32:
                # Parse address array
                addr_count = int.from_bytes(cleanup_data[:32], "big")
                if addr_count > 0 and len(cleanup_data) >= 32 + addr_count * 32:
                    # Parse amount array
                    amount_offset = 32 + addr_count * 32
                    if len(cleanup_data) >= amount_offset + 32:
                        amount_count = int.from_bytes(
                            cleanup_data[amount_offset : amount_offset + 32], "big"
                        )
                        if (
                            amount_count > 0
                            and len(cleanup_data)
                            >= amount_offset + 32 + amount_count * 32
                        ):
                            for i in range(amount_count):
                                amount_start = amount_offset + 32 + i * 32
                                if amount_start + 32 <= len(cleanup_data):
                                    amount = int.from_bytes(
                                        cleanup_data[amount_start : amount_start + 32],
                                        "big",
                                    )
                                    if amount > 0:
                                        fees.append(amount)
                                        logger.info(
                                            f"Found fee in cleanup data: {amount} gwei"
                                        )

        except Exception as e:
            logger.error(f"Error extracting fees from cleanup data: {e}")

        return fees

    def _extract_partner_identifiers(self, data: bytes) -> dict:
        """Extract partner/affiliate identifiers from transaction data"""
        partner_info = {}

        # Look for common partner/affiliate patterns
        # These might be encoded as strings, addresses, or other identifiers

        # Check for string data that might contain partner names
        for i in range(0, min(len(data) - 31, 200), 32):
            chunk = data[i : i + 32]
            try:
                # Remove trailing zeros
                while chunk and chunk[-1] == 0:
                    chunk = chunk[:-1]
                if chunk:
                    string_data = chunk.decode("utf-8", errors="ignore")
                    if (
                        string_data
                        and string_data.isprintable()
                        and len(string_data) > 2
                    ):
                        # Look for partner-related keywords
                        lower_string = string_data.lower()
                        if any(
                            keyword in lower_string
                            for keyword in [
                                "partner",
                                "affiliate",
                                "shapeshift",
                                "ss",
                                "portal",
                                "referral",
                            ]
                        ):
                            partner_info["partner_string"] = string_data
                            partner_info["partner_string_offset"] = i
            except:
                pass

            # Check if this looks like an address (not all zeros)
            if chunk[:12] != b"\x00" * 12:
                addr = "0x" + chunk[-20:].hex()
                # Check if this might be a partner/affiliate address
                if any(
                    keyword in addr.lower()
                    for keyword in ["shapeshift", "ss", "partner", "affiliate"]
                ):
                    partner_info["partner_address"] = addr
                    partner_info["partner_address_offset"] = i

        return partner_info

    def _detect_affiliate_token(
        self, w3: Web3, receipt: Dict, global_solver_amount: int
    ) -> str:
        """Detect the token involved in an affiliate transaction"""
        token_address = (
            "0x0000000000000000000000000000000000000000"  # Default to native token
        )

        # First, look for ERC-20 transfers that involve the affiliate address
        for log in receipt["logs"]:
            if not log["topics"] or len(log["topics"]) < 3:
                continue

            # ERC-20 Transfer event signature
            if (
                log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                from_addr = "0x" + log["topics"][1][-20:].hex()
                to_addr = "0x" + log["topics"][2][-20:].hex()

                # Check if this transfer involves the affiliate address
                if (
                    from_addr.lower() == self.affiliate_address.lower()
                    or to_addr.lower() == self.affiliate_address.lower()
                ):
                    token_address = log["address"]
                    logger.info(
                        f"Found affiliate-related ERC-20 token: {token_address}"
                    )
                    return token_address

        # Look for ERC-20 transfers with amounts close to the affiliate fee amount
        for log in receipt["logs"]:
            if not log["topics"] or len(log["topics"]) < 3:
                continue

            if (
                log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                # Decode the transfer amount from the log data
                if len(log["data"]) >= 32:
                    try:
                        transfer_amount = int.from_bytes(log["data"][:32], "big")
                        # If this transfer amount is close to the affiliate fee amount, it might be the affiliate token
                        if (
                            transfer_amount > 0
                            and abs(transfer_amount - global_solver_amount)
                            < transfer_amount * 0.1
                        ):  # Within 10%
                            token_address = log["address"]
                            logger.info(
                                f"Found ERC-20 token with matching amount: {token_address} (amount: {transfer_amount})"
                            )
                            return token_address
                    except:
                        pass

        # Look for any ERC-20 transfers in the transaction
        for log in receipt["logs"]:
            if not log["topics"]:
                continue

            if (
                log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                # Decode the transfer amount
                if len(log["data"]) >= 32:
                    try:
                        transfer_amount = int.from_bytes(log["data"][:32], "big")
                        # If this is a significant transfer (more than 1 token), use this token
                        if (
                            transfer_amount > 10**18
                        ):  # More than 1 token (assuming 18 decimals)
                            token_address = log["address"]
                            logger.info(
                                f"Found significant ERC-20 transfer: {token_address} (amount: {transfer_amount})"
                            )
                            return token_address
                    except:
                        pass

        # If no ERC-20 tokens found, check if this is a native token transaction
        tx = w3.eth.get_transaction(receipt["transactionHash"])
        if tx["value"] > 0:
            logger.info(
                f"Using native token (ETH/MATIC/etc.) for transaction {receipt['transactionHash'].hex()}"
            )
            # Keep the zero address for native tokens
        else:
            logger.warning(
                f"No ERC-20 token found for transaction {receipt['transactionHash'].hex()}, using zero address"
            )

        return token_address

    def _extract_trading_pair(self, w3: Web3, receipt: Dict) -> Dict:
        """Extract trading pair from transaction receipt by analyzing ERC20 transfers."""
        transfers = {}

        for log in receipt["logs"]:
            if (
                log.get("topics")
                and len(log["topics"]) == 3
                and log["topics"][0].hex()
                == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                token_address = log["address"]
                from_address = "0x" + log["topics"][1].hex()[-40:]
                to_address = "0x" + log["topics"][2].hex()[-40:]
                amount = int.from_bytes(log["data"], "big")

                if token_address not in transfers:
                    transfers[token_address] = {"in": 0, "out": 0}

                transfers[token_address]["out"] += amount
                transfers[token_address]["in"] += amount

        # Identify from/to tokens based on net balance change
        from_token, to_token = None, None
        from_amount, to_amount = 0, 0

        # Simple heuristic: largest outflow is 'from', largest inflow is 'to'
        sorted_by_outflow = sorted(
            transfers.items(), key=lambda item: item[1]["out"], reverse=True
        )
        sorted_by_inflow = sorted(
            transfers.items(), key=lambda item: item[1]["in"], reverse=True
        )

        if sorted_by_outflow:
            from_token = sorted_by_outflow[0][0]
            from_amount = sorted_by_outflow[0][1]["out"]

        if sorted_by_inflow:
            to_token = sorted_by_inflow[0][0]
            to_amount = sorted_by_inflow[0][1]["in"]

        return {
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": str(from_amount),
            "to_amount": str(to_amount),
        }

    def _process_transaction(
        self, w3: Web3, tx_hash: str, chain_name: str
    ) -> List[Tuple]:
        """
        Processes a single transaction to find and record affiliate fees
        paid to the ShapeShift affiliate address. It directly looks for
        transfers to the affiliate address rather than parsing call data.
        """
        fees = []
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                logger.warning(
                    f"Could not get receipt for tx {tx_hash} on {chain_name}"
                )
                return []

            block = w3.eth.get_block(receipt["blockNumber"])
            timestamp = block["timestamp"]

            # Extract trading pair
            pair_info = self._extract_trading_pair(w3, receipt)

            # 1. Check for ERC-20 token transfers to the affiliate address
            for idx, log in enumerate(receipt["logs"]):
                # Check for standard ERC-20 Transfer event signature and correct number of topics
                if (
                    log.get("topics")
                    and len(log["topics"]) == 3
                    and log["topics"][0].hex()
                    == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    to_address = "0x" + log["topics"][2].hex()[-40:]

                    if to_address.lower() == self.affiliate_address.lower():
                        token_address = log["address"]
                        amount = str(int.from_bytes(log["data"], "big"))
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
                            f"Found ERC-20 affiliate fee in {tx_hash}: {amount} of {token_address}"
                        )

            # 2. Check for native currency transfer to the affiliate address
            tx = w3.eth.get_transaction(tx_hash)
            if (
                tx
                and tx.get("to")
                and tx["to"].lower() == self.affiliate_address.lower()
                and tx.get("value", 0) > 0
            ):
                amount = str(tx["value"])
                token_address = "0x0000000000000000000000000000000000000000"

                # Use a fake log_index for uniqueness (-1 for native transfer)
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
                logger.info(f"Found native affiliate fee in {tx_hash}: {amount} wei")

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error processing transaction {tx_hash} on {chain_name}: {e}")

        return fees

    def _decode_transfer_data(self, data: bytes) -> Tuple[str, int]:
        """Decode transfer data to extract token address and amount"""
        if len(data) < 4:
            return None, None

        # Check if this is a transfer call
        transfer_selector = b"\xa9\x05\x9c\xbb"  # transfer(address,uint256)
        transfer_from_selector = (
            b"\x23\xb8\x72\xdd"  # transferFrom(address,address,uint256)
        )

        if data.startswith(transfer_selector) and len(data) >= 68:
            # transfer(to, amount)
            to_address = "0x" + data[4:24].hex()
            amount = int.from_bytes(data[24:56], "big")
            return to_address, amount

        elif data.startswith(transfer_from_selector) and len(data) >= 100:
            # transferFrom(from, to, amount)
            from_address = "0x" + data[4:24].hex()
            to_address = "0x" + data[24:44].hex()
            amount = int.from_bytes(data[44:76], "big")
            return to_address, amount

        return None, None

    def scan_chain(
        self,
        chain_name: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
    ) -> int:
        """Scan a specific chain for affiliate fee events by iterating through blocks."""
        chain_config = self._get_chain_config(chain_name)
        if not chain_config:
            logger.error(f"Chain config not found for {chain_name}")
            return 0

        w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
        if not w3.is_connected():
            logger.error(f"Failed to connect to {chain_name} RPC")
            return 0

        if start_block is None:
            start_block = self.block_tracker.get_last_scanned_block(
                "relay", chain_name, chain_config["start_block"]
            )
        if end_block is None:
            end_block = w3.eth.block_number

        logger.info(f"Scanning {chain_name} from block {start_block} to {end_block}")

        all_fees = []

        for block_num in range(start_block, end_block + 1):
            try:
                if block_num % 50 == 0:
                    logger.info(f"Scanning block {block_num} on {chain_name}...")
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.get("transactions", []):
                    tx_hash = tx["hash"].hex()
                    fees = self._process_transaction(w3, tx_hash, chain_name)
                    if fees:
                        all_fees.extend(fees)
            except Exception as e:
                logger.error(f"Error processing block {block_num} on {chain_name}: {e}")
                time.sleep(1)  # Add a small delay on error
                continue

        if all_fees:
            self._save_affiliate_fees(all_fees)

        # Update last scanned block
        self.block_tracker.update_last_scanned_block("relay", chain_name, end_block)

        logger.info(f"Found {len(all_fees)} affiliate fee events on {chain_name}")
        return len(all_fees)

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.config["db"]["path"])
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM relay_affiliate_fees")
        total_fees = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT tx_hash) FROM relay_affiliate_fees")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chain) FROM relay_affiliate_fees")
        chains_with_fees = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT chain, COUNT(*) as fee_count, COUNT(DISTINCT tx_hash) as tx_count
            FROM relay_affiliate_fees 
            GROUP BY chain
        """
        )
        chain_stats = {}
        for row in cursor.fetchall():
            chain_stats[row[0]] = {"fee_count": row[1], "tx_count": row[2]}

        conn.close()

        return {
            "total_fees": total_fees,
            "total_transactions": total_transactions,
            "chains_with_fees": chains_with_fees,
            "chain_stats": chain_stats,
        }


def main():
    parser = argparse.ArgumentParser(
        description="ShapeShift Relay Affiliate Fee Tracker"
    )
    parser.add_argument(
        "--chain",
        required=True,
        help="Chain to scan (base, optimism, avalanche, polygon)",
    )
    parser.add_argument(
        "--from", dest="start_block", type=int, help="Start block number"
    )
    parser.add_argument(
        "--to",
        dest="end_block",
        type=str,
        default="latest",
        help='End block number or "latest"',
    )
    parser.add_argument(
        "--config",
        default="listeners/relay_listener_config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    try:
        listener = RelayListener(args.config)

        # Handle "latest" end block
        end_block = None
        if args.end_block != "latest":
            end_block = int(args.end_block)

        fee_count = listener.scan_chain(args.chain, args.start_block, end_block)

        # Print statistics
        stats = listener.get_stats()
        logger.info(f"Scan complete. Database stats: {stats}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
