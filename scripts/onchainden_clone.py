#!/usr/bin/env python3
"""
OnchainDen Clone - Transaction Analysis & Revenue Tracking

A comprehensive tool for analyzing Zapper addresses, downloading transactions from multiple chains,
and categorizing them according to configurable rules for revenue analysis.

Features:
- Multi-chain transaction downloading (Ethereum, Base, Arbitrum, Polygon, etc.)
- Configurable transaction categorization rules
- Revenue analysis and reporting
- Token price tracking and USD value calculations
- Export to CSV, JSON, and interactive HTML reports
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
import aiohttp
import aiofiles

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from block_tracker import BlockTracker
from price_cache import PriceCache
from token_lookup_enhanced import TokenLookupEnhanced

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("onchainden.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Represents a blockchain transaction with categorization."""

    tx_hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: str
    gas_used: int
    gas_price: str
    chain_id: int
    chain_name: str
    category: str
    subcategory: str
    revenue_type: str
    token_address: Optional[str]
    token_symbol: Optional[str]
    token_name: Optional[str]
    usd_value: Optional[float]
    notes: str = ""


@dataclass
class AddressConfig:
    """Configuration for an address to track."""

    address: str
    label: str
    chains: List[int]
    revenue_addresses: List[str]
    expense_addresses: List[str]
    ignored_addresses: List[str]
    custom_rules: Dict[str, Any]


