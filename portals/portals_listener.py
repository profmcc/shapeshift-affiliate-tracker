#!/usr/bin/env python3
"""
CSV-based Portals Affiliate Fee Listener
Tracks ShapeShift affiliate fees from Portals bridge transactions across EVM chains.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via RPC providers
2. Monitors Portals bridge contracts for transaction events
3. Filters for ShapeShift affiliate addresses
4. Extracts bridge data, fees, and affiliate information
5. Saves everything to CSV files for easy analysis

Portals is a cross-chain bridge protocol that enables users to move assets between
different blockchain networks with affiliate fee sharing.
"""

import os
import csv
import time
import json
import requests
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
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
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

        # ShapeShift affiliate addresses by chain
        # These addresses receive affiliate fees from Portals bridge transactions
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",  # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",  # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Base
        }

        # Chain configurations will be set up after methods are defined
        self.chains = {}

        # Set up chains after all methods are available
        logger.info("🔧 About to call _setup_chains")
        self._setup_chains()
        logger.info("🔧 Finished calling _setup_chains")

        # Portals event signatures (keccak256 hashes of event signatures)
        # These identify specific events we want to monitor
        self.event_signatures = {
            "bridge": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # Bridge event
            "affiliate_fee": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Affiliate fee transfer
            "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # ERC-20 transfer
        }

        # Token metadata cache to avoid repeated lookups
        self.token_cache = {}

    def _get_rpc_url(self, chain_name: str) -> str:
        """Get RPC URL for a specific chain - using Alchemy first, then Infura fallback"""
        if self.alchemy_api_key:
            logger.info(f"🔧 Getting RPC URL for {chain_name} (Alchemy)")
            if chain_name == "ethereum":
                return f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif chain_name == "polygon":
                return f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif chain_name == "optimism":
                return f"https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif chain_name == "arbitrum":
                return f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif chain_name == "base":
                return f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        
        # Fallback to Infura
        logger.info(f"🔧 Getting RPC URL for {chain_name} (Infura)")
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
        else:
            raise ValueError(f"Unsupported chain: {chain_name}")

    def _setup_chains(self):
        """Set up chain configurations with RPC connections"""
        chain_configs = {
            "ethereum": {
                "chain_id": 1,
                "name": "Ethereum",
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "portals_contract": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "affiliate_address": self.shapeshift_affiliates[1],
            },
            "polygon": {
                "chain_id": 137,
                "name": "Polygon",
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "portals_contract": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "affiliate_address": self.shapeshift_affiliates[137],
            },
            "optimism": {
                "chain_id": 10,
                "name": "Optimism",
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "portals_contract": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "affiliate_address": self.shapeshift_affiliates[10],
            },
            "arbitrum": {
                "chain_id": 42161,
                "name": "Arbitrum",
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "portals_contract": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "affiliate_address": self.shapeshift_affiliates[42161],
            },
            "base": {
                "chain_id": 8453,
                "name": "Base",
                "portals_router": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "portals_contract": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "affiliate_address": self.shapeshift_affiliates[8453],
            },
        }

        for chain_name, config in chain_configs.items():
            try:
                rpc_url = self._get_rpc_url(chain_name)
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                if w3.is_connected():
                    config["w3"] = w3
                    config["rpc_url"] = rpc_url
                    self.chains[chain_name] = config
                    logger.info(f"✅ Connected to {chain_name} via {rpc_url}")
                else:
                    logger.warning(f"⚠️ Failed to connect to {chain_name}")
            except Exception as e:
                logger.error(f"❌ Error setting up {chain_name}: {e}")

        logger.info(f"🔧 Set up {len(self.chains)} chains: {list(self.chains.keys())}")

    def init_csv_structure(self):
        """Initialize CSV file structure for storing Portals data"""
        os.makedirs(self.csv_dir, exist_ok=True)
        
        # Main transactions CSV
        transactions_path = os.path.join(self.csv_dir, "portals_transactions.csv")
        if not os.path.exists(transactions_path):
            with open(transactions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "tx_hash", "block_number", "timestamp", "chain", "from_address",
                    "to_address", "token_address", "token_symbol", "amount", "amount_usd",
                    "affiliate_address", "affiliate_fee", "affiliate_fee_usd", "bridge_type",
                    "source_chain", "destination_chain", "processed_at"
                ])
            logger.info(f"✅ Created Portals transactions CSV: {transactions_path}")

        # Block tracker CSV
        block_tracker_path = os.path.join(self.csv_dir, "portals_block_tracker.csv")
        if not os.path.exists(block_tracker_path):
            with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "chain", "last_processed_block", "last_processed_timestamp", "status"
                ])
            logger.info(f"✅ Created Portals block tracker CSV: {block_tracker_path}")

    def get_last_processed_block(self, chain_name: str) -> int:
        """Get the last processed block number for a specific chain"""
        block_tracker_path = os.path.join(self.csv_dir, "portals_block_tracker.csv")
        
        if not os.path.exists(block_tracker_path):
            return 0
        
        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["chain"] == chain_name:
                        return int(row["last_processed_block"])
        except Exception as e:
            logger.error(f"❌ Error reading block tracker: {e}")
        
        return 0

    def update_last_processed_block(self, chain_name: str, block_number: int):
        """Update the last processed block number for a specific chain"""
        block_tracker_path = os.path.join(self.csv_dir, "portals_block_tracker.csv")
        
        # Read existing data
        rows = []
        if os.path.exists(block_tracker_path):
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        
        # Update or add entry
        updated = False
        for row in rows:
            if row["chain"] == chain_name:
                row["last_processed_block"] = str(block_number)
                row["last_processed_timestamp"] = datetime.now().isoformat()
                row["status"] = "completed"
                updated = True
                break
        
        if not updated:
            rows.append({
                "chain": chain_name,
                "last_processed_block": str(block_number),
                "last_processed_timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
        
        # Write back to file
        with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "chain", "last_processed_block", "last_processed_timestamp", "status"
            ])
            writer.writeheader()
            writer.writerows(rows)

    def decode_portals_event(self, log: Dict, w3: Web3) -> Optional[Dict]:
        """Decode a Portals event log to extract transaction data"""
        try:
            # Check if this is a Portals-related transaction
            if not log.get("address"):
                return None
            
            # Look for ShapeShift affiliate address in the transaction
            tx_hash = log.get("transactionHash", "")
            if not tx_hash:
                return None
            
            # Get transaction details
            tx = w3.eth.get_transaction(tx_hash)
            if not tx:
                return None
            
            # Check if transaction involves Portals router
            portals_router = None
            for chain_config in self.chains.values():
                if chain_config["portals_router"].lower() == log["address"].lower():
                    portals_router = chain_config
                    break
            
            if not portals_router:
                return None
            
            # Extract basic transaction info
            event_data = {
                "tx_hash": tx_hash.hex(),
                "block_number": log.get("blockNumber", 0),
                "timestamp": 0,  # Will be filled later
                "chain": portals_router["name"].lower(),
                "from_address": tx.get("from", ""),
                "to_address": tx.get("to", ""),
                "token_address": "",  # Will be extracted from logs
                "token_symbol": "",
                "amount": 0,
                "amount_usd": 0,
                "affiliate_address": portals_router["affiliate_address"],
                "affiliate_fee": 0,
                "affiliate_fee_usd": 0,
                "bridge_type": "portals",
                "source_chain": portals_router["name"].lower(),
                "destination_chain": "",  # Would need cross-chain analysis
                "processed_at": datetime.now().isoformat()
            }
            
            # Try to extract token and amount information
            try:
                # Look for ERC-20 transfer events in the same transaction
                tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
                for log_entry in tx_receipt.get("logs", []):
                    if log_entry.get("topics") and len(log_entry["topics"]) > 0:
                        # Check if this is an ERC-20 transfer
                        if log_entry["topics"][0].hex() == self.event_signatures["erc20_transfer"]:
                            # Decode the transfer event
                            try:
                                # ERC-20 Transfer event: Transfer(address from, address to, uint256 value)
                                decoded = decode(
                                    ["address", "address", "uint256"],
                                    bytes.fromhex(log_entry["data"][2:])  # Remove '0x' prefix
                                )
                                from_addr, to_addr, value = decoded
                                
                                # Check if this involves the affiliate address
                                if (from_addr.lower() == portals_router["affiliate_address"].lower() or 
                                    to_addr.lower() == portals_router["affiliate_address"].lower()):
                                    
                                    event_data["token_address"] = log_entry["address"]
                                    event_data["amount"] = value
                                    
                                    # Try to get token symbol
                                    try:
                                        token_contract = w3.eth.contract(
                                            address=log_entry["address"],
                                            abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                        )
                                        event_data["token_symbol"] = token_contract.functions.symbol().call()
                                    except:
                                        event_data["token_symbol"] = "UNKNOWN"
                                    
                                    # If affiliate address is receiving, this is the affiliate fee
                                    if to_addr.lower() == portals_router["affiliate_address"].lower():
                                        event_data["affiliate_fee"] = value
                                        event_data["affiliate_fee_usd"] = 0  # Would need price lookup
                                    
                                    break
                            except Exception as e:
                                logger.debug(f"Could not decode ERC-20 transfer: {e}")
                                continue
            except Exception as e:
                logger.debug(f"Could not get transaction receipt: {e}")
            
            return event_data
            
        except Exception as e:
            logger.error(f"❌ Error decoding Portals event: {e}")
            return None

    def fetch_portals_events(
        self, chain_name: str, from_block: int, to_block: int
    ) -> List[Dict]:
        """Fetch Portals events from a specific chain and block range"""
        if chain_name not in self.chains:
            logger.warning(f"⚠️ Chain {chain_name} not configured")
            return []
        
        chain_config = self.chains[chain_name]
        w3 = chain_config["w3"]
        
        logger.info(f"🔍 Fetching Portals events from {chain_name} blocks {from_block} to {to_block}")
        
        try:
            # Get logs from Portals router contract
            logs = w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": chain_config["portals_router"],
                "topics": []  # Get all events
            })
            
            logger.info(f"📋 Found {len(logs)} logs from Portals router on {chain_name}")
            
            events = []
            for log in logs:
                event_data = self.decode_portals_event(log, w3)
                if event_data:
                    events.append(event_data)
            
            logger.info(f"✅ Extracted {len(events)} Portals events from {chain_name}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error fetching Portals events from {chain_name}: {e}")
            return []

    def save_transactions_to_csv(self, transactions: List[Dict]):
        """Save Portals transactions to CSV file"""
        if not transactions:
            return
        
        csv_file = os.path.join(self.csv_dir, "portals_transactions.csv")
        
        # Read existing data to avoid duplicates
        existing_txs = set()
        if os.path.exists(csv_file):
            with open(csv_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_txs.add(row["tx_hash"])
        
        # Filter out duplicates
        new_transactions = [tx for tx in transactions if tx["tx_hash"] not in existing_txs]
        
        if not new_transactions:
            logger.info("ℹ️ No new transactions to save")
            return
        
        # Append new transactions
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "tx_hash", "block_number", "timestamp", "chain", "from_address",
                "to_address", "token_address", "token_symbol", "amount", "amount_usd",
                "affiliate_address", "affiliate_fee", "affiliate_fee_usd", "bridge_type",
                "source_chain", "destination_chain", "processed_at"
            ])
            
            for tx in new_transactions:
                writer.writerow(tx)
        
        logger.info(f"✅ Saved {len(new_transactions)} new Portals transactions to CSV")

    def process_chain(self, chain_name: str, max_blocks: int = 1000) -> int:
        """Process a specific chain for Portals affiliate events"""
        if chain_name not in self.chains:
            logger.warning(f"⚠️ Chain {chain_name} not configured")
            return 0
        
        chain_config = self.chains[chain_name]
        w3 = chain_config["w3"]
        
        # Get current block
        try:
            current_block = w3.eth.block_number
        except Exception as e:
            logger.error(f"❌ Error getting current block from {chain_name}: {e}")
            return 0
        
        # Get last processed block
        last_processed = self.get_last_processed_block(chain_name)
        start_block = max(last_processed + 1, current_block - max_blocks)
        end_block = current_block
        
        if start_block >= end_block:
            logger.info(f"ℹ️ {chain_name} is up to date (last processed: {last_processed}, current: {current_block})")
            return 0
        
        logger.info(f"🔍 Processing {chain_name} from block {start_block} to {end_block}")
        
        # Fetch events
        events = self.fetch_portals_events(chain_name, start_block, end_block)
        
        if events:
            # Save to CSV
            self.save_transactions_to_csv(events)
            
            # Update last processed block
            self.update_last_processed_block(chain_name, end_block)
            
            logger.info(f"✅ Processed {len(events)} events from {chain_name}")
            return len(events)
        else:
            # Still update the block tracker even if no events found
            self.update_last_processed_block(chain_name, end_block)
            logger.info(f"ℹ️ No events found on {chain_name}, updated block tracker")
            return 0

    def run(self, chains: List[str] = None, max_blocks: int = 1000):
        """Run the Portals listener for specified chains"""
        if chains is None:
            chains = list(self.chains.keys())
        
        logger.info(f"🚀 Starting Portals listener for chains: {chains}")
        
        total_transactions = 0
        
        for chain_name in chains:
            if chain_name in self.chains:
                try:
                    transactions = self.process_chain(chain_name, max_blocks)
                    total_transactions += transactions
                except Exception as e:
                    logger.error(f"❌ Error processing {chain_name}: {e}")
            else:
                logger.warning(f"⚠️ Chain {chain_name} not configured")
        
        logger.info(f"🎯 Portals listener completed. Total transactions: {total_transactions}")
        return total_transactions

    def test_connection(self):
        """Test connection to all configured chains"""
        logger.info("🧪 Testing connections to all chains...")
        
        for chain_name, config in self.chains.items():
            try:
                w3 = config["w3"]
                current_block = w3.eth.block_number
                logger.info(f"✅ {chain_name}: Connected (block {current_block})")
            except Exception as e:
                logger.error(f"❌ {chain_name}: Connection failed - {e}")
        
        logger.info("🧪 Connection test completed")

    def check_addresses(self):
        """Check if affiliate addresses are valid and have balances"""
        logger.info("🔍 Checking affiliate addresses...")
        
        for chain_name, config in self.chains.items():
            try:
                w3 = config["w3"]
                affiliate_address = config["affiliate_address"]
                
                # Check if address is valid
                if not w3.is_address(affiliate_address):
                    logger.warning(f"⚠️ {chain_name}: Invalid affiliate address {affiliate_address}")
                    continue
                
                # Check balance
                balance = w3.eth.get_balance(affiliate_address)
                balance_eth = w3.from_wei(balance, "ether")
                
                logger.info(f"✅ {chain_name}: {affiliate_address} - {balance_eth} ETH")
                
            except Exception as e:
                logger.error(f"❌ {chain_name}: Error checking address - {e}")
        
        logger.info("🔍 Address check completed")


