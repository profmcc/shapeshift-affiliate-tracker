#!/usr/bin/env python3
"""
LP Listener - WETH/FOX Liquidity Pool Tracker

Tracks liquidity pool events (mint, burn, swap) for WETH/FOX pairs on:
- Ethereum Mainnet: 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c
- Arbitrum: 0x5f6ce0ca13b87bd738519545d3e018e70e339c24

Features:
- Real-time event monitoring
- Liquidity impact analysis
- DAO ownership tracking
- Price data integration
- Comprehensive reporting
"""

import os
import sys
import sqlite3
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
from web3 import Web3
from eth_abi import decode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("lp_listener.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for a liquidity pool"""

    name: str
    address: str
    chain: str
    rpc_url: str
    weth_address: str
    fox_address: str
    dao_lp_tokens: float
    db_path: str


class LPTracker:
    """Main LP tracking class"""

    def __init__(self):
        self.pools = {
            "ethereum": PoolConfig(
                name="Ethereum WETH/FOX",
                address="0x470e8de2eBaef52014A47Cb5E6aF86884947F08c",
                chain="ethereum",
                rpc_url="https://mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
                weth_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                fox_address="0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d",
                dao_lp_tokens=74219.8483,
                db_path="databases/ethereum_weth_fox_events.db",
            ),
            "arbitrum": PoolConfig(
                name="Arbitrum WETH/FOX",
                address="0x5f6ce0ca13b87bd738519545d3e018e70e339c24",
                chain="arbitrum",
                rpc_url="https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
                weth_address="0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
                fox_address="0xc770eefad204b5180df6a14ee197d99d808ee52d",
                dao_lp_tokens=4414.3394,
                db_path="databases/arbitrum_weth_fox_events.db",
            ),
        }

        # Ensure databases directory exists
        Path("databases").mkdir(exist_ok=True)

        # Load ABI
        self.abi = self._load_abi()

    def _load_abi(self) -> List[Dict]:
        """Load Uniswap V2 Pair ABI"""
        abi_path = "abis/UniswapV2Pair.json"
        try:
            with open(abi_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"ABI file not found at {abi_path}, using minimal ABI")
            return self._get_minimal_abi()

    def _get_minimal_abi(self) -> List[Dict]:
        """Get minimal ABI for Uniswap V2 Pair events"""
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": False, "name": "amount0", "type": "uint256"},
                    {"indexed": False, "name": "amount1", "type": "uint256"},
                ],
                "name": "Mint",
                "type": "event",
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "amount0", "type": "uint256"},
                    {"indexed": False, "name": "amount1", "type": "uint256"},
                ],
                "name": "Burn",
                "type": "event",
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "amount0In", "type": "uint256"},
                    {"indexed": False, "name": "amount1In", "type": "uint256"},
                    {"indexed": False, "name": "amount0Out", "type": "uint256"},
                    {"indexed": False, "name": "amount1Out", "type": "uint256"},
                ],
                "name": "Swap",
                "type": "event",
            },
        ]

    def _create_tables(self, db_path: str):
        """Create database tables"""
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_number INTEGER,
                tx_hash TEXT,
                log_index INTEGER,
                sender TEXT,
                amount0 TEXT,
                amount1 TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS burn (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_number INTEGER,
                tx_hash TEXT,
                log_index INTEGER,
                sender TEXT,
                amount0 TEXT,
                amount1 TEXT,
                to_addr TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS swap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_number INTEGER,
                tx_hash TEXT,
                log_index INTEGER,
                sender TEXT,
                amount0In TEXT,
                amount1In TEXT,
                amount0Out TEXT,
                amount1Out TEXT,
                to_addr TEXT,
                timestamp TEXT
            );
        """
        )
        conn.close()

    def get_web3(self, rpc_url: str) -> Web3:
        """Get Web3 instance"""
        return Web3(Web3.HTTPProvider(rpc_url))

    def get_token_price(self, token_address: str) -> float:
        """Get token price in USD using CoinGecko API"""
        try:
            token_map = {
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "ethereum",  # Ethereum WETH
                "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": "ethereum",  # Arbitrum WETH
                "0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d": "shapeshift-fox-token",  # FOX
                "0xc770eefad204b5180df6a14ee197d99d808ee52d": "shapeshift-fox-token",  # FOX (lowercase)
            }

            if token_address not in token_map:
                return 0

            coin_id = token_map[token_address]
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()
            return data[coin_id]["usd"]
        except Exception as e:
            logger.warning(f"Failed to get price for {token_address}: {e}")
            # Fallback prices
            fallback_prices = {
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": 3500,  # Ethereum WETH
                "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": 3500,  # Arbitrum WETH
                "0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d": 0.15,  # FOX
                "0xc770eefad204b5180df6a14ee197d99d808ee52d": 0.15,  # FOX
            }
            return fallback_prices.get(token_address, 0)

    def get_pool_info(self, pool: PoolConfig) -> Optional[Dict]:
        """Get current pool information"""
        w3 = self.get_web3(pool.rpc_url)

        # Minimal ABI for pool info
        pool_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "_reserve0", "type": "uint112"},
                    {"name": "_reserve1", "type": "uint112"},
                    {"name": "_blockTimestampLast", "type": "uint32"},
                ],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            },
        ]

        try:
            checksum_address = w3.to_checksum_address(pool.address)
            contract = w3.eth.contract(address=checksum_address, abi=pool_abi)

            reserves = contract.functions.getReserves().call()
            total_supply = contract.functions.totalSupply().call()

            return {
                "weth_reserve": reserves[0],
                "fox_reserve": reserves[1],
                "total_supply": total_supply,
                "block_timestamp": reserves[2],
            }
        except Exception as e:
            logger.error(f"Error getting pool info for {pool.name}: {e}")
            return None

    def fetch_events(
        self, pool: PoolConfig, start_block: int, end_block: int
    ) -> Dict[str, int]:
        """Fetch and store LP events"""
        w3 = self.get_web3(pool.rpc_url)
        checksum_address = w3.to_checksum_address(pool.address)
        contract = w3.eth.contract(address=checksum_address, abi=self.abi)

        # Create database tables
        self._create_tables(pool.db_path)
        conn = sqlite3.connect(pool.db_path)
        cur = conn.cursor()

        # Event signatures
        event_map = {
            "Mint": (
                "mint",
                "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
            ),
            "Burn": (
                "burn",
                "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496",
            ),
            "Swap": (
                "swap",
                "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
            ),
        }

        event_counts = {}

        for event_name, (table, event_signature) in event_map.items():
            try:
                topics = [event_signature]
                log_filter = {
                    "address": checksum_address,
                    "topics": topics,
                    "fromBlock": start_block,
                    "toBlock": end_block,
                }

                logger.info(f"Fetching {event_name} events for {pool.name}")
                logs = w3.eth.get_logs(log_filter)

                for log in logs:
                    block = w3.eth.get_block(log["blockNumber"])
                    timestamp = datetime.utcfromtimestamp(
                        block["timestamp"]
                    ).isoformat()

                    if event_name == "Mint":
                        sender = "0x" + log["topics"][1].hex()[-40:]
                        decoded = decode(
                            ["uint256", "uint256"], bytes.fromhex(log["data"].hex()[2:])
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0, amount1, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                log["blockNumber"],
                                log["transactionHash"].hex(),
                                log["logIndex"],
                                sender,
                                str(decoded[0]),
                                str(decoded[1]),
                                timestamp,
                            ),
                        )

                    elif event_name == "Burn":
                        sender = "0x" + log["topics"][1].hex()[-40:]
                        to_addr = "0x" + log["topics"][2].hex()[-40:]
                        data_hex = log["data"].hex()
                        if len(data_hex) % 64 != 0:
                            data_hex = data_hex.zfill(128)
                        decoded = decode(
                            ["uint256", "uint256"], bytes.fromhex(data_hex)
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0, amount1, to_addr, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                log["blockNumber"],
                                log["transactionHash"].hex(),
                                log["logIndex"],
                                sender,
                                str(decoded[0]),
                                str(decoded[1]),
                                to_addr,
                                timestamp,
                            ),
                        )

                    elif event_name == "Swap":
                        sender = "0x" + log["topics"][1].hex()[-40:]
                        to_addr = "0x" + log["topics"][2].hex()[-40:]
                        data_hex = log["data"].hex()
                        if len(data_hex) % 64 != 0:
                            data_hex = data_hex.zfill(256)
                        decoded = decode(
                            ["uint256", "uint256", "uint256", "uint256"],
                            bytes.fromhex(data_hex),
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {table} (block_number, tx_hash, log_index, sender, amount0In, amount1In, amount0Out, amount1Out, to_addr, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                log["blockNumber"],
                                log["transactionHash"].hex(),
                                log["logIndex"],
                                sender,
                                str(decoded[0]),
                                str(decoded[1]),
                                str(decoded[2]),
                                str(decoded[3]),
                                to_addr,
                                timestamp,
                            ),
                        )

                event_counts[event_name] = len(logs)
                logger.info(f"Fetched {len(logs)} {event_name} events for {pool.name}")

            except Exception as e:
                logger.error(f"Error fetching {event_name} events for {pool.name}: {e}")
                event_counts[event_name] = 0

        conn.commit()
        conn.close()
        return event_counts

    def analyze_pool(self, pool: PoolConfig) -> Dict:
        """Analyze pool liquidity and DAO ownership"""
        # Get current pool info
        pool_info = self.get_pool_info(pool)
        if not pool_info:
            return {}

        # Get token prices
        weth_price = self.get_token_price(pool.weth_address)
        fox_price = self.get_token_price(pool.fox_address)

        # Calculate current values
        current_weth_usd = (pool_info["weth_reserve"] / 1e18) * weth_price
        current_fox_usd = (pool_info["fox_reserve"] / 1e18) * fox_price
        current_total_usd = current_weth_usd + current_fox_usd

        # Calculate DAO ownership
        total_supply = pool_info["total_supply"] / 1e18
        dao_percentage = (pool.dao_lp_tokens / total_supply) * 100
        dao_usd_value = current_total_usd * (dao_percentage / 100)

        # Load burn events for liquidity analysis
        conn = sqlite3.connect(pool.db_path)

        # Check if burn table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='burn'"
        )
        if cursor.fetchone():
            burns_df = pd.read_sql_query(
                """
                SELECT 
                    block_number, tx_hash, sender,
                    CAST(amount0 AS REAL) / 1e18 as weth_amount,
                    CAST(amount1 AS REAL) / 1e18 as fox_amount,
                    to_addr, timestamp
                FROM burn 
                ORDER BY block_number ASC
            """,
                conn,
            )
        else:
            # Create empty DataFrame if table doesn't exist
            burns_df = pd.DataFrame()

        conn.close()

        if not burns_df.empty:
            burns_df["timestamp"] = pd.to_datetime(burns_df["timestamp"])
            burns_df["weth_usd"] = burns_df["weth_amount"] * weth_price
            burns_df["fox_usd"] = burns_df["fox_amount"] * fox_price
            burns_df["total_usd"] = burns_df["weth_usd"] + burns_df["fox_usd"]
            burns_df["cumulative_usd"] = burns_df["total_usd"].cumsum()
            total_removed_usd = burns_df["total_usd"].sum()
            original_total_usd = current_total_usd + total_removed_usd
            reduction_percentage = (total_removed_usd / original_total_usd) * 100
        else:
            total_removed_usd = 0
            original_total_usd = current_total_usd
            reduction_percentage = 0

        return {
            "pool_name": pool.name,
            "current_weth": pool_info["weth_reserve"] / 1e18,
            "current_fox": pool_info["fox_reserve"] / 1e18,
            "current_weth_usd": current_weth_usd,
            "current_fox_usd": current_fox_usd,
            "current_total_usd": current_total_usd,
            "dao_lp_tokens": pool.dao_lp_tokens,
            "total_supply": total_supply,
            "dao_percentage": dao_percentage,
            "dao_usd_value": dao_usd_value,
            "total_removed_usd": total_removed_usd,
            "original_total_usd": original_total_usd,
            "reduction_percentage": reduction_percentage,
            "burn_events": len(burns_df) if not burns_df.empty else 0,
        }

    def run_analysis(self, pool_name: str = None) -> None:
        """Run comprehensive LP analysis"""
        pools_to_analyze = [self.pools[pool_name]] if pool_name else self.pools.values()

        for pool in pools_to_analyze:
            logger.info(f"\n{'='*60}")
            logger.info(f"ANALYZING {pool.name.upper()}")
            logger.info(f"{'='*60}")

            analysis = self.analyze_pool(pool)
            if not analysis:
                logger.error(f"Failed to analyze {pool.name}")
                continue

            # Print analysis results
            logger.info(f"\nCurrent Pool Reserves:")
            logger.info(
                f"  WETH: {analysis['current_weth']:.4f} (${analysis['current_weth_usd']:,.2f})"
            )
            logger.info(
                f"  FOX: {analysis['current_fox']:,.2f} (${analysis['current_fox_usd']:,.2f})"
            )
            logger.info(f"  Total: ${analysis['current_total_usd']:,.2f}")

            logger.info(f"\nDAO Ownership:")
            logger.info(f"  DAO LP tokens: {analysis['dao_lp_tokens']:,.2f}")
            logger.info(f"  Total LP supply: {analysis['total_supply']:,.2f}")
            logger.info(f"  DAO percentage: {analysis['dao_percentage']:.2f}%")
            logger.info(f"  DAO USD value: ${analysis['dao_usd_value']:,.2f}")

            logger.info(f"\nLiquidity Analysis:")
            logger.info(f"  Total removed: ${analysis['total_removed_usd']:,.2f}")
            logger.info(f"  Original total: ${analysis['original_total_usd']:,.2f}")
            logger.info(f"  Current total: ${analysis['current_total_usd']:,.2f}")
            logger.info(f"  Reduction: {analysis['reduction_percentage']:.1f}%")
            logger.info(f"  Burn events: {analysis['burn_events']}")

    def run_listener(self, blocks: int = 1000, limit: int = 100) -> None:
        """Run the LP listener to fetch recent events"""
        logger.info(f"Starting LP listener - fetching last {blocks} blocks")

        for pool_name, pool in self.pools.items():
            logger.info(f"\nProcessing {pool.name}...")

            w3 = self.get_web3(pool.rpc_url)
            latest_block = w3.eth.block_number
            start_block = max(0, latest_block - blocks)

            logger.info(f"Fetching events from block {start_block} to {latest_block}")
            event_counts = self.fetch_events(pool, start_block, latest_block)

            logger.info(f"Event counts for {pool.name}:")
            for event_type, count in event_counts.items():
                logger.info(f"  {event_type}: {count}")

        # Run analysis after fetching events
        self.run_analysis()


def main():
    parser = argparse.ArgumentParser(
        description="LP Listener - WETH/FOX Liquidity Pool Tracker"
    )
    parser.add_argument(
        "--blocks", type=int, default=1000, help="Number of blocks to fetch"
    )
    parser.add_argument("--limit", type=int, default=100, help="Limit for analysis")
    parser.add_argument(
        "--pool", choices=["ethereum", "arbitrum"], help="Specific pool to analyze"
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Run analysis only, no event fetching",
    )

    args = parser.parse_args()

    tracker = LPTracker()

    if args.analysis_only:
        tracker.run_analysis(args.pool)
    else:
        tracker.run_listener(args.blocks, args.limit)


if __name__ == "__main__":
    main()
