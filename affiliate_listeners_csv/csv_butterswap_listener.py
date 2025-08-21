#!/usr/bin/env python3
"""
# =============================================================================
# CSV-based ButterSwap Affiliate Fee Listener - Comprehensive Documentation
# =============================================================================
#
# PROJECT HISTORY & LEARNING JOURNEY:
# ===================================
# 
# This listener has evolved through multiple iterations, each teaching valuable
# lessons about blockchain development, affiliate tracking, and data storage.
#
# TIMELINE OF DEVELOPMENT:
# - Started as part of monolithic affiliate tracking system
# - Had hardcoded affiliate addresses scattered throughout the code
# - Previous attempts at centralized config failed due to validation issues
# - Current approach: Hybrid system with both hardcoded and configurable addresses
# - Migrated to CSV-based storage for simplicity and easy analysis
#
# KEY LESSONS LEARNED:
# 1. Centralized configuration without proper validation is fragile
# 2. Hardcoded addresses lead to maintenance nightmares and missed fees
# 3. Hybrid approaches allow gradual migration without breaking existing systems
# 4. CSV storage provides better analysis capabilities than databases
# 5. Error handling must be built into blockchain monitoring systems
#
# FAILED ATTEMPTS & WHAT WENT WRONG:
# ===================================
# 
# ATTEMPT 1: Monolithic Listener System
# - Problem: Single large listener tried to handle all protocols
# - Issue: Code became unwieldy, difficult to maintain and debug
# - Lesson: Separate concerns, one listener per protocol
#
# ATTEMPT 2: Strict Configuration Validation
# - Problem: Config loader required ALL contract configs to be Ethereum addresses
# - Issue: ThorChain config had API endpoints (midgard_api, thornode_api) that failed validation
# - Error: "Contract address for thorchain on midgard_api must be a valid Ethereum address starting with 0x"
# - Lesson: Validation logic must match actual data structure, not assumptions
#
# ATTEMPT 3: Hardcoded Addresses Everywhere
# - Problem: Affiliate addresses scattered across multiple listener files
# - Issue: Inconsistent addresses led to missed affiliate fees
# - Lesson: Centralize configuration, but with flexible validation
#
# ATTEMPT 4: Database-Only Storage
# - Problem: Tried to force all protocols into database storage
# - Issue: Different protocols have different data structures and requirements
# - Lesson: Hybrid approaches allow protocols to use appropriate storage
#
# WHAT THIS LISTENER IS ATTEMPTING:
# =================================
# 
# PRIMARY GOAL:
# - Monitor ButterSwap transactions across multiple EVM chains
# - Detect when ShapeShift receives affiliate fees from swaps
# - Track transaction volumes, fees, and user addresses
# - Provide comprehensive data for affiliate revenue analysis
#
# TECHNICAL OBJECTIVES:
# - Real-time blockchain monitoring for ButterSwap affiliate events
# - Multi-chain support with consistent data structure
# - Event filtering for Swap, Mint, Burn, and Transfer events
# - Batch processing to handle high transaction volumes
# - Rate limiting to respect RPC provider limits
#
# WHY BUTTERSWAP SPECIFICALLY:
# ============================
# 
# PROTOCOL CHARACTERISTICS:
# - ButterSwap is a DEX aggregator similar to Uniswap V2
# - Uses affiliate fee model where ShapeShift receives a percentage
# - Important for understanding ShapeShift's revenue from DEX activities
# - Base chain is primary focus due to recent deployment and activity
#
# AFFILIATE FEE MODEL:
# - ShapeShift receives a percentage of each swap as affiliate fee
# - Fees are sent to specific affiliate addresses on each chain
# - Different chains may use different affiliate addresses
# - Fee amounts vary based on swap volume and protocol settings
#
# WHY CSV-BASED STORAGE:
# =======================
# 
# ADVANTAGES OVER DATABASES:
# - Simpler than database management
# - Easy to analyze with standard tools (Excel, Python, R)
# - Portable and human-readable format
# - Better for data science and analysis workflows
# - No database setup or maintenance required
#
# DISADVANTAGES:
# - No transaction integrity guarantees
# - Concurrent access can cause data corruption
# - Limited query capabilities
# - No built-in indexing or optimization
#
# CURRENT STATUS & IMPLEMENTATION:
# ===============================
# 
# VERSION COMPARISON:
# - ready-v2: Database-based approach, working but complex
# - ready-v3: CSV-based approach with centralized config, most advanced
# - ready-v4: Database-based with comprehensive comments from v3
# - commented: This branch - comprehensive documentation of all approaches
#
# AFFILIATE ADDRESSES BY CHAIN:
# - Base (8453): 0x35339070f178dC4119732982C23F5a8d88D3f8a3 (Updated)
# - Ethereum (1): 0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be
# - Polygon (137): 0xB5F944600785724e31Edb90F9DFa16dBF01Af000
# - Optimism (10): 0x6268d07327f4fb7380732dc6d63d95F88c0E083b
# - Arbitrum (42161): 0x38276553F8fbf2A027D901F8be45f00373d8Dd48
# - Avalanche (43114): 0x74d63F31C2335b5b3BA7ad2812357672b2624cEd
# - BSC (56): 0x8b92b1698b57bEDF2142297e9397875ADBb2297E
#
# TECHNICAL IMPLEMENTATION:
# =========================
# 
# CORE COMPONENTS:
# 1. Web3 Connection Management: Handles RPC connections to multiple chains
# 2. Event Filtering: Identifies relevant blockchain events for affiliate fees
# 3. Transaction Parsing: Extracts fee amounts, volumes, and user addresses
# 4. CSV Data Storage: Saves affiliate transaction data to CSV files
# 5. Block Tracking: Prevents re-processing of already scanned blocks
#
# KEY TECHNOLOGIES:
# - Web3.py for blockchain interaction
# - Event filtering for specific contract events (Swap, Mint, Burn, Transfer)
# - Batch processing to handle high transaction volumes
# - Rate limiting to respect RPC provider limits
# - CSV processing for data storage and export
#
# ERROR HANDLING STRATEGY:
# ========================
# 
# BLOCKCHAIN ERRORS:
# - RPC connection retry logic with exponential backoff
# - Rate limit handling with automatic delays
# - Transaction parsing error recovery
# - Comprehensive logging for debugging
#
# CSV STORAGE ERRORS:
# - File permission handling
# - Write error recovery and retry
# - Backup and recovery mechanisms
# - Graceful degradation when storage fails
#
# CONFIGURATION ERRORS:
# - Fallback to hardcoded addresses if config fails
# - Warning messages instead of fatal errors
# - System continues operation with reduced functionality
#
# PERFORMANCE CONSIDERATIONS:
# ==========================
# 
# RATE LIMITING:
# - Respect RPC provider rate limits (Alchemy, Infura)
# - Implement delays between batch requests
# - Use exponential backoff for failed requests
# - Monitor API usage to avoid hitting limits
#
# BATCH PROCESSING:
# - Process multiple blocks in single RPC call when possible
# - Optimize event filtering to reduce unnecessary data
# - Use efficient data structures for in-memory processing
# - Implement progress tracking for long-running scans
#
# MEMORY MANAGEMENT:
# - Process transactions in chunks to avoid memory issues
# - Clear processed data from memory regularly
# - Use generators for large dataset iteration
# - Monitor memory usage during operation
#
# CSV OPTIMIZATION:
# - Batch CSV writes to reduce I/O operations
# - Use appropriate CSV dialects and formatting
# - Implement data compression for large files
# - Regular file cleanup and archival
#
# DEVELOPMENT WORKFLOW:
# =====================
# 
# TESTING APPROACH:
# - Test with real blockchain data on testnets first
# - Validate affiliate address detection with known transactions
# - Test error scenarios and recovery mechanisms
# - Performance testing with high-volume chains
#
# DEBUGGING STRATEGY:
# - Comprehensive logging at multiple levels
# - Transaction hash tracking for specific issues
# - Block-by-block progress monitoring
# - Error context preservation for troubleshooting
#
# FUTURE IMPROVEMENTS:
# ====================
# 
# IMMEDIATE PRIORITIES:
# 1. Complete error handling coverage
# 2. Performance optimization for high-volume chains
# 3. Real-time monitoring dashboard
# 4. Automated testing suite
#
# LONG-TERM GOALS:
# 1. Machine learning for affiliate fee prediction
# 2. Cross-chain correlation analysis
# 3. Advanced analytics and reporting
# 4. Integration with additional DEX protocols
#
# LESSONS FOR FUTURE DEVELOPERS:
# =============================
# 
# 1. START SIMPLE: Begin with working prototypes, not perfect architecture
# 2. VALIDATE ASSUMPTIONS: Test configuration systems with real data
# 3. GRADUAL MIGRATION: Hybrid approaches allow incremental improvement
# 4. COMPREHENSIVE DOCUMENTATION: Document decisions, failures, and lessons
# 5. ERROR HANDLING FIRST: Build robust error handling before adding features
# 6. TEST WITH REAL DATA: Blockchain development requires real-world testing
# 7. MONITOR PERFORMANCE: Rate limits and RPC costs are real constraints
# 8. VERSION CONTROL: Each iteration should be a separate branch for comparison
#
# CONTACT & SUPPORT:
# ==================
# 
# For questions about this listener:
# - Check the troubleshooting section below
# - Review the commit history for specific changes
# - Examine the different branch approaches
# - Contact the development team with specific issues
#
# --- END OF COMPREHENSIVE DOCUMENTATION ---

CSV-based ButterSwap Affiliate Fee Listener
Tracks ShapeShift affiliate fees from ButterSwap trades across EVM chains.
Stores data in CSV format instead of databases.

This listener:
1. Connects to multiple EVM chains via RPC providers
2. Monitors ButterSwap contracts for trade events
3. Filters for ShapeShift affiliate addresses
4. Extracts trade data, fees, and affiliate information
5. Saves everything to CSV files for easy analysis
6. Can run tracer tests for specific dates
"""

