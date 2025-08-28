#!/usr/bin/env python3
"""
Search for Portals Transaction Hash
==================================

This script searches for the specific Portals transaction hash to find
what block it's actually in and verify the data.

Author: ShapeShift Affiliate Tracker Team
Date: 2024
"""

import os
import sys
import logging
from web3 import Web3

# Add shared directory to path for centralized config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

# Import centralized configuration
from config_loader import ConfigLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def search_portals_transaction():
    """Search for the specific Portals transaction hash"""

    # Transaction hash from CSV
    target_tx_hash = (
        "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d"
    )

    logger.info(f"🔍 Searching for Portals transaction: {target_tx_hash}")

    try:
        # Load configuration
        config = ConfigLoader()
        alchemy_api_key = config.get_alchemy_api_key()

        if not alchemy_api_key:
            logger.error("❌ ALCHEMY_API_KEY not found in configuration")
            return

        # Initialize Web3 connection to Ethereum
        w3 = Web3(
            Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}")
        )

        if not w3.is_connected():
            logger.error("❌ Failed to connect to Ethereum network")
            return

        logger.info(f"✅ Connected to Ethereum network")
        logger.info(f"📊 Current block: {w3.eth.block_number}")

        # Try to get transaction by hash
        try:
            tx = w3.eth.get_transaction(target_tx_hash)
            logger.info(f"✅ Found transaction!")
            logger.info(f"📊 Block number: {tx['blockNumber']}")
            logger.info(f"📊 From: {tx['from']}")
            logger.info(f"📊 To: {tx['to']}")
            logger.info(f"📊 Data length: {len(tx['data'])} bytes")

            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(target_tx_hash)
            logger.info(f"📊 Gas used: {receipt['gasUsed']}")
            logger.info(f"📊 Logs: {len(receipt['logs'])}")

            # Check if this matches our CSV data
            csv_block = 22774492
            actual_block = tx["blockNumber"]

            if csv_block == actual_block:
                logger.info(f"✅ Block number matches CSV: {csv_block}")
            else:
                logger.warning(f"⚠️  Block number mismatch!")
                logger.warning(f"   CSV shows: {csv_block}")
                logger.warning(f"   Actual: {actual_block}")
                logger.warning(f"   Difference: {actual_block - csv_block} blocks")

            # Check if sender matches ShapeShift treasury
            shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
            if tx["from"].lower() == shapeshift_treasury.lower():
                logger.info(f"✅ Sender matches ShapeShift treasury")
            else:
                logger.warning(f"⚠️  Sender does not match ShapeShift treasury")
                logger.warning(f"   Expected: {shapeshift_treasury}")
                logger.warning(f"   Actual: {tx['from']}")

            return tx["blockNumber"]

        except Exception as e:
            logger.error(f"❌ Transaction not found: {e}")

            # Try searching recent blocks for this transaction
            logger.info(f"🔍 Searching recent blocks for transaction...")

            current_block = w3.eth.block_number
            search_start = max(0, current_block - 10000)  # Search last 10,000 blocks

            logger.info(f"🔍 Searching blocks {search_start} to {current_block}")

            found = False
            for block_num in range(search_start, current_block + 1):
                if block_num % 1000 == 0:
                    logger.info(f"🔍 Searched up to block {block_num}")

                try:
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    for tx in block.transactions:
                        if tx.hash.hex() == target_tx_hash:
                            logger.info(f"🎯 FOUND TRANSACTION in block {block_num}!")
                            logger.info(f"📊 CSV shows block: 22774492")
                            logger.info(f"📊 Actual block: {block_num}")
                            logger.info(f"📊 Difference: {block_num - 22774492} blocks")
                            found = True
                            break
                    if found:
                        break
                except Exception as e:
                    continue

            if not found:
                logger.error(f"❌ Transaction not found in last 10,000 blocks")
                logger.error(f"💡 This suggests the CSV data may be incorrect")

            return None

    except Exception as e:
        logger.error(f"❌ Error during search: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    search_portals_transaction()
