#!/usr/bin/env python3
"""
Optimized Portals Affiliate Fee Listener
Uses event-based scanning with proper rate limiting to avoid timeouts.
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


class OptimizedPortalsListener:
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
                "chunk_size": 10,  # Much smaller chunks
                "delay": 2.0,  # Longer delays
                "last_processed_block": 22774492,
            },
            "base": {
                "name": "Base",
                "chain_id": 8453,
                "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
                "chunk_size": 20,
                "delay": 1.5,
                "last_processed_block": 0,
            },
        }

        # ERC-20 Transfer event signature
        self.transfer_signature = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

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
                input_token_name TEXT,
                output_token_name TEXT,
                affiliate_token_name TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain)
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

    def fetch_portals_events_optimized(
        self, chain_name: str, blocks_to_scan: int = 1000
    ) -> List[Dict]:
        """Fetch Portals events using optimized event-based scanning"""
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

            # Limit the scan to avoid timeouts
            if latest_block - start_block > 10000:
                start_block = latest_block - 10000
                logger.info(f"⚠️  Limiting scan to last 10,000 blocks to avoid timeout")

            events = []
            current_block = start_block
            chunk_size = chain_config["chunk_size"]

            while current_block <= latest_block:
                end_block = min(current_block + chunk_size - 1, latest_block)

                try:
                    # Use event-based scanning instead of full block scanning
                    # Look for ERC-20 transfers to ShapeShift affiliate address
                    affiliate_address = self.shapeshift_affiliates.get(
                        chain_config["chain_id"]
                    )
                    if not affiliate_address:
                        current_block = end_block + 1
                        continue

                    # Create filter for ERC-20 transfers to affiliate address
                    filter_params = {
                        "fromBlock": current_block,
                        "toBlock": end_block,
                        "topics": [
                            self.transfer_signature,  # Transfer event signature
                            None,  # From address (any)
                            "0x"
                            + "0" * 24
                            + affiliate_address[2:],  # To address (affiliate)
                        ],
                    }

                    logs = w3.eth.get_logs(filter_params)

                    for log in logs:
                        try:
                            # Get transaction receipt for additional context
                            receipt = w3.eth.get_transaction_receipt(
                                log["transactionHash"]
                            )
                            block = w3.eth.get_block(log["blockNumber"])

                            # Extract trading pair information
                            pair_info = self.extract_trading_pair_from_receipt(receipt)

                            # Parse transfer amount
                            amount = self.parse_transfer_amount(log["data"])

                            event_data = {
                                "chain": chain_config["name"],
                                "tx_hash": log["transactionHash"].hex(),
                                "block_number": log["blockNumber"],
                                "block_timestamp": block["timestamp"],
                                "input_token": pair_info["input_token"],
                                "input_amount": pair_info["input_amount"],
                                "output_token": pair_info["output_token"],
                                "output_amount": pair_info["output_amount"],
                                "sender": receipt["from"],
                                "broadcaster": None,
                                "recipient": None,
                                "partner": affiliate_address,
                                "affiliate_token": log["address"],
                                "affiliate_amount": amount,
                                "affiliate_fee_usd": pair_info["affiliate_fee_usd"],
                                "volume_usd": pair_info["volume_usd"],
                                "input_token_name": self.get_token_name(
                                    pair_info["input_token"]
                                ),
                                "output_token_name": self.get_token_name(
                                    pair_info["output_token"]
                                ),
                                "affiliate_token_name": self.get_token_name(
                                    log["address"]
                                ),
                            }

                            events.append(event_data)
                            logger.info(
                                f"   ✅ Found ShapeShift Portals transaction: {log['transactionHash'].hex()}"
                            )

                        except Exception as e:
                            logger.warning(f"Error processing log: {e}")
                            continue

                    if current_block % 100 == 0:
                        logger.info(
                            f"   📊 Processed {current_block - start_block} blocks..."
                        )

                    current_block = end_block + 1
                    time.sleep(chain_config["delay"])  # Rate limiting

                except Exception as e:
                    logger.error(
                        f"Error fetching logs for blocks {current_block}-{end_block}: {e}"
                    )
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        logger.warning("Rate limit hit, waiting 30 seconds...")
                        time.sleep(30.0)  # Wait longer for rate limits
                    current_block = end_block + 1
                    continue

            # Update last processed block
            chain_config["last_processed_block"] = latest_block

            return events

        except Exception as e:
            logger.error(f"Error fetching Portals events for {chain_name}: {e}")
            return []

    def extract_trading_pair_from_receipt(self, receipt: Dict) -> Dict:
        """Extract trading pair information from transaction receipt with better volume detection"""
        result = {
            "input_token": "",
            "output_token": "",
            "input_amount": "0",
            "output_amount": "0",
            "affiliate_token": "",
            "affiliate_amount": "0",
            "volume_usd": 0.0,
            "affiliate_fee_usd": 0.0,
        }

        try:
            # Look for ERC-20 transfers to identify trading pairs
            transfers = []
            affiliate_transfers = []

            for log in receipt["logs"]:
                if (
                    log.get("topics")
                    and len(log["topics"]) == 3
                    and log["topics"][0].hex() == self.transfer_signature
                ):
                    from_addr = "0x" + log["topics"][1].hex()[-40:]
                    to_addr = "0x" + log["topics"][2].hex()[-40:]
                    token_addr = log["address"]
                    amount = self.parse_transfer_amount(log["data"])

                    transfer = {
                        "from": from_addr,
                        "to": to_addr,
                        "token": token_addr,
                        "amount": amount,
                    }
                    transfers.append(transfer)

                    # Track affiliate transfers separately
                    affiliate_addresses = [
                        addr.lower() for addr in self.shapeshift_affiliates.values()
                    ]
                    if to_addr.lower() in affiliate_addresses:
                        affiliate_transfers.append(transfer)

            # Analyze transfer patterns to determine trading flow
            if len(transfers) >= 2:
                # Sort transfers by amount to identify input/output
                transfers_by_amount = sorted(
                    transfers, key=lambda x: int(x["amount"]), reverse=True
                )

                # Filter out affiliate transfers from main trading pair detection
                non_affiliate_transfers = [
                    t for t in transfers if t not in affiliate_transfers
                ]

                if len(non_affiliate_transfers) >= 2:
                    # Usually the largest non-affiliate transfer is the input (user's trade)
                    # Second largest might be the output
                    result["input_token"] = non_affiliate_transfers[0]["token"]
                    result["input_amount"] = non_affiliate_transfers[0]["amount"]
                    result["output_token"] = non_affiliate_transfers[1]["token"]
                    result["output_amount"] = non_affiliate_transfers[1]["amount"]

                    # Calculate volume using the input token
                    if result["input_amount"] != "0":
                        result["volume_usd"] = self.calculate_volume_usd(
                            result["input_token"], result["input_amount"]
                        )
                        logger.info(
                            f"   📊 Volume: {result['input_amount']} {result['input_token']} = ${result['volume_usd']:.2f}"
                        )

            # Set affiliate information
            if affiliate_transfers:
                affiliate_transfer = affiliate_transfers[0]
                result["affiliate_token"] = affiliate_transfer["token"]
                result["affiliate_amount"] = affiliate_transfer["amount"]

                # Calculate affiliate fee in USD
                if result["affiliate_amount"] != "0":
                    result["affiliate_fee_usd"] = self.calculate_volume_usd(
                        result["affiliate_token"], result["affiliate_amount"]
                    )
                    logger.info(
                        f"   💰 Affiliate fee: {result['affiliate_amount']} {result['affiliate_token']} = ${result['affiliate_fee_usd']:.2f}"
                    )

        except Exception as e:
            logger.warning(f"Error extracting trading pair: {e}")

        return result

    def parse_transfer_amount(self, data: bytes) -> str:
        """Parse transfer amount from log data"""
        try:
            if not data or len(data) == 0:
                return "0"

            # Ensure data is at least 32 bytes
            if len(data) < 32:
                padded_data = data + b"\x00" * (32 - len(data))
            else:
                padded_data = data[:32]

            # Parse as big-endian integer
            amount = int.from_bytes(padded_data, "big")
            return str(amount)
        except Exception as e:
            logger.warning(f"Error parsing transfer amount: {e}")
            return "0"

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
                     affiliate_token, affiliate_amount, affiliate_fee_usd, volume_usd, 
                     input_token_name, output_token_name, affiliate_token_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        event["input_token_name"],
                        event["output_token_name"],
                        event["affiliate_token_name"],
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
            "SELECT COUNT(*) FROM portals_transactions WHERE input_token IS NOT NULL"
        )
        swap_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n📊 Portals Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Swap events: {swap_count}")
        print(f"   Unique chains: {unique_chains}")
        print(f"   Total affiliate fees: ${total_fees:.2f}")
        print(f"   Total volume: ${total_volume:.2f}")

    def run_listener(self, blocks_to_scan: int = 1000):
        """Run the optimized Portals listener"""
        logger.info("🚀 Starting Optimized Portals affiliate fee listener")

        total_events = 0
        for chain_name in self.chains.keys():
            logger.info(f"\n🔍 Processing {chain_name}...")
            events = self.fetch_portals_events_optimized(chain_name, blocks_to_scan)
            self.save_events_to_db(events)
            total_events += len(events)

        logger.info(
            f"\n✅ Optimized Portals listener completed! Found {total_events} total events"
        )
        self.get_database_stats()

    def get_token_name(self, token_address: str) -> str:
        """Get token name from address (simplified version)"""
        # Common token addresses
        token_names = {
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
            "0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8": "USDC",
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",
            "0x514910771AF9Ca656af840dff83E8264EcF986CA": "LINK",
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": "UNI",
            "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": "AAVE",
            "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": "MKR",
            "0x0D8775F648430679A709E98d2b0Cb6250d2887EF": "BAT",
            "0xE41d2489571d322189246DaFA5ebDe1F4699F498": "ZRX",
            "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942": "MANA",
            "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad9eC": "YFI",
            "0x4fE83213D56308330EC302a8BD641f1d0113A4Cc": "NU",
            "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db": "USDT",
            "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db": "USDT",
            "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db": "USDT",
        }

        return token_names.get(token_address, f"Token_{token_address[:8]}")

    def estimate_token_price(self, token_address: str) -> float:
        """Estimate token price in USD (improved version)"""
        # More comprehensive price estimates for common tokens
        price_estimates = {
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": 2000.0,  # WETH
            "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": 2000.0,  # WETH (Arbitrum)
            "0x4200000000000000000000000000000000000006": 2000.0,  # WETH (Optimism)
            "0x4200000000000000000000000000000000000006": 2000.0,  # WETH (Base)
            "0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8": 1.0,  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": 1.0,  # USDT
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": 40000.0,  # WBTC
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": 1.0,  # DAI
            "0x514910771AF9Ca656af840dff83E8264EcF986CA": 15.0,  # LINK
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": 8.0,  # UNI
            "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": 100.0,  # AAVE
            "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": 2000.0,  # MKR
            "0x0D8775F648430679A709E98d2b0Cb6250d2887EF": 0.5,  # BAT
            "0xE41d2489571d322189246DaFA5ebDe1F4699F498": 0.3,  # ZRX
            "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942": 0.4,  # MANA
            "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad9eC": 8000.0,  # YFI
            "0x4fE83213D56308330EC302a8BD641f1d0113A4Cc": 0.1,  # NU
            "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db": 1.0,  # USDT (Polygon)
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174": 1.0,  # USDC (Polygon)
            "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063": 1.0,  # DAI (Polygon)
            "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619": 2000.0,  # WETH (Polygon)
            "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6": 40000.0,  # WBTC (Polygon)
            "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270": 1.0,  # WMATIC
            "0x7F5c764cBc14f9669B88837ca1490cCa17c31607": 1.0,  # USDC (Optimism)
            "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58": 1.0,  # USDT (Optimism)
            "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1": 1.0,  # DAI (Optimism)
            "0x4200000000000000000000000000000000000006": 2000.0,  # WETH (Optimism)
            "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": 1.0,  # USDC (Base)
            "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb": 1.0,  # DAI (Base)
            "0x4200000000000000000000000000000000000006": 2000.0,  # WETH (Base)
            "0x912CE59144191C1204E64559FE8253a0e49E6548": 1.0,  # ARB
            "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f": 40000.0,  # WBTC (Arbitrum)
            "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8": 1.0,  # USDC (Arbitrum)
            "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9": 1.0,  # USDT (Arbitrum)
            "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1": 1.0,  # DAI (Arbitrum)
        }

        return price_estimates.get(
            token_address.lower(), 1.0
        )  # Default to $1 if unknown

    def calculate_volume_usd(self, token_address: str, amount: str) -> float:
        """Calculate volume in USD with improved precision"""
        try:
            if not amount or amount == "0":
                return 0.0

            # Convert amount to float (assuming 18 decimals for most tokens)
            amount_float = float(amount) / 1e18

            # Handle tokens with different decimal places
            if token_address.lower() in [
                "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
                "0xa0b86a33e6441b8c4c8c8c8c8c8c8c8c8c8c8c8",  # USDC
                "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
                "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",  # USDC (Polygon)
                "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063",  # DAI (Polygon)
                "0x7f5c764cbc14f9669b88837ca1490cca17c31607",  # USDC (Optimism)
                "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",  # USDT (Optimism)
                "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",  # DAI (Optimism)
                "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC (Base)
                "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",  # DAI (Base)
                "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8",  # USDC (Arbitrum)
                "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",  # USDT (Arbitrum)
                "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",  # DAI (Arbitrum)
            ]:
                # These tokens use 6 decimals
                amount_float = float(amount) / 1e6

            token_price = self.estimate_token_price(token_address)
            volume_usd = amount_float * token_price

            logger.debug(
                f"Volume calculation: {amount} {token_address} = ${volume_usd:.2f}"
            )
            return volume_usd

        except Exception as e:
            logger.warning(f"Error calculating volume USD for {token_address}: {e}")
            return 0.0


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimized Portals Affiliate Fee Listener"
    )
    parser.add_argument(
        "--blocks", type=int, default=1000, help="Number of blocks to scan"
    )
    args = parser.parse_args()

    listener = OptimizedPortalsListener()
    listener.run_listener(args.blocks)


if __name__ == "__main__":
    main()
