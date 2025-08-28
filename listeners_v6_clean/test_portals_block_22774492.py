#!/usr/bin/env python3
"""
Test Portals Listener on Specific Block - ShapeShift Transaction
===============================================================

This script tests the Portals listener specifically on block 22,774,492
where we know there's a ShapeShift transaction to debug detection issues.

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
from config_loader import (
    get_config,
    get_shapeshift_address,
    get_contract_address,
    get_chain_config,
    get_storage_path,
    get_listener_config,
    get_event_signature,
    get_threshold,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_portals_block_22774492():
    """Test Portals listener on the specific block with known ShapeShift transaction"""

    # Known transaction details
    target_block = 22774492
    target_tx_hash = (
        "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d"
    )
    shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

    logger.info(f"🎯 Testing Portals listener on block {target_block}")
    logger.info(f"🎯 Target transaction: {target_tx_hash}")
    logger.info(f"🎯 ShapeShift Treasury: {shapeshift_treasury}")

    try:
        # Load configuration
        config = get_config()
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

        # Get the target block
        try:
            block = w3.eth.get_block(target_block, full_transactions=True)
            logger.info(f"✅ Retrieved block {target_block}")
            logger.info(f"📊 Block timestamp: {block.timestamp}")
            logger.info(f"📊 Transactions in block: {len(block.transactions)}")
        except Exception as e:
            logger.error(f"❌ Error retrieving block {target_block}: {e}")
            return

        # Find our target transaction
        target_tx = None
        for tx in block.transactions:
            if tx.hash.hex() == target_tx_hash:
                target_tx = tx
                break

        if not target_tx:
            logger.error(
                f"❌ Target transaction {target_tx_hash} not found in block {target_block}"
            )
            return

        logger.info(f"✅ Found target transaction in block")
        logger.info(f"📊 From: {target_tx['from']}")
        logger.info(f"📊 To: {target_tx['to']}")
        logger.info(f"📊 Data length: {len(target_tx['data'])} bytes")

        # Get transaction receipt
        try:
            receipt = w3.eth.get_transaction_receipt(target_tx_hash)
            logger.info(f"✅ Retrieved transaction receipt")
            logger.info(f"📊 Gas used: {receipt['gasUsed']}")
            logger.info(f"📊 Logs: {len(receipt['logs'])}")
        except Exception as e:
            logger.error(f"❌ Error retrieving transaction receipt: {e}")
            return

        # Analyze logs for ShapeShift involvement
        logger.info(f"\n🔍 Analyzing transaction logs for ShapeShift involvement...")

        shapeshift_found = False

        for i, log in enumerate(receipt["logs"]):
            logger.info(f"\n📋 Log {i}:")
            logger.info(f"   Address: {log['address']}")
            logger.info(f"   Topics: {len(log['topics'])}")

            # Check if ShapeShift treasury address appears
            if log["address"] and log["address"].lower() == shapeshift_treasury.lower():
                logger.info(f"🎯 SHAPESHIFT TREASURY FOUND in log address!")
                shapeshift_found = True

            # Check topics for ShapeShift treasury
            for j, topic in enumerate(log["topics"]):
                topic_hex = topic.hex()
                logger.info(f"   Topic {j}: {topic_hex}")

                if shapeshift_treasury.lower().replace("0x", "") in topic_hex.lower():
                    logger.info(f"🎯 SHAPESHIFT TREASURY FOUND in topic {j}!")
                    shapeshift_found = True

            # Check data for ShapeShift treasury
            if log["data"]:
                data_hex = log["data"].hex()
                logger.info(f"   Data: {data_hex[:64]}...")

                if shapeshift_treasury.lower().replace("0x", "") in data_hex.lower():
                    logger.info(f"🎯 SHAPESHIFT TREASURY FOUND in log data!")
                    shapeshift_found = True

        # Check transaction data
        logger.info(f"\n🔍 Analyzing transaction data...")
        if target_tx["data"]:
            data_hex = target_tx["data"].hex()
            logger.info(f"📊 Transaction data: {data_hex[:64]}...")

            if shapeshift_treasury.lower().replace("0x", "") in data_hex.lower():
                logger.info(f"🎯 SHAPESHIFT TREASURY FOUND in transaction data!")
                shapeshift_found = True

        # Summary
        logger.info(f"\n📊 ANALYSIS SUMMARY:")
        logger.info(f"   Block: {target_block}")
        logger.info(f"   Transaction: {target_tx_hash}")
        logger.info(
            f"   ShapeShift Involvement: {'✅ YES' if shapeshift_found else '❌ NO'}"
        )

        if shapeshift_found:
            logger.info(f"🎯 SUCCESS: ShapeShift involvement detected!")
            logger.info(f"💡 This confirms our detection logic should work")
        else:
            logger.info(f"⚠️  WARNING: No ShapeShift involvement detected in logs")
            logger.info(f"💡 This explains why the listener isn't finding transactions")
            logger.info(
                f"🔍 Need to investigate how Portals actually identifies affiliate transactions"
            )

        # Check for other potential affiliate indicators
        logger.info(f"\n🔍 Looking for other affiliate indicators...")

        # Check for any addresses that might be ShapeShift-related
        all_addresses = set()
        all_addresses.add(target_tx["from"])
        if target_tx["to"]:
            all_addresses.add(target_tx["to"])

        for log in receipt["logs"]:
            all_addresses.add(log["address"])

        logger.info(f"📊 Unique addresses in transaction: {len(all_addresses)}")

        # Look for any addresses that might contain "shapeshift" or similar
        for addr in all_addresses:
            if addr:
                # Check if this address appears in our ShapeShift affiliate list
                config = get_config()
                shapeshift_affiliates = config.get_all_shapeshift_addresses()

                for affiliate in shapeshift_affiliates:
                    if affiliate.lower() == addr.lower():
                        logger.info(f"🎯 SHAPESHIFT AFFILIATE ADDRESS FOUND: {addr}")
                        shapeshift_found = True

        logger.info(f"\n🎯 FINAL RESULT:")
        logger.info(
            f"   ShapeShift Involvement: {'✅ YES' if shapeshift_found else '❌ NO'}"
        )

        if not shapeshift_found:
            logger.info(f"\n💡 RECOMMENDATIONS:")
            logger.info(
                f"   1. Investigate how Portals actually identifies affiliate transactions"
            )
            logger.info(f"   2. Check if affiliate information is stored differently")
            logger.info(f"   3. Look for other event types or data structures")
            logger.info(f"   4. Verify if affiliate detection happens off-chain")

    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_portals_block_22774492()
