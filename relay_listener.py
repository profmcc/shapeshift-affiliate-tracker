#!/usr/bin/env python3
"""
Relay Affiliate Fee Listener
============================

A standalone Python application for monitoring Relay transactions and tracking 
ShapeShift affiliate fees across multiple blockchain networks.

Features:
- Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche)
- CSV-based data storage
- Automatic affiliate fee detection
- Block tracking and progress persistence
- Rate limiting and error handling
"""

import os
import csv
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from web3 import Web3
from web3.exceptions import BlockNotFound, TransactionNotFound

# Import configuration
from config.config_loader import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RelayListener:
    """Main listener for Relay transactions with ShapeShift affiliate fees"""

    def __init__(self, config_path: str = None):
        """Initialize the Relay listener"""
        self.config = get_config(config_path)
        
        # Validate API key
        self.alchemy_api_key = self.config.get_alchemy_api_key()
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in configuration")
        
        # Get ShapeShift affiliate addresses
        self.shapeshift_affiliates = self.config.get_all_shapeshift_addresses()
        if not self.shapeshift_affiliates:
            raise ValueError("No ShapeShift affiliate addresses found in configuration")
        
        logger.info(f"Loaded {len(self.shapeshift_affiliates)} ShapeShift affiliate addresses")
        
        # Get storage paths
        self.csv_dir = self.config.get_storage_path("csv_directory")
        self.relay_csv = self.config.get_storage_path("file_pattern", "relay")
        self.block_tracker_csv = self.config.get_storage_path("file_pattern", "block_tracker").format(protocol="relay")
        
        # Get listener configuration
        self.listener_config = self.config.get_listener_config("relay")
        self.chunk_size = self.listener_config.get("chunk_size", 100)
        self.delay = self.listener_config.get("delay", 0.5)
        self.max_blocks = self.listener_config.get("max_blocks", 1000)
        
        # Get event signatures
        self.affiliate_fee_event = self.config.get_event_signature("relay", "affiliate_fee")
        self.transfer_event = self.config.get_event_signature("relay", "transfer")
        
        # Get threshold
        self.min_volume_usd = self.config.get_threshold("minimum_volume_usd")
        
        # Initialize Web3 connections
        self.web3_connections = {}
        self._initialize_web3_connections()
        
        # Initialize CSV structure
        self.init_csv_structure()
        
        logger.info("RelayListener initialized successfully")

    def _initialize_web3_connections(self):
        """Initialize Web3 connections for all supported chains"""
        supported_chains = self.config.get_supported_chains()
        
        for chain_name in supported_chains:
            try:
                chain_config = self.config.get_chain_config(chain_name)
                if chain_config and "rpc_url" in chain_config:
                    rpc_url = chain_config["rpc_url"]
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    
                    if w3.is_connected():
                        self.web3_connections[chain_name] = {
                            "web3": w3,
                            "config": chain_config,
                            "router_address": self.config.get_contract_address("relay", chain_name),
                        }
                        logger.info(f"Connected to {chain_name}: {chain_config['name']}")
                    else:
                        logger.warning(f"Failed to connect to {chain_name}")
                        
            except Exception as e:
                logger.error(f"Error initializing {chain_name}: {e}")
        
        if not self.web3_connections:
            raise ValueError("No Web3 connections established")
        
        logger.info(f"Initialized {len(self.web3_connections)} chain connections")

    def init_csv_structure(self):
        """Initialize CSV file structure for Relay data"""
        os.makedirs(self.csv_dir, exist_ok=True)
        
        # Main Relay transactions CSV
        relay_csv_path = os.path.join(self.csv_dir, self.relay_csv)
        if not os.path.exists(relay_csv_path):
            headers = [
                "tx_hash",
                "chain",
                "block_number",
                "timestamp",
                "from_address",
                "to_address",
                "affiliate_address",
                "affiliate_fee_amount",
                "affiliate_fee_token",
                "affiliate_fee_usd",
                "volume_amount",
                "volume_token",
                "volume_usd",
                "gas_used",
                "gas_price",
                "created_at",
            ]
            
            with open(relay_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created Relay transactions CSV: {relay_csv_path}")
        
        # Block tracker CSV
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)
        if not os.path.exists(block_tracker_path):
            headers = [
                "chain",
                "last_processed_block",
                "last_processed_date",
                "total_blocks_processed",
            ]
            with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"Created Relay block tracker CSV: {block_tracker_path}")

    def get_last_processed_block(self, chain: str) -> int:
        """Get the last processed block for a specific chain"""
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)
        
        if not os.path.exists(block_tracker_path):
            return 0
        
        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["chain"] == chain:
                        return int(row["last_processed_block"])
        except Exception as e:
            logger.error(f"Error reading block tracker for {chain}: {e}")
        
        # Return start block from config if no tracker found
        chain_config = self.config.get_chain_config(chain)
        return chain_config.get("start_block", 0)

    def update_block_tracker(self, chain: str, block_number: int):
        """Update the block tracker with the latest processed block"""
        block_tracker_path = os.path.join(self.csv_dir, self.block_tracker_csv)
        
        # Read existing data
        rows = []
        try:
            with open(block_tracker_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            pass
        
        # Update or add entry for this chain
        updated = False
        for row in rows:
            if row["chain"] == chain:
                row["last_processed_block"] = str(block_number)
                row["last_processed_date"] = datetime.now().isoformat()
                row["total_blocks_processed"] = str(int(row.get("total_blocks_processed", 0)) + self.chunk_size)
                updated = True
                break
        
        if not updated:
            rows.append({
                "chain": chain,
                "last_processed_block": str(block_number),
                "last_processed_date": datetime.now().isoformat(),
                "total_blocks_processed": str(self.chunk_size)
            })
        
        # Write updated data
        with open(block_tracker_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["chain", "last_processed_block", "last_processed_date", "total_blocks_processed"])
            writer.writeheader()
            writer.writerows(rows)

    def process_chain(self, chain_name: str, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """Process a range of blocks on a specific chain"""
        if chain_name not in self.web3_connections:
            logger.warning(f"No Web3 connection for {chain_name}")
            return []
        
        connection = self.web3_connections[chain_name]
        w3 = connection["web3"]
        router_address = connection["router_address"]
        
        if router_address == "0x0000000000000000000000000000000000000000":
            logger.info(f"Relay not deployed on {chain_name}")
            return []
        
        events = []
        
        try:
            # Get logs for the block range - only filter by event signature to avoid RPC limits
            logs = w3.eth.get_logs({
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": router_address,
                "topics": [
                    w3.keccak(text=self.affiliate_fee_event).hex()
                ]
            })
            
            logger.info(f"Found {len(logs)} logs on {chain_name}")
            
            for log in logs:
                try:
                    # Parse the log data
                    event_data = self._parse_affiliate_fee_log(log, w3)
                    if event_data:
                        event_data["chain"] = chain_name
                        events.append(event_data)
                        
                except Exception as e:
                    logger.error(f"Error parsing log {log['transactionHash'].hex()}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error processing {chain_name} blocks {start_block}-{end_block}: {e}")
        
        return events

    def _parse_affiliate_fee_log(self, log: Dict[str, Any], w3: Web3) -> Optional[Dict[str, Any]]:
        """Parse an affiliate fee log entry"""
        try:
            tx_hash = log["transactionHash"].hex()
            block_number = log["blockNumber"]
            
            # Get transaction details
            tx = w3.eth.get_transaction(tx_hash)
            if not tx:
                return None
            
            # Get block details
            block = w3.eth.get_block(block_number)
            if not block:
                return None
            
            # Parse log topics and data
            topics = log["topics"]
            if len(topics) < 5:
                return None
            
            # Extract addresses and amounts from topics
            affiliate_address = "0x" + topics[1].hex()[-40:]
            user_address = "0x" + topics[2].hex()[-40:]
            amount = int(topics[3].hex(), 16)
            token_address = "0x" + topics[4].hex()[-40:]
            
            # Check if this is a ShapeShift affiliate
            if affiliate_address.lower() not in [addr.lower() for addr in self.shapeshift_affiliates]:
                return None
            
            # Get token symbol (simplified)
            token_symbol = self._get_token_symbol(token_address, w3)
            
            # Calculate USD values (placeholder - would need price oracle)
            amount_usd = 0.0  # TODO: Implement price conversion
            
            return {
                "tx_hash": tx_hash,
                "block_number": block_number,
                "timestamp": block["timestamp"],
                "from_address": user_address,
                "to_address": affiliate_address,
                "affiliate_address": affiliate_address,
                "affiliate_fee_amount": amount,
                "affiliate_fee_token": token_symbol,
                "affiliate_fee_usd": amount_usd,
                "volume_amount": amount,  # Simplified - same as fee for now
                "volume_token": token_symbol,
                "volume_usd": amount_usd,
                "gas_used": tx.get("gas", 0),
                "gas_price": tx.get("gasPrice", 0),
                "created_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error parsing affiliate fee log: {e}")
            return None

    def _get_token_symbol(self, token_address: str, w3: Web3) -> str:
        """Get token symbol from contract address"""
        try:
            # ERC20 token contract ABI (minimal)
            abi = [
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
            ]
            
            contract = w3.eth.contract(address=token_address, abi=abi)
            symbol = contract.functions.symbol().call()
            return symbol
        except:
            # Return shortened address if symbol lookup fails
            return token_address[:10] + "..."

    def save_events_to_csv(self, events: List[Dict[str, Any]]):
        """Save events to CSV file"""
        if not events:
            return
        
        csv_file = os.path.join(self.csv_dir, self.relay_csv)
        
        try:
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "tx_hash", "chain", "block_number", "timestamp", "from_address",
                    "to_address", "affiliate_address", "affiliate_fee_amount",
                    "affiliate_fee_token", "affiliate_fee_usd", "volume_amount",
                    "volume_token", "volume_usd", "gas_used", "gas_price", "created_at"
                ])
                
                for event in events:
                    writer.writerow(event)
            
            logger.info(f"Saved {len(events)} Relay affiliate events to CSV")
            
        except Exception as e:
            logger.error(f"Error saving events to CSV: {e}")

    def run_listener(self, target_chains: List[str] = None) -> int:
        """Run the Relay listener for all supported chains"""
        if target_chains:
            chains_to_process = [chain for chain in target_chains if chain in self.web3_connections]
        else:
            chains_to_process = list(self.web3_connections.keys())
        
        if not chains_to_process:
            logger.warning("No chains available for processing")
            return 0
        
        logger.info(f"Starting Relay listener for chains: {chains_to_process}")
        logger.info(f"Max blocks per scan: {self.max_blocks}")
        
        total_events = 0
        
        for chain_name in chains_to_process:
            try:
                # Get last processed block
                last_block = self.get_last_processed_block(chain_name)
                current_block = self.web3_connections[chain_name]["web3"].eth.block_number
                
                # Calculate block range
                start_block = last_block + 1
                end_block = min(current_block, start_block + self.max_blocks)
                
                if start_block > end_block:
                    logger.info(f"{chain_name}: No new blocks to process")
                    continue
                
                logger.info(f"{chain_name}: Processing blocks {start_block} to {end_block}")
                
                # Process blocks in chunks
                for chunk_start in range(start_block, end_block, self.chunk_size):
                    chunk_end = min(chunk_start + self.chunk_size, end_block)
                    
                    events = self.process_chain(chain_name, chunk_start, chunk_end)
                    if events:
                        self.save_events_to_csv(events)
                        total_events += len(events)
                    
                    # Update block tracker
                    self.update_block_tracker(chain_name, chunk_end)
                    
                    # Rate limiting
                    time.sleep(self.delay)
                
                logger.info(f"{chain_name}: Completed processing")
                
            except Exception as e:
                logger.error(f"Error processing {chain_name}: {e}")
                continue
        
        logger.info(f"Relay listener completed. Total events found: {total_events}")
        return total_events

    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the CSV data"""
        relay_csv_path = os.path.join(self.csv_dir, self.relay_csv)
        
        if not os.path.exists(relay_csv_path):
            return {"total_transactions": 0, "chains": {}}
        
        try:
            with open(relay_csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            stats = {
                "total_transactions": len(rows),
                "chains": {},
                "affiliate_addresses": {},
            }
            
            for row in rows:
                chain = row.get("chain", "unknown")
                affiliate = row.get("affiliate_address", "unknown")
                
                # Count by chain
                if chain not in stats["chains"]:
                    stats["chains"][chain] = 0
                stats["chains"][chain] += 1
                
                # Count by affiliate address
                if affiliate not in stats["affiliate_addresses"]:
                    stats["affiliate_addresses"][affiliate] = 0
                stats["affiliate_addresses"][affiliate] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting CSV stats: {e}")
            return {"total_transactions": 0, "chains": {}}


def main():
    """Main function to run the Relay listener"""
    parser = argparse.ArgumentParser(description="Relay Affiliate Fee Listener")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--chains", help="Comma-separated list of chains to monitor")
    args = parser.parse_args()
    
    try:
        # Parse target chains
        target_chains = None
        if args.chains:
            target_chains = [chain.strip() for chain in args.chains.split(",")]
        
        # Initialize listener
        listener = RelayListener(args.config)
        
        # Run listener
        total_events = listener.run_listener(target_chains)
        
        # Print statistics
        stats = listener.get_csv_stats()
        print(f"\n📊 Relay Listener Statistics:")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Transactions by chain:")
        for chain, count in stats["chains"].items():
            print(f"     {chain}: {count}")
        print(f"   Affiliate addresses found:")
        for addr, count in stats["affiliate_addresses"].items():
            print(f"     {addr}: {count}")
        
        print(f"\n✅ Relay listener completed successfully!")
        print(f"   Total events found: {total_events}")
        
    except Exception as e:
        logger.error(f"Error running Relay listener: {e}")
        raise


if __name__ == "__main__":
    main()
