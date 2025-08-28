#!/usr/bin/env python3
"""
Enhanced OnchainDen Clone - Advanced Transaction Analysis & Revenue Tracking

Enhanced version with:
- ERC-20 token transfer detection
- Event log parsing for complex transactions
- Advanced categorization rules
- Gas cost analysis
- Token price integration
- Multi-chain aggregation
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from decimal import Decimal
import pandas as pd
import requests
from web3 import Web3

try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # For Web3 v7+
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None
from web3.exceptions import BlockNotFound, TransactionNotFound
import aiohttp
import aiofiles

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from block_tracker import BlockTracker
from price_cache import PriceCache
from token_lookup_enhanced import EnhancedTokenLookup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("enhanced_onchainden.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class EnhancedTransaction:
    """Enhanced transaction with detailed token and event information."""

    tx_hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: str
    gas_used: int
    gas_price: str
    gas_cost_eth: float
    gas_cost_usd: Optional[float]
    chain_id: int
    chain_name: str
    category: str
    subcategory: str
    revenue_type: str
    token_address: Optional[str]
    token_symbol: Optional[str]
    token_name: Optional[str]
    token_decimals: Optional[int]
    token_amount: Optional[str]
    usd_value: Optional[float]
    method_signature: Optional[str]
    contract_interaction: bool
    events: List[Dict[str, Any]]
    notes: str = ""


class ERC20Parser:
    """Parses ERC-20 token transfers and other token events."""

    # ERC-20 Transfer event signature
    TRANSFER_EVENT_SIGNATURE = (
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )
    APPROVAL_EVENT_SIGNATURE = (
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
    )

    def __init__(self):
        self.transfer_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"},
                ],
                "name": "Transfer",
                "type": "event",
            }
        ]

    def parse_transfer_event(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse ERC-20 Transfer event from log."""
        if log.get("topics", [])[0] != self.TRANSFER_EVENT_SIGNATURE:
            return None

        try:
            # Parse event data
            from_address = "0x" + log["topics"][1][-40:]
            to_address = "0x" + log["topics"][2][-40:]
            value = int(log["data"], 16)

            return {
                "type": "Transfer",
                "from": from_address,
                "to": to_address,
                "value": str(value),
                "token_address": log["address"],
            }
        except Exception as e:
            logger.warning(f"Error parsing transfer event: {e}")
            return None

    def parse_contract_interaction(
        self, tx: Dict[str, Any], receipt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse contract interaction details."""
        result = {
            "contract_interaction": False,
            "method_signature": None,
            "events": [],
            "token_transfers": [],
        }

        if not tx.get("to") or not receipt.get("logs"):
            return result

        result["contract_interaction"] = True

        # Extract method signature from input data
        if tx.get("input") and tx["input"] != "0x":
            result["method_signature"] = tx["input"][:10]

        # Parse logs for events
        for log in receipt["logs"]:
            # Parse ERC-20 transfers
            transfer_event = self.parse_transfer_event(log)
            if transfer_event:
                result["token_transfers"].append(transfer_event)
                result["events"].append(transfer_event)

            # Add other events (could be expanded)
            else:
                result["events"].append(
                    {
                        "type": "Unknown",
                        "address": log["address"],
                        "topics": log["topics"],
                        "data": log["data"],
                    }
                )

        return result


class EnhancedTransactionCategorizer:
    """Enhanced transaction categorizer with advanced rules."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.revenue_addresses = set(config.get("revenue_addresses", []))
        self.expense_addresses = set(config.get("expense_addresses", []))
        self.ignored_addresses = set(config.get("ignored_addresses", []))
        self.custom_rules = config.get("custom_rules", [])
        self.erc20_parser = ERC20Parser()

        # Load known protocols and addresses
        self.known_protocols = self._load_known_protocols()

    def _load_known_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Load known DeFi protocols and their addresses."""
        return {
            "uniswap_v2": {
                "addresses": [
                    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
                    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
                ],
                "category": "DeFi",
                "subcategory": "DEX Trading",
            },
            "uniswap_v3": {
                "addresses": [
                    "0xe592427a0aece92de3edee1f18e0157c05861564",
                    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",
                ],
                "category": "DeFi",
                "subcategory": "DEX Trading",
            },
            "aave": {
                "addresses": [
                    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9",
                    "0x8dff5e27ea6b7ac08ebfdf9eb090f32ee9a30fcf",
                ],
                "category": "DeFi",
                "subcategory": "Lending",
            },
            "compound": {
                "addresses": [
                    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
                    "0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407",
                ],
                "category": "DeFi",
                "subcategory": "Lending",
            },
        }

    def categorize_transaction(
        self,
        tx: Dict[str, Any],
        receipt: Dict[str, Any],
        chain_name: str,
        gas_price_eth: float,
    ) -> EnhancedTransaction:
        """Categorize a transaction with enhanced parsing."""
        # Basic transaction info
        tx_hash = tx.get("hash", "")
        block_number = tx.get("blockNumber", 0)
        timestamp = tx.get("timestamp", 0)
        from_address = tx.get("from", "").lower()
        to_address = tx.get("to", "").lower()
        value = tx.get("value", "0")
        gas_used = receipt.get("gasUsed", 0)
        gas_price = tx.get("gasPrice", "0")

        # Calculate gas costs
        gas_cost_eth = (gas_used * int(gas_price)) / 1e18
        gas_cost_usd = None  # TODO: Integrate with price cache

        # Parse contract interaction
        contract_parsing = self.erc20_parser.parse_contract_interaction(tx, receipt)

        # Determine category
        category, subcategory, revenue_type = self._determine_enhanced_category(
            from_address, to_address, value, chain_name, contract_parsing
        )

        # Extract token info
        token_info = self._extract_token_info(contract_parsing, value)

        # Calculate USD value
        usd_value = self._calculate_usd_value(
            token_info.get("amount"), token_info.get("symbol"), chain_name
        )

        return EnhancedTransaction(
            tx_hash=tx_hash,
            block_number=block_number,
            timestamp=timestamp,
            from_address=from_address,
            to_address=to_address,
            value=value,
            gas_used=gas_used,
            gas_price=gas_price,
            gas_cost_eth=gas_cost_eth,
            gas_cost_usd=gas_cost_usd,
            chain_id=tx.get("chainId", 0),
            chain_name=chain_name,
            category=category,
            subcategory=subcategory,
            revenue_type=revenue_type,
            token_address=token_info.get("address"),
            token_symbol=token_info.get("symbol"),
            token_name=token_info.get("name"),
            token_decimals=token_info.get("decimals"),
            token_amount=token_info.get("amount"),
            usd_value=usd_value,
            method_signature=contract_parsing.get("method_signature"),
            contract_interaction=contract_parsing.get("contract_interaction"),
            events=contract_parsing.get("events", []),
            notes="",
        )

    def _determine_enhanced_category(
        self,
        from_addr: str,
        to_addr: str,
        value: str,
        chain_name: str,
        contract_parsing: Dict[str, Any],
    ) -> Tuple[str, str, str]:
        """Determine transaction category with enhanced logic."""
        # Check known protocols
        protocol_info = self._identify_protocol(from_addr, to_addr)
        if protocol_info:
            return protocol_info["category"], protocol_info["subcategory"], "Protocol"

        # Check revenue/expense addresses
        if from_addr in self.revenue_addresses:
            return "Revenue", "Incoming", "Primary"
        elif to_addr in self.revenue_addresses:
            return "Revenue", "Outgoing", "Primary"

        if from_addr in self.expense_addresses:
            return "Expense", "Outgoing", "Primary"
        elif to_addr in self.expense_addresses:
            return "Expense", "Incoming", "Primary"

        # Check ignored addresses
        if from_addr in self.ignored_addresses or to_addr in self.ignored_addresses:
            return "Ignored", "Internal", "None"

        # Check custom rules
        category = self._apply_enhanced_custom_rules(
            from_addr, to_addr, value, chain_name, contract_parsing
        )
        if category:
            return category[0], category[1], "Custom"

        # Determine based on contract interaction
        if contract_parsing.get("contract_interaction"):
            if contract_parsing.get("token_transfers"):
                return "Token Transfer", "ERC-20", "None"
            else:
                return "Contract", "Interaction", "None"

        # Default categorization
        if value and int(value) > 0:
            return "Transfer", "Native Token", "None"
        else:
            return "Contract", "Deployment", "None"

    def _identify_protocol(
        self, from_addr: str, to_addr: str
    ) -> Optional[Dict[str, Any]]:
        """Identify if transaction involves known DeFi protocols."""
        for protocol_name, protocol_info in self.known_protocols.items():
            if (
                from_addr in protocol_info["addresses"]
                or to_addr in protocol_info["addresses"]
            ):
                return protocol_info
        return None

    def _apply_enhanced_custom_rules(
        self,
        from_addr: str,
        to_addr: str,
        value: str,
        chain_name: str,
        contract_parsing: Dict[str, Any],
    ) -> Optional[Tuple[str, str]]:
        """Apply enhanced custom categorization rules."""
        for rule in self.custom_rules:
            if rule.get("type") == "address_pattern":
                pattern = rule["pattern"]
                if pattern in from_addr or pattern in to_addr:
                    return rule["category"], rule["subcategory"]

            elif rule.get("type") == "value_threshold":
                threshold = int(rule["threshold"])
                if value and int(value) >= threshold:
                    return rule["category"], rule["subcategory"]

            elif rule.get("type") == "method_signature":
                if contract_parsing.get("method_signature") == rule["signature"]:
                    return rule["category"], rule["subcategory"]

            elif rule.get("type") == "token_transfer":
                if contract_parsing.get("token_transfers"):
                    return rule["category"], rule["subcategory"]

        return None

    def _extract_token_info(
        self, contract_parsing: Dict[str, Any], native_value: str
    ) -> Dict[str, Any]:
        """Extract token information from contract parsing."""
        token_info = {
            "address": None,
            "symbol": None,
            "name": None,
            "decimals": None,
            "amount": None,
        }

        # Check for ERC-20 transfers
        if contract_parsing.get("token_transfers"):
            transfer = contract_parsing["token_transfers"][0]
            token_info["address"] = transfer["token_address"]
            token_info["amount"] = transfer["value"]
            # TODO: Fetch token metadata (symbol, name, decimals)

        # If no token transfer, use native token
        elif native_value and int(native_value) > 0:
            token_info["symbol"] = "ETH"  # or appropriate native token
            token_info["amount"] = native_value

        return token_info

    def _calculate_usd_value(
        self, amount: Optional[str], symbol: Optional[str], chain_name: str
    ) -> Optional[float]:
        """Calculate USD value of transaction."""
        try:
            if not amount or not symbol:
                return None

            # Convert to decimal
            amount_decimal = Decimal(amount)

            # TODO: Integrate with price cache for real-time pricing
            # For now, return None
            return None

        except (ValueError, TypeError):
            return None


class EnhancedChainScanner:
    """Enhanced blockchain scanner with better transaction parsing."""

    def __init__(self, rpc_urls: Dict[int, str], api_keys: Dict[str, str]):
        self.rpc_urls = rpc_urls
        self.api_keys = api_keys
        self.web3_instances = {}
        self._setup_web3()

    def _setup_web3(self):
        """Setup Web3 instances for each chain."""
        for chain_id, rpc_url in self.rpc_urls.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))

                # Add POA middleware for chains that need it
                if (
                    chain_id in [137, 80001, 56, 43114, 8453] and geth_poa_middleware
                ):  # Polygon, BSC, Avalanche, Base
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

                self.web3_instances[chain_id] = w3
                logger.info(f"Connected to chain {chain_id} via {rpc_url}")

            except Exception as e:
                logger.error(f"Failed to connect to chain {chain_id}: {e}")

    async def get_transactions(
        self, address: str, chain_id: int, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """Get transactions for an address with enhanced parsing."""
        if chain_id not in self.web3_instances:
            logger.error(f"No Web3 instance for chain {chain_id}")
            return []

        w3 = self.web3_instances[chain_id]
        transactions = []

        try:
            # Validate and convert address to checksum format
            try:
                checksum_address = Web3.to_checksum_address(address)
            except Exception as e:
                logger.error(f"Invalid address format for {address}: {e}")
                return []

            # Get transaction count
            nonce = w3.eth.get_transaction_count(checksum_address)
            logger.info(
                f"Address {checksum_address} has {nonce} transactions on chain {chain_id}"
            )

            # Scan blocks for transactions with better error handling
            max_blocks_to_scan = min(1000, end_block - start_block + 1)
            blocks_scanned = 0

            for block_num in range(
                start_block, min(end_block + 1, start_block + max_blocks_to_scan)
            ):
                try:
                    # Add delay to prevent rate limiting
                    if blocks_scanned > 0 and blocks_scanned % 10 == 0:
                        await asyncio.sleep(0.1)  # 100ms delay every 10 blocks

                    block = w3.eth.get_block(block_num, full_transactions=True)
                    blocks_scanned += 1

                    for tx in block.transactions:
                        if tx["from"].lower() == checksum_address.lower() or (
                            tx["to"] and tx["to"].lower() == checksum_address.lower()
                        ):
                            # Get transaction receipt with retry logic
                            receipt = None
                            for attempt in range(3):
                                try:
                                    receipt = w3.eth.get_transaction_receipt(tx["hash"])
                                    break
                                except TransactionNotFound:
                                    logger.warning(
                                        f"Receipt not found for tx {tx['hash'].hex()}"
                                    )
                                    break
                                except Exception as e:
                                    if attempt < 2:
                                        await asyncio.sleep(0.5)  # Wait before retry
                                        continue
                                    else:
                                        logger.warning(
                                            f"Failed to get receipt after 3 attempts: {e}"
                                        )
                                        break

                            if not receipt:
                                continue

                            # Get gas price in ETH
                            gas_price_eth = int(tx["gasPrice"]) / 1e18

                            tx_data = {
                                "hash": tx["hash"].hex(),
                                "blockNumber": block_num,
                                "timestamp": block.timestamp,
                                "from": tx["from"],
                                "to": tx["to"],
                                "value": str(tx["value"]),
                                "input": tx.get("input", "0x"),
                                "gasUsed": receipt["gasUsed"],
                                "gasPrice": str(tx["gasPrice"]),
                                "chainId": chain_id,
                                "gasPriceEth": gas_price_eth,
                            }

                            # Add receipt data
                            tx_data["receipt"] = {
                                "gasUsed": receipt["gasUsed"],
                                "logs": receipt["logs"],
                                "status": receipt.get("status", 1),
                            }

                            transactions.append(tx_data)

                            if len(transactions) % 100 == 0:
                                logger.info(
                                    f"Found {len(transactions)} transactions so far..."
                                )

                except BlockNotFound:
                    logger.warning(f"Block {block_num} not found")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing block {block_num}: {e}")
                    # Add longer delay on errors
                    await asyncio.sleep(1.0)
                    continue

                # Limit to prevent overwhelming
                if len(transactions) >= 1000:  # Reduced from 10000
                    logger.warning(
                        f"Reached transaction limit for {address} on chain {chain_id}"
                    )
                    break

        except Exception as e:
            logger.error(
                f"Error getting transactions for {address} on chain {chain_id}: {e}"
            )

        return transactions


class EnhancedOnchainDenAnalyzer:
    """Enhanced OnchainDen analyzer with advanced features."""

    def __init__(self, config_path: str = "config/onchainden_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.categorizer = EnhancedTransactionCategorizer(self.config)
        self.block_tracker = BlockTracker()
        # Initialize price cache with a default API key if available
        try:
            self.price_cache = PriceCache(api_key="demo")
        except:
            self.price_cache = None
        self.token_lookup = EnhancedTokenLookup()

        # Setup enhanced chain scanner
        self.chain_scanner = EnhancedChainScanner(
            rpc_urls=self.config["rpc_urls"], api_keys=self.config["api_keys"]
        )

        # Database setup
        self.db_path = "databases/enhanced_onchainden.db"
        self._init_database()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "rpc_urls": {
                1: "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
                137: "https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY",
                8453: "https://mainnet.base.org",
                42161: "https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY",
            },
            "api_keys": {
                "etherscan": "YOUR_ETHERSCAN_KEY",
                "polygonscan": "YOUR_POLYGONSCAN_KEY",
                "basescan": "YOUR_BASESCAN_KEY",
                "arbiscan": "YOUR_ARBISCAN_KEY",
            },
            "addresses": [],
            "revenue_addresses": [],
            "expense_addresses": [],
            "ignored_addresses": [],
            "custom_rules": [],
        }

    def _init_database(self):
        """Initialize the enhanced database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create enhanced transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS enhanced_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                block_number INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT NOT NULL,
                value TEXT NOT NULL,
                gas_used INTEGER NOT NULL,
                gas_price TEXT NOT NULL,
                gas_cost_eth REAL NOT NULL,
                gas_cost_usd REAL,
                chain_id INTEGER NOT NULL,
                chain_name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                revenue_type TEXT NOT NULL,
                token_address TEXT,
                token_symbol TEXT,
                token_name TEXT,
                token_decimals INTEGER,
                token_amount TEXT,
                usd_value REAL,
                method_signature TEXT,
                contract_interaction BOOLEAN NOT NULL,
                events TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_address ON enhanced_transactions(from_address, to_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_category ON enhanced_transactions(category, revenue_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_chain ON enhanced_transactions(chain_id, chain_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_timestamp ON enhanced_transactions(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_token ON enhanced_transactions(token_address)"
        )

        conn.commit()
        conn.close()
        logger.info("Enhanced database initialized successfully")

    async def analyze_addresses(
        self, addresses: List[str], chains: List[int] = None
    ) -> Dict[str, Any]:
        """Analyze multiple addresses with enhanced features."""
        if not chains:
            chains = list(self.config["rpc_urls"].keys())

        results = {}

        for address in addresses:
            logger.info(f"Analyzing address: {address}")
            address_results = await self._analyze_single_address(address, chains)
            results[address] = address_results

        return results

    async def _analyze_single_address(
        self, address: str, chains: List[int]
    ) -> Dict[str, Any]:
        """Analyze a single address with enhanced parsing."""
        address_results = {
            "address": address,
            "chains": {},
            "summary": {
                "total_transactions": 0,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "total_gas_costs": 0.0,
                "categories": {},
                "token_summary": {},
            },
        }

        for chain_id in chains:
            chain_name = self._get_chain_name(chain_id)
            logger.info(f"Scanning {address} on {chain_name} (chain {chain_id})")

            # Get current block first
            try:
                w3 = self.chain_scanner.web3_instances.get(chain_id)
                if w3:
                    end_block = w3.eth.block_number
                else:
                    end_block = start_block
            except:
                end_block = start_block

            # Get last scanned block
            start_block = self.block_tracker.get_last_scanned_block(
                f"enhanced_onchainden_{address}", str(chain_id), 0
            )

            # Apply test mode offset if configured
            if (
                self.config.get("scan_settings", {}).get("test_mode")
                and start_block == 0
            ):
                offset = self.config.get("scan_settings", {}).get(
                    "start_block_offset", 1000
                )
                start_block = max(0, end_block - offset)
                logger.info(
                    f"Test mode: Starting scan from block {start_block} (offset: {offset})"
                )

            if start_block >= end_block:
                logger.info(f"No new blocks to scan for {address} on {chain_name}")
                continue

            # Get transactions
            transactions = await self.chain_scanner.get_transactions(
                address, chain_id, start_block, end_block
            )

            # Categorize transactions
            categorized_txs = []
            for tx in transactions:
                receipt = tx.get("receipt", {})
                gas_price_eth = tx.get("gasPriceEth", 0)

                categorized_tx = self.categorizer.categorize_transaction(
                    tx, receipt, chain_name, gas_price_eth
                )
                categorized_txs.append(categorized_tx)

                # Store in database
                self._store_enhanced_transaction(categorized_tx)

            # Update block tracker
            if transactions:
                self.block_tracker.update_last_scanned_block(
                    f"enhanced_onchainden_{address}", str(chain_id), end_block
                )

            # Store results
            address_results["chains"][chain_name] = {
                "transactions": len(transactions),
                "blocks_scanned": end_block - start_block,
                "last_block": end_block,
            }

            address_results["summary"]["total_transactions"] += len(transactions)

        # Calculate enhanced summary statistics
        address_results["summary"] = self._calculate_enhanced_address_summary(address)

        return address_results

    def _get_chain_name(self, chain_id: int) -> str:
        """Get human-readable chain name."""
        chain_names = {
            1: "Ethereum",
            137: "Polygon",
            8453: "Base",
            42161: "Arbitrum",
            10: "Optimism",
            56: "BSC",
            43114: "Avalanche",
            80001: "Polygon Mumbai",
            11155111: "Sepolia",
        }
        return chain_names.get(chain_id, f"Chain_{chain_id}")

    def _store_enhanced_transaction(self, tx: EnhancedTransaction):
        """Store enhanced transaction in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert events to JSON string
            events_json = json.dumps(tx.events) if tx.events else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO enhanced_transactions (
                    tx_hash, block_number, timestamp, from_address, to_address,
                    value, gas_used, gas_price, gas_cost_eth, gas_cost_usd,
                    chain_id, chain_name, category, subcategory, revenue_type,
                    token_address, token_symbol, token_name, token_decimals,
                    token_amount, usd_value, method_signature, contract_interaction,
                    events, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    tx.tx_hash,
                    tx.block_number,
                    tx.timestamp,
                    tx.from_address,
                    tx.to_address,
                    tx.value,
                    tx.gas_used,
                    tx.gas_price,
                    tx.gas_cost_eth,
                    tx.gas_cost_usd,
                    tx.chain_id,
                    tx.chain_name,
                    tx.category,
                    tx.subcategory,
                    tx.revenue_type,
                    tx.token_address,
                    tx.token_symbol,
                    tx.token_name,
                    tx.token_decimals,
                    tx.token_amount,
                    tx.usd_value,
                    tx.method_signature,
                    tx.contract_interaction,
                    events_json,
                    tx.notes,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing enhanced transaction {tx.tx_hash}: {e}")

    def _calculate_enhanced_address_summary(self, address: str) -> Dict[str, Any]:
        """Calculate enhanced summary statistics for an address."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total transactions
            cursor.execute(
                "SELECT COUNT(*) FROM enhanced_transactions WHERE from_address = ? OR to_address = ?",
                (address.lower(), address.lower()),
            )
            total_transactions = cursor.fetchone()[0]

            # Get category breakdown
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM enhanced_transactions 
                WHERE from_address = ? OR to_address = ?
                GROUP BY category
            """,
                (address.lower(), address.lower()),
            )
            categories = dict(cursor.fetchall())

            # Get gas costs
            cursor.execute(
                """
                SELECT SUM(gas_cost_eth) as total_gas
                FROM enhanced_transactions 
                WHERE from_address = ? OR to_address = ?
            """,
                (address.lower(), address.lower()),
            )
            gas_result = cursor.fetchone()
            total_gas_costs = gas_result[0] if gas_result[0] else 0.0

            # Get token summary
            cursor.execute(
                """
                SELECT token_symbol, COUNT(*) as count, SUM(CAST(token_amount AS REAL)) as total_amount
                FROM enhanced_transactions 
                WHERE (from_address = ? OR to_address = ?) AND token_symbol IS NOT NULL
                GROUP BY token_symbol
            """,
                (address.lower(), address.lower()),
            )
            token_summary = {}
            for row in cursor.fetchall():
                token_summary[row[0]] = {"count": row[1], "total_amount": row[2]}

            conn.close()

            return {
                "total_transactions": total_transactions,
                "total_revenue": 0.0,  # TODO: Calculate from categorized transactions
                "total_expenses": 0.0,  # TODO: Calculate from categorized transactions
                "total_gas_costs": total_gas_costs,
                "categories": categories,
                "token_summary": token_summary,
            }

        except Exception as e:
            logger.error(f"Error calculating enhanced summary for {address}: {e}")
            return {
                "total_transactions": 0,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "total_gas_costs": 0.0,
                "categories": {},
                "token_summary": {},
            }

    def generate_enhanced_report(
        self, addresses: List[str], output_format: str = "csv"
    ) -> str:
        """Generate enhanced analysis report."""
        if output_format == "csv":
            return self._generate_enhanced_csv_report(addresses)
        elif output_format == "json":
            return self._generate_enhanced_json_report(addresses)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_enhanced_csv_report(self, addresses: List[str]) -> str:
        """Generate enhanced CSV report."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Get all enhanced transactions for specified addresses
            placeholders = ",".join(["?" for _ in addresses])
            query = f"""
                SELECT * FROM enhanced_transactions 
                WHERE from_address IN ({placeholders}) OR to_address IN ({placeholders})
                ORDER BY timestamp DESC
            """

            df = pd.read_sql_query(query, conn, params=addresses + addresses)
            conn.close()

            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/enhanced_onchainden_report_{timestamp}.csv"

            os.makedirs("reports", exist_ok=True)
            df.to_csv(filename, index=False)

            logger.info(f"Enhanced CSV report saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating enhanced CSV report: {e}")
            return ""

    def _generate_enhanced_json_report(self, addresses: List[str]) -> str:
        """Generate enhanced JSON report."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all enhanced transactions for specified addresses
            placeholders = ",".join(["?" for _ in addresses])
            query = f"""
                SELECT * FROM enhanced_transactions 
                WHERE from_address IN ({placeholders}) OR to_address IN ({placeholders})
                ORDER BY timestamp DESC
            """

            cursor.execute(query, addresses + addresses)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            transactions = []
            for row in rows:
                tx_dict = dict(zip(columns, row))
                # Parse events JSON
                if tx_dict.get("events"):
                    try:
                        tx_dict["events"] = json.loads(tx_dict["events"])
                    except:
                        tx_dict["events"] = []
                transactions.append(tx_dict)

            conn.close()

            # Create enhanced report structure
            report = {
                "generated_at": datetime.now().isoformat(),
                "addresses_analyzed": addresses,
                "total_transactions": len(transactions),
                "transactions": transactions,
                "summary_by_address": {},
                "chain_summary": {},
                "category_summary": {},
                "token_summary": {},
            }

            # Add summary for each address
            for address in addresses:
                report["summary_by_address"][
                    address
                ] = self._calculate_enhanced_address_summary(address)

            # Add chain summary
            chain_counts = {}
            category_counts = {}
            token_counts = {}

            for tx in transactions:
                # Chain summary
                chain = tx.get("chain_name", "Unknown")
                chain_counts[chain] = chain_counts.get(chain, 0) + 1

                # Category summary
                category = tx.get("category", "Unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

                # Token summary
                token = tx.get("token_symbol", "Native")
                if token:
                    if token not in token_counts:
                        token_counts[token] = {"count": 0, "total_amount": 0}
                    token_counts[token]["count"] += 1
                    if tx.get("token_amount"):
                        try:
                            token_counts[token]["total_amount"] += float(
                                tx["token_amount"]
                            )
                        except:
                            pass

            report["chain_summary"] = chain_counts
            report["category_summary"] = category_counts
            report["token_summary"] = token_counts

            # Save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/enhanced_onchainden_report_{timestamp}.json"

            os.makedirs("reports", exist_ok=True)
            with open(filename, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Enhanced JSON report saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating enhanced JSON report: {e}")
            return ""


async def main():
    """Main function to run the enhanced OnchainDen analyzer."""
    # Example configuration
    config = {
        "rpc_urls": {
            1: "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
            137: "https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY",
            8453: "https://mainnet.base.org",
            42161: "https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY",
        },
        "api_keys": {
            "etherscan": "YOUR_ETHERSCAN_KEY",
            "polygonscan": "YOUR_POLYGONSCAN_KEY",
            "basescan": "YOUR_BASESCAN_KEY",
            "arbiscan": "YOUR_ARBISCAN_KEY",
        },
        "addresses": [
            "0x90a48d5cf7343b08da12e067680b4c6dbfe551be",
            "0x6268d07327f4fb7380732dc6d63d95f88c0e083b",
        ],
        "revenue_addresses": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "expense_addresses": [],
        "ignored_addresses": [],
        "custom_rules": [
            {
                "type": "address_pattern",
                "pattern": "0x1234",
                "category": "Custom",
                "subcategory": "Special",
            },
            {
                "type": "method_signature",
                "signature": "0xa9059cbb",
                "category": "Token Transfer",
                "subcategory": "ERC-20",
            },
        ],
    }

    # Save config
    os.makedirs("config", exist_ok=True)
    with open("config/enhanced_onchainden_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Initialize enhanced analyzer
    analyzer = EnhancedOnchainDenAnalyzer("config/enhanced_onchainden_config.json")

    # Analyze addresses
    addresses = config["addresses"]
    logger.info(f"Starting enhanced analysis of {len(addresses)} addresses")

    results = await analyzer.analyze_addresses(addresses)

    # Generate enhanced reports
    logger.info("Generating enhanced reports...")
    csv_report = analyzer.generate_enhanced_report(addresses, "csv")
    json_report = analyzer.generate_enhanced_report(addresses, "json")

    logger.info("Enhanced analysis complete!")
    logger.info(f"Enhanced CSV report: {csv_report}")
    logger.info(f"Enhanced JSON report: {json_report}")

    # Print enhanced summary
    for address, result in results.items():
        print(f"\nAddress: {address}")
        print(f"Total transactions: {result['summary']['total_transactions']}")
        print(f"Total gas costs: {result['summary']['total_gas_costs']:.6f} ETH")
        print(f"Categories: {result['summary']['categories']}")
        print(f"Token summary: {result['summary']['token_summary']}")


if __name__ == "__main__":
    asyncio.run(main())
