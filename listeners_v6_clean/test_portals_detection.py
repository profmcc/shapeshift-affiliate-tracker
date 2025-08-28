#!/usr/bin/env python3
"""
Test Portals Detection Logic on Known Transaction
================================================

This script tests the Portals detection logic on the known transaction
where ShapeShift treasury received affiliate fees.

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


def test_portals_detection():
    """Test the Portals detection logic on known transaction"""

    # Known transaction details
    target_tx_hash = (
        "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d"
    )
    shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

    logger.info(f"🎯 Testing Portals detection logic on transaction: {target_tx_hash}")
    logger.info(f"🎯 ShapeShift Treasury: {shapeshift_treasury}")

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

        # Get transaction receipt
        try:
            receipt = w3.eth.get_transaction_receipt(target_tx_hash)
            logger.info(f"✅ Retrieved transaction receipt")
            logger.info(f"📊 Block: {receipt['blockNumber']}")
            logger.info(f"📊 Logs: {len(receipt['logs'])}")
        except Exception as e:
            logger.error(f"❌ Error retrieving transaction receipt: {e}")
            return

        # Test the detection logic
        logger.info(f"\n🔍 Testing ShapeShift Treasury detection logic...")

        # Simulate the detection method from the Portals listener
        treasury_received_funds = False

        # Method 1: Check for ERC-20 transfers TO the ShapeShift DAO Treasury
        transfer_topic = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        for log_entry in receipt["logs"]:
            if (
                log_entry["topics"]
                and len(log_entry["topics"]) >= 3
                and log_entry["topics"][0].hex() == transfer_topic
            ):
                # Check if the recipient (topic[2]) is the ShapeShift DAO Treasury
                if len(log_entry["topics"]) >= 3:
                    recipient = log_entry["topics"][2].hex()
                    if recipient.lower().endswith(
                        shapeshift_treasury.lower().replace("0x", "")
                    ):
                        logger.info(
                            f"🎯 Found ERC-20 transfer TO ShapeShift DAO Treasury!"
                        )
                        logger.info(f"   Transfer recipient: {recipient}")
                        logger.info(f"   Treasury address: {shapeshift_treasury}")
                        treasury_received_funds = True
                        break

        # Method 2: Check for any log where treasury appears as recipient
        if not treasury_received_funds:
            for log_entry in receipt["logs"]:
                if log_entry["topics"]:
                    for topic in log_entry["topics"]:
                        topic_hex = topic.hex().lower()
                        if (
                            shapeshift_treasury.lower().replace("0x", "")
                            in topic_hex.lower()
                        ):
                            logger.info(
                                f"🎯 ShapeShift DAO Treasury found in log topic (likely recipient)!"
                            )
                            logger.info(f"   Topic: {topic_hex}")
                            logger.info(f"   Treasury: {shapeshift_treasury}")
                            treasury_received_funds = True
                            break

                if treasury_received_funds:
                    break

        # Method 3: Check if treasury appears in data
        if not treasury_received_funds:
            for log_entry in receipt["logs"]:
                if log_entry["data"]:
                    data_hex = log_entry["data"].hex().lower()
                    if (
                        shapeshift_treasury.lower().replace("0x", "")
                        in data_hex.lower()
                    ):
                        logger.info(
                            f"🎯 ShapeShift DAO Treasury found in log data (likely recipient)!"
                        )
                        logger.info(f"   Data: {data_hex[:64]}...")
                        logger.info(f"   Treasury: {shapeshift_treasury}")
                        treasury_received_funds = True
                        break

        # Summary
        logger.info(f"\n📊 DETECTION TEST RESULTS:")
        logger.info(f"   Transaction: {target_tx_hash}")
        logger.info(f"   Block: {receipt['blockNumber']}")
        logger.info(
            f"   ShapeShift Treasury Received Funds: {'✅ YES' if treasury_received_funds else '❌ NO'}"
        )

        if treasury_received_funds:
            logger.info(f"🎯 SUCCESS: Detection logic works!")
            logger.info(
                f"💡 The Portals listener should be able to find this transaction"
            )
            logger.info(
                f"🔍 Issue is likely with block scanning range, not detection logic"
            )
        else:
            logger.info(f"⚠️  WARNING: Detection logic failed")
            logger.info(f"💡 Need to investigate why treasury detection isn't working")

        # Show all addresses involved for debugging
        logger.info(f"\n🔍 All addresses involved in transaction:")
        all_addresses = set()
        for log in receipt["logs"]:
            all_addresses.add(log["address"])

        for addr in sorted(all_addresses):
            logger.info(f"   {addr}")

    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_portals_detection()