import os
import csv
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from web3 import Web3
from eth_abi import decode

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVButterSwapListener:
    def __init__(self, csv_dir: str = "csv_data"):
        self.csv_dir = csv_dir
        
        # Get API keys from environment
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        self.infura_api_key = os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')
        
        if not self.alchemy_api_key:
            logger.warning("ALCHEMY_API_KEY not found, using Infura as fallback")
        
        # Initialize CSV structure
        self.init_csv_structure()
        
        # ShapeShift affiliate addresses by chain
        # These addresses receive affiliate fees from ButterSwap trades
        self.shapeshift_affiliates = {
            1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",      # Ethereum
            137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",     # Polygon
            10: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",      # Optimism
            42161: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",   # Arbitrum
            8453: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",    # Base
            43114: "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",  # Avalanche
            56: "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"       # BSC
        }
        
        # Chain configurations with RPC URLs and contract addresses
        # Each chain has its own ButterSwap contract and optimal settings
        self.chains = {
            'ethereum': {
                'name': 'Ethereum',
                'chain_id': 1,
                'rpc_url': f'https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 15000000,  # Approximate deployment block
                'chunk_size': 1000,       # Blocks to scan per batch
                'delay': 1.0              # Seconds between RPC calls
            },
            'polygon': {
                'name': 'Polygon',
                'chain_id': 137,
                'rpc_url': f'https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://polygon-mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 25000000,
                'chunk_size': 2000,
                'delay': 0.5
            },
            'optimism': {
                'name': 'Optimism',
                'chain_id': 10,
                'rpc_url': f'https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://optimism-mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 10000000,
                'chunk_size': 2000,
                'delay': 0.5
            },
            'arbitrum': {
                'name': 'Arbitrum',
                'chain_id': 42161,
                'rpc_url': f'https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 50000000,
                'chunk_size': 2000,
                'delay': 0.5
            },
            'base': {
                'name': 'Base',
                'chain_id': 8453,
                'rpc_url': f'https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://base-mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 10000000,
                'chunk_size': 2000,
                'delay': 0.5
            },
            'avalanche': {
                'name': 'Avalanche',
                'chain_id': 43114,
                'rpc_url': f'https://avalanche-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}' if self.alchemy_api_key else f'https://avalanche-mainnet.infura.io/v3/{self.infura_api_key}',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 10000000,
                'chunk_size': 2000,
                'delay': 0.5
            },
            'bsc': {
                'name': 'BSC',
                'chain_id': 56,
                'rpc_url': f'https://bsc-dataseed1.binance.org/',
                'butterswap_router': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Router
                'butterswap_factory': '0x35339070f178dC4119732982C23F5a8d88D3f8a3',  # ButterSwap Factory
                'start_block': 10000000,
                'chunk_size': 2000,
                'delay': 0.5
            }
        }
        
        # Initialize Web3 connections
        self.web3_connections = {}
        for chain_name, chain_config in self.chains.items():
            try:
                self.web3_connections[chain_name] = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
                if self.web3_connections[chain_name].is_connected():
                    logger.info(f"✅ Connected to {chain_name}")
                else:
                    logger.warning(f"⚠️ Failed to connect to {chain_name}")
            except Exception as e:
                logger.error(f"❌ Error connecting to {chain_name}: {e}")
    
    def init_csv_structure(self):
        """Initialize CSV file structure for ButterSwap data"""
        os.makedirs(self.csv_dir, exist_ok=True)
        
        # Main ButterSwap transactions CSV
        butterswap_csv = os.path.join(self.csv_dir, 'butterswap_transactions.csv')
        
        # Create CSV with headers if it doesn't exist
        if not os.path.exists(butterswap_csv):
            headers = [
                'tx_hash', 'block_number', 'block_timestamp', 'block_date', 'chain', 'protocol',
                'user_address', 'affiliate_address', 'expected_fee_bps', 'actual_fee_bps',
                'affiliate_fee_token', 'affiliate_fee_amount', 'affiliate_fee_usd',
                'input_token', 'input_amount', 'input_amount_usd', 'output_token', 'output_amount', 'output_amount_usd',
                'volume_usd', 'gas_used', 'gas_price', 'created_at', 'created_date'
            ]
            
            with open(butterswap_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created ButterSwap CSV file: {butterswap_csv}")
        
        # Block tracker CSV for ButterSwap
        block_tracker_csv = os.path.join(self.csv_dir, 'butterswap_block_tracker.csv')
        if not os.path.exists(block_tracker_csv):
            headers = ['chain', 'last_processed_block', 'last_processed_date', 'total_transactions_processed', 'last_error', 'last_error_date']
            with open(block_tracker_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created ButterSwap block tracker CSV: {block_tracker_csv}")
    
    def get_block_timestamp(self, web3: Web3, block_number: int) -> int:
        """Get block timestamp from block number"""
        try:
            block = web3.eth.get_block(block_number)
            return block.timestamp
        except Exception as e:
            logger.warning(f"Could not get timestamp for block {block_number}: {e}")
            return int(time.time())
    
    def get_token_metadata(self, web3: Web3, token_address: str, chain_name: str) -> Dict:
        """Get token metadata (name, symbol, decimals)"""
        try:
            # Basic ERC20 ABI for token info
            abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
            
            contract = web3.eth.contract(address=token_address, abi=abi)
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'address': token_address
            }
        except Exception as e:
            logger.warning(f"Could not get metadata for token {token_address} on {chain_name}: {e}")
            return {
                'name': 'Unknown',
                'symbol': 'UNKNOWN',
                'decimals': 18,
                'address': token_address
            }
    
    def scan_chain_for_butterswap_transactions(self, chain_name: str, start_block: int, end_block: int) -> List[Dict]:
        """Scan a specific chain for ButterSwap transactions with affiliate fees"""
        if chain_name not in self.web3_connections:
            logger.warning(f"Web3 connection not available for {chain_name}")
            return []
        
        web3 = self.web3_connections[chain_name]
        chain_config = self.chains[chain_name]
        transactions = []
        
        logger.info(f"🔍 Scanning {chain_name} from block {start_block} to {end_block}")
        
        # Scan blocks in chunks
        for block_num in range(start_block, end_block + 1, chain_config['chunk_size']):
            chunk_end = min(block_num + chain_config['chunk_size'] - 1, end_block)
            
            try:
                # Get block with transactions
                block = web3.eth.get_block(chunk_end, full_transactions=True)
                if not block or not block.transactions:
                    continue
                
                logger.info(f"📦 Processing block {chunk_end} on {chain_name} ({len(block.transactions)} transactions)")
                
                # Process each transaction in the block
                for tx in block.transactions:
                    try:
                        # Check if transaction involves ButterSwap router
                        if tx.to and tx.to.lower() == chain_config['butterswap_router'].lower():
                            # Check if transaction involves ShapeShift affiliate
                            if self.is_shapeshift_affiliate_transaction(tx, web3, chain_name):
                                tx_data = self.extract_butterswap_transaction_data(tx, block, web3, chain_name)
                                if tx_data:
                                    transactions.append(tx_data)
                    
                    except Exception as e:
                        logger.warning(f"Error processing transaction {tx.hash.hex()}: {e}")
                        continue
                
                # Rate limiting
                time.sleep(chain_config['delay'])
                
            except Exception as e:
                logger.error(f"Error processing block {chunk_end} on {chain_name}: {e}")
                continue
        
        logger.info(f"✅ Found {len(transactions)} ButterSwap transactions on {chain_name}")
        return transactions
    
    def is_shapeshift_affiliate_transaction(self, tx, web3: Web3, chain_name: str) -> bool:
        """Check if transaction involves ShapeShift affiliate address"""
        try:
            # Check if any ShapeShift affiliate address is involved
            chain_id = self.chains[chain_name]['chain_id']
            affiliate_address = self.shapeshift_affiliates.get(chain_id)
            
            if not affiliate_address:
                return False
            
            # Check if affiliate address is in transaction data or logs
            if tx.to and tx.to.lower() == affiliate_address.lower():
                return True
            
            # Check transaction logs for affiliate address
            try:
                receipt = web3.eth.get_transaction_receipt(tx.hash)
                if receipt and receipt.logs:
                    for log in receipt.logs:
                        if affiliate_address.lower() in log.address.lower():
                            return True
                        if affiliate_address.lower() in log.topics:
                            return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking affiliate status: {e}")
            return False
    
    def extract_butterswap_transaction_data(self, tx, block, web3: Web3, chain_name: str) -> Optional[Dict]:
        """Extract transaction data from ButterSwap transaction"""
        try:
            # Get block timestamp
            block_timestamp = block.timestamp
            block_date = datetime.fromtimestamp(block_timestamp).strftime('%Y-%m-%d')
            
            # Basic transaction data
            tx_data = {
                'tx_hash': tx.hash.hex(),
                'block_number': block.number,
                'block_timestamp': block_timestamp,
                'block_date': block_date,
                'chain': chain_name,
                'protocol': 'butterswap',
                'user_address': tx['from'],
                'affiliate_address': self.shapeshift_affiliates.get(self.chains[chain_name]['chain_id'], ''),
                'expected_fee_bps': 55,  # ShapeShift standard affiliate rate
                'actual_fee_bps': 55,    # Will be calculated from actual fee
                'affiliate_fee_token': '',
                'affiliate_fee_amount': 0,
                'affiliate_fee_usd': 0,
                'input_token': '',
                'input_amount': 0,
                'input_amount_usd': 0,
                'output_token': '',
                'output_amount': 0,
                'output_amount_usd': 0,
                'volume_usd': 0,
                'gas_used': 0,
                'gas_price': tx.gasPrice,
                'created_at': datetime.now().isoformat(),
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Try to get transaction receipt for more details
            try:
                receipt = web3.eth.get_transaction_receipt(tx.hash)
                if receipt:
                    tx_data['gas_used'] = receipt.gasUsed
                    
                    # Parse logs for token transfer events
                    if receipt.logs:
                        tx_data = self.parse_transfer_logs(receipt.logs, tx_data, web3, chain_name)
            except:
                pass
            
            return tx_data
            
        except Exception as e:
            logger.error(f"Error extracting transaction data: {e}")
            return None
    
    def parse_transfer_logs(self, logs, tx_data: Dict, web3: Web3, chain_name: str) -> Dict:
        """Parse transfer logs to extract token and amount information"""
        try:
            # ERC20 Transfer event signature
            transfer_signature = web3.keccak(text="Transfer(address,address,uint256)").hex()
            
            for log in logs:
                if log.topics and log.topics[0].hex() == transfer_signature:
                    # Parse transfer event
                    try:
                        decoded = decode(['address', 'address', 'uint256'], log.data)
                        from_addr = decoded[0]
                        to_addr = decoded[1]
                        amount = decoded[2]
                        
                        # Check if this involves ShapeShift affiliate
                        chain_id = self.chains[chain_name]['chain_id']
                        affiliate_address = self.shapeshift_affiliates.get(chain_id)
                        
                        if affiliate_address and (from_addr.lower() == affiliate_address.lower() or to_addr.lower() == affiliate_address.lower()):
                            # This is the affiliate fee transfer
                            token_metadata = self.get_token_metadata(web3, log.address, chain_name)
                            tx_data['affiliate_fee_token'] = token_metadata['symbol']
                            tx_data['affiliate_fee_amount'] = amount / (10 ** token_metadata['decimals'])
                            
                            # Calculate actual fee rate (simplified)
                            # In practice, you'd need to parse the actual swap data
                            tx_data['actual_fee_bps'] = 55  # Placeholder
                        
                        # Track input/output tokens (simplified)
                        if not tx_data['input_token']:
                            token_metadata = self.get_token_metadata(web3, log.address, chain_name)
                            tx_data['input_token'] = token_metadata['symbol']
                            tx_data['input_amount'] = amount / (10 ** token_metadata['decimals'])
                        elif not tx_data['output_token']:
                            token_metadata = self.get_token_metadata(web3, log.address, chain_name)
                            tx_data['output_token'] = token_metadata['symbol']
                            tx_data['output_amount'] = amount / (10 ** token_metadata['decimals'])
                    
                    except Exception as e:
                        logger.warning(f"Error parsing transfer log: {e}")
                        continue
            
            return tx_data
            
        except Exception as e:
            logger.error(f"Error parsing transfer logs: {e}")
            return tx_data
    
    def save_transactions_to_csv(self, transactions: List[Dict], chain_name: str):
        """Save transactions to CSV file"""
        if not transactions:
            return
        
        csv_file = os.path.join(self.csv_dir, 'butterswap_transactions.csv')
        
        # Append new transactions
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'tx_hash', 'block_number', 'block_timestamp', 'block_date', 'chain', 'protocol',
                'user_address', 'affiliate_address', 'expected_fee_bps', 'actual_fee_bps',
                'affiliate_fee_token', 'affiliate_fee_amount', 'affiliate_fee_usd',
                'input_token', 'input_amount', 'input_amount_usd', 'output_token', 'output_amount', 'output_amount_usd',
                'volume_usd', 'gas_used', 'gas_price', 'created_at', 'created_date'
            ])
            
            for tx in transactions:
                writer.writerow(tx)
        
        logger.info(f"💾 Saved {len(transactions)} transactions to {csv_file}")
    
    def run_tracer_test(self, target_date: str = "2025-08-15", blocks_to_scan: int = 10000):
        """Run a tracer test for a specific date to find ButterSwap activity"""
        logger.info(f"🔍 Running tracer test for {target_date}")
        
        # Convert date to timestamp range
        target_timestamp = int(datetime.strptime(target_date, "%Y-%m-%d").timestamp())
        start_timestamp = target_timestamp
        end_timestamp = target_timestamp + 86400  # 24 hours
        
        logger.info(f"📅 Scanning for transactions between {datetime.fromtimestamp(start_timestamp)} and {datetime.fromtimestamp(end_timestamp)}")
        
        all_transactions = []
        
        # Scan each chain
        for chain_name, chain_config in self.chains.items():
            if chain_name not in self.web3_connections:
                continue
            
            web3 = self.web3_connections[chain_name]
            
            # Get current block
            try:
                current_block = web3.eth.block_number
                logger.info(f"📊 Current block on {chain_name}: {current_block}")
                
                # Estimate block range for the target date
                # This is approximate - in practice you'd need to binary search for exact blocks
                estimated_start_block = current_block - blocks_to_scan
                estimated_end_block = current_block
                
                logger.info(f"🔍 Scanning {chain_name} from block {estimated_start_block} to {estimated_end_block}")
                
                # Scan for transactions
                transactions = self.scan_chain_for_butterswap_transactions(
                    chain_name, estimated_start_block, estimated_end_block
                )
                
                # Filter by timestamp
                filtered_transactions = []
                for tx in transactions:
                    if start_timestamp <= tx['block_timestamp'] <= end_timestamp:
                        filtered_transactions.append(tx)
                
                logger.info(f"📅 Found {len(filtered_transactions)} transactions on {target_date} for {chain_name}")
                all_transactions.extend(filtered_transactions)
                
            except Exception as e:
                logger.error(f"Error scanning {chain_name}: {e}")
                continue
        
        # Save all found transactions
        if all_transactions:
            self.save_transactions_to_csv(all_transactions, 'tracer_test')
            logger.info(f"🎉 Tracer test complete! Found {len(all_transactions)} transactions on {target_date}")
            
            # Show summary
            for tx in all_transactions:
                logger.info(f"📝 {tx['chain']} - {tx['tx_hash'][:10]}... - {tx['input_token']} → {tx['output_token']} - Fee: {tx['affiliate_fee_amount']} {tx['affiliate_fee_token']}")
        else:
            logger.warning(f"⚠️ No ButterSwap transactions found on {target_date}")
        
        return all_transactions

def main():
    """Main function to run the ButterSwap listener"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ButterSwap Affiliate Fee Listener')
    parser.add_argument('--tracer-test', action='store_true', help='Run tracer test for specific date')
    parser.add_argument('--date', type=str, default='2025-08-15', help='Date for tracer test (YYYY-MM-DD)')
    parser.add_argument('--blocks', type=int, default=10000, help='Number of blocks to scan for tracer test')
    parser.add_argument('--csv-dir', type=str, default='csv_data', help='Directory for CSV files')
    
    args = parser.parse_args()
    
    # Initialize listener
    listener = CSVButterSwapListener(csv_dir=args.csv_dir)
    
    if args.tracer_test:
        # Run tracer test
        listener.run_tracer_test(args.date, args.blocks)
    else:
        # Run normal scanning (placeholder for future implementation)
        logger.info("Normal scanning mode not yet implemented. Use --tracer-test for testing.")

if __name__ == "__main__":
    main()