def main():
    """Main function to run the Portals listener"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Portals Listener with Block Override Options"
    )
    parser.add_argument("--max-blocks", type=int, default=1000,
                       help="Maximum blocks to scan per chain")
    parser.add_argument("--chains", nargs="+", 
                       help="Specific chains to process")
    parser.add_argument("--test-connection", action="store_true",
                       help="Test connection to all chains")
    parser.add_argument("--check-addresses", action="store_true",
                       help="Check affiliate addresses")
    
    args = parser.parse_args()
    
    try:
        listener = CSVPortalsListener()
        
        if args.test_connection:
            listener.test_connection()
        elif args.check_addresses:
            listener.check_addresses()
        else:
            # Run the listener
            chains = args.chains if args.chains else None
            total_transactions = listener.run(chains, args.max_blocks)
            
            print(f"\n📊 Portals Listener Statistics:")
            print(f"   Total transactions found: {total_transactions}")
            print(f"   Data saved to: {listener.csv_dir}/")
            print(f"   CSV files: portals_transactions.csv, portals_block_tracker.csv")
            
            if total_transactions > 0:
                print(f"\n✅ Portals listener completed successfully!")
                print(f"📁 Check {listener.csv_dir}/portals_transactions.csv for results")
            else:
                print(f"\n💡 The Portals listener is now working correctly")
                print(f"📁 No transactions found in the specified block range")
        
    except Exception as e:
        logging.error(f"❌ Error running Portals listener: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