class TransactionCategorizer:
    """Categorizes transactions based on configurable rules."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.revenue_addresses = set(config.get("revenue_addresses", []))
        self.expense_addresses = set(config.get("expense_addresses", []))
        self.ignored_addresses = set(config.get("ignored_addresses", []))
        self.custom_rules = config.get("custom_rules", {})

    def categorize_transaction(
        self, tx: Dict[str, Any], chain_name: str
    ) -> Transaction:
        """Categorize a transaction based on rules."""
        # Basic transaction info
        tx_hash = tx.get("hash", "")
        block_number = tx.get("blockNumber", 0)
        timestamp = tx.get("timestamp", 0)
        from_address = tx.get("from", "").lower()
        to_address = tx.get("to", "").lower()
        value = tx.get("value", "0")
        gas_used = tx.get("gasUsed", 0)
        gas_price = tx.get("gasPrice", "0")

        # Determine category based on addresses
        category, subcategory, revenue_type = self._determine_category(
            from_address, to_address, value, chain_name
        )

        # Extract token info if available
        token_address = tx.get("tokenAddress")
        token_symbol = tx.get("tokenSymbol")
        token_name = tx.get("tokenName")

        # Calculate USD value if possible
        usd_value = self._calculate_usd_value(value, token_symbol, chain_name)

        return Transaction(
            tx_hash=tx_hash,
            block_number=block_number,
            timestamp=timestamp,
            from_address=from_address,
            to_address=to_address,
            value=value,
            gas_used=gas_used,
            gas_price=gas_price,
            chain_id=tx.get("chainId", 0),
            chain_name=chain_name,
            category=category,
            subcategory=subcategory,
            revenue_type=revenue_type,
            token_address=token_address,
            token_symbol=token_symbol,
            token_name=token_name,
            usd_value=usd_value,
            notes="",
        )

    def _determine_category(
        self, from_addr: str, to_addr: str, value: str, chain_name: str
    ) -> Tuple[str, str, str]:
        """Determine transaction category based on addresses and rules."""
        # Check if this is a revenue transaction
        if from_addr in self.revenue_addresses:
            return "Revenue", "Incoming", "Primary"
        elif to_addr in self.revenue_addresses:
            return "Revenue", "Outgoing", "Primary"

        # Check if this is an expense transaction
        if from_addr in self.expense_addresses:
            return "Expense", "Outgoing", "Primary"
        elif to_addr in self.expense_addresses:
            return "Expense", "Incoming", "Primary"

        # Check ignored addresses
        if from_addr in self.ignored_addresses or to_addr in self.ignored_addresses:
            return "Ignored", "Internal", "None"

        # Check custom rules
        category = self._apply_custom_rules(from_addr, to_addr, value, chain_name)
        if category:
            return category[0], category[1], "Custom"

        # Default categorization
        if value and int(value) > 0:
            return "Transfer", "External", "None"
        else:
            return "Contract", "Interaction", "None"

    def _apply_custom_rules(
        self, from_addr: str, to_addr: str, value: str, chain_name: str
    ) -> Optional[Tuple[str, str]]:
        """Apply custom categorization rules."""
        for rule in self.custom_rules:
            if rule.get("type") == "address_pattern":
                pattern = rule["pattern"]
                if pattern in from_addr or pattern in to_addr:
                    return rule["category"], rule["subcategory"]

            elif rule.get("type") == "value_threshold":
                threshold = int(rule["threshold"])
                if value and int(value) >= threshold:
                    return rule["category"], rule["subcategory"]

        return None

    def _calculate_usd_value(
        self, value: str, token_symbol: Optional[str], chain_name: str
    ) -> Optional[float]:
        """Calculate USD value of transaction."""
        try:
            if not value or not token_symbol:
                return None

            # Convert wei to ether
            value_eth = float(Web3.from_wei(int(value), "ether"))

            # TODO: Integrate with price cache for real-time pricing
            # For now, return None
            return None

        except (ValueError, TypeError):
            return None


class ChainScanner:
    """Scans blockchain transactions for specific addresses."""

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
                if chain_id in [137, 80001] and geth_poa_middleware:  # Polygon chains
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

                self.web3_instances[chain_id] = w3
                logger.info(f"Connected to chain {chain_id} via {rpc_url}")

            except Exception as e:
                logger.error(f"Failed to connect to chain {chain_id}: {e}")

    async def get_transactions(
        self, address: str, chain_id: int, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """Get transactions for an address on a specific chain."""
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

            # Get transaction count to estimate range
            nonce = w3.eth.get_transaction_count(checksum_address)
            logger.info(
                f"Address {checksum_address} has {nonce} transactions on chain {chain_id}"
            )

            # Scan blocks for transactions
            for block_num in range(start_block, min(end_block + 1, start_block + 1000)):
                try:
                    block = w3.eth.get_block(block_num, full_transactions=True)

                    for tx in block.transactions:
                        if tx["from"].lower() == checksum_address.lower() or (
                            tx["to"] and tx["to"].lower() == checksum_address.lower()
                        ):
                            # Get transaction receipt for gas info
                            receipt = w3.eth.get_transaction_receipt(tx["hash"])

                            tx_data = {
                                "hash": tx["hash"].hex(),
                                "blockNumber": block_num,
                                "timestamp": block.timestamp,
                                "from": tx["from"],
                                "to": tx["to"],
                                "value": str(tx["value"]),
                                "gasUsed": receipt["gasUsed"],
                                "gasPrice": str(tx["gasPrice"]),
                                "chainId": chain_id,
                                "tokenAddress": None,
                                "tokenSymbol": None,
                                "tokenName": None,
                            }

                            transactions.append(tx_data)

                            if len(transactions) % 100 == 0:
                                logger.info(
                                    f"Found {len(transactions)} transactions so far..."
                                )

                except Exception as e:
                    logger.warning(f"Error processing block {block_num}: {e}")
                    continue

                # Limit to prevent overwhelming
                if len(transactions) >= 10000:
                    logger.warning(
                        f"Reached transaction limit for {address} on chain {chain_id}"
                    )
                    break

        except Exception as e:
            logger.error(
                f"Error getting transactions for {address} on chain {chain_id}: {e}"
            )

        return transactions


class OnchainDenAnalyzer:
    """Main analyzer class for OnchainDen clone."""

    def __init__(self, config_path: str = "config/onchainden_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.categorizer = TransactionCategorizer(self.config)
        self.block_tracker = BlockTracker()
        # Initialize price cache with a default API key if available
        try:
            self.price_cache = PriceCache(api_key="demo")
        except:
            self.price_cache = None
        self.token_lookup = EnhancedTokenLookup()

        # Setup chain scanner
        self.chain_scanner = ChainScanner(
            rpc_urls=self.config["rpc_urls"], api_keys=self.config["api_keys"]
        )

        # Database setup
        self.db_path = "databases/onchainden.db"
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
        """Initialize the database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                block_number INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT NOT NULL,
                value TEXT NOT NULL,
                gas_used INTEGER NOT NULL,
                gas_price TEXT NOT NULL,
                chain_id INTEGER NOT NULL,
                chain_name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                revenue_type TEXT NOT NULL,
                token_address TEXT,
                token_symbol TEXT,
                token_name TEXT,
                usd_value REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_address ON transactions(from_address, to_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_category ON transactions(category, revenue_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chain ON transactions(chain_id, chain_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)"
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    async def analyze_addresses(
        self, addresses: List[str], chains: List[int] = None
    ) -> Dict[str, Any]:
        """Analyze multiple addresses across specified chains."""
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
        """Analyze a single address across multiple chains."""
        address_results = {
            "address": address,
            "chains": {},
            "summary": {
                "total_transactions": 0,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "categories": {},
            },
        }

        for chain_id in chains:
            chain_name = self._get_chain_name(chain_id)
            logger.info(f"Scanning {address} on {chain_name} (chain {chain_id})")

            # Get last scanned block
            start_block = self.block_tracker.get_last_scanned_block(
                f"onchainden_{address}", str(chain_id), 0
            )

            # Get current block
            try:
                w3 = self.chain_scanner.web3_instances.get(chain_id)
                if w3:
                    end_block = w3.eth.block_number
                else:
                    end_block = start_block
            except:
                end_block = start_block

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
                categorized_tx = self.categorizer.categorize_transaction(tx, chain_name)
                categorized_txs.append(categorized_tx)

                # Store in database
                self._store_transaction(categorized_tx)

            # Update block tracker
            if transactions:
                self.block_tracker.update_last_scanned_block(
                    f"onchainden_{address}", str(chain_id), end_block
                )

            # Store results
            address_results["chains"][chain_name] = {
                "transactions": len(transactions),
                "blocks_scanned": end_block - start_block,
                "last_block": end_block,
            }

            address_results["summary"]["total_transactions"] += len(transactions)

        # Calculate summary statistics
        address_results["summary"] = self._calculate_address_summary(address)

        return address_results

    def _get_chain_name(self, chain_id: int) -> str:
        """Get human-readable chain name."""
        chain_names = {
            1: "Ethereum",
            137: "Polygon",
            8453: "Base",
            42161: "Arbitrum",
            80001: "Polygon Mumbai",
            11155111: "Sepolia",
        }
        return chain_names.get(chain_id, f"Chain_{chain_id}")

    def _store_transaction(self, tx: Transaction):
        """Store transaction in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO transactions (
                    tx_hash, block_number, timestamp, from_address, to_address,
                    value, gas_used, gas_price, chain_id, chain_name,
                    category, subcategory, revenue_type, token_address,
                    token_symbol, token_name, usd_value, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    tx.chain_id,
                    tx.chain_name,
                    tx.category,
                    tx.subcategory,
                    tx.revenue_type,
                    tx.token_address,
                    tx.token_symbol,
                    tx.token_name,
                    tx.usd_value,
                    tx.notes,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing transaction {tx.tx_hash}: {e}")

    def _calculate_address_summary(self, address: str) -> Dict[str, Any]:
        """Calculate summary statistics for an address."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total transactions
            cursor.execute(
                "SELECT COUNT(*) FROM transactions WHERE from_address = ? OR to_address = ?",
                (address.lower(), address.lower()),
            )
            total_transactions = cursor.fetchone()[0]

            # Get category breakdown
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM transactions 
                WHERE from_address = ? OR to_address = ?
                GROUP BY category
            """,
                (address.lower(), address.lower()),
            )
            categories = dict(cursor.fetchall())

            # Get revenue/expense totals (placeholder for now)
            total_revenue = 0.0
            total_expenses = 0.0

            conn.close()

            return {
                "total_transactions": total_transactions,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Error calculating summary for {address}: {e}")
            return {
                "total_transactions": 0,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "categories": {},
            }

    def generate_report(self, addresses: List[str], output_format: str = "html") -> str:
        """Generate analysis report in specified format."""
        if output_format == "html":
            return self._generate_html_report(addresses)
        elif output_format == "csv":
            return self._generate_csv_report(addresses)
        elif output_format == "json":
            return self._generate_json_report(addresses)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_html_report(self, addresses: List[str]) -> str:
        """Generate interactive HTML report."""
        # This would generate a comprehensive HTML report
        # For now, return a simple placeholder
        return "HTML report generation not yet implemented"

    def _generate_csv_report(self, addresses: List[str]) -> str:
        """Generate CSV report."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Get all transactions for specified addresses
            placeholders = ",".join(["?" for _ in addresses])
            query = f"""
                SELECT * FROM transactions 
                WHERE from_address IN ({placeholders}) OR to_address IN ({placeholders})
                ORDER BY timestamp DESC
            """

            df = pd.read_sql_query(query, conn, params=addresses + addresses)
            conn.close()

            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/onchainden_report_{timestamp}.csv"

            os.makedirs("reports", exist_ok=True)
            df.to_csv(filename, index=False)

            logger.info(f"CSV report saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            return ""

    def _generate_json_report(self, addresses: List[str]) -> str:
        """Generate JSON report."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all transactions for specified addresses
            placeholders = ",".join(["?" for _ in addresses])
            query = f"""
                SELECT * FROM transactions 
                WHERE from_address IN ({placeholders}) OR to_address IN ({placeholders})
                ORDER BY timestamp DESC
            """

            cursor.execute(query, addresses + addresses)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            transactions = []
            for row in rows:
                transactions.append(dict(zip(columns, row)))

            conn.close()

            # Create report structure
            report = {
                "generated_at": datetime.now().isoformat(),
                "addresses_analyzed": addresses,
                "total_transactions": len(transactions),
                "transactions": transactions,
                "summary_by_address": {},
            }

            # Add summary for each address
            for address in addresses:
                report["summary_by_address"][address] = self._calculate_address_summary(
                    address
                )

            # Save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/onchainden_report_{timestamp}.json"

            os.makedirs("reports", exist_ok=True)
            with open(filename, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"JSON report saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
            return ""


async def main():
    """Main function to run the OnchainDen analyzer."""
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
            }
        ],
    }

    # Save config
    os.makedirs("config", exist_ok=True)
    with open("config/onchainden_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Initialize analyzer
    analyzer = OnchainDenAnalyzer("config/onchainden_config.json")

    # Analyze addresses
    addresses = config["addresses"]
    logger.info(f"Starting analysis of {len(addresses)} addresses")

    results = await analyzer.analyze_addresses(addresses)

    # Generate reports
    logger.info("Generating reports...")
    csv_report = analyzer.generate_report(addresses, "csv")
    json_report = analyzer.generate_report(addresses, "json")

    logger.info("Analysis complete!")
    logger.info(f"CSV report: {csv_report}")
    logger.info(f"JSON report: {json_report}")

    # Print summary
    for address, result in results.items():
        print(f"\nAddress: {address}")
        print(f"Total transactions: {result['summary']['total_transactions']}")
        print(f"Categories: {result['summary']['categories']}")


if __name__ == "__main__":
    asyncio.run(main())
