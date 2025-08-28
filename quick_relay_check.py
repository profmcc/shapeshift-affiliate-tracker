#!/usr/bin/env python3
"""
Quick Relay Check - Simple script to find recent relay transactions
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def quick_relay_check():
    """Quick check for recent relay transactions"""

    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    # Focus on Base chain (most active for Relay)
    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base")
        return

    print("🔍 Quick Relay Check - Base Chain")
    print("=" * 50)

    # Get current block info
    latest_block = w3.eth.block_number
    latest_block_data = w3.eth.get_block(latest_block)
    latest_timestamp = latest_block_data["timestamp"]

    print(f"Latest block: {latest_block}")
    print(f"Latest timestamp: {datetime.fromtimestamp(latest_timestamp)}")

    # Calculate 24 hours ago
    hours_24_ago = latest_timestamp - (24 * 3600)
    print(f"24 hours ago: {datetime.fromtimestamp(hours_24_ago)}")

    # Estimate blocks for 24 hours (Base: ~2 seconds per block)
    blocks_per_second = 1 / 2
    seconds_diff = latest_timestamp - hours_24_ago
    estimated_blocks = int(seconds_diff * blocks_per_second)

    print(f"Estimated blocks to scan: {estimated_blocks}")

    # Check last 1000 blocks (much smaller range for speed)
    blocks_to_check = min(1000, estimated_blocks)
    start_block = latest_block - blocks_to_check

    print(f"Will check blocks {start_block} to {latest_block}")
    print(f"Checking for Relay router activity...")

    # Relay router address on Base
    relay_router = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    try:
        # Get logs from last 1000 blocks
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
            "address": relay_router,
        }

        print("Fetching logs...")
        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(
                f"✅ Found {len(logs)} Relay router logs in last {blocks_to_check} blocks"
            )

            # Check first few transactions for affiliate involvement
            print(f"\n🔍 Checking first 5 transactions for ShapeShift affiliate...")

            shapeshift_affiliate = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

            for i, log in enumerate(logs[:5]):
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(f"   Transaction {i+1}: {tx_hash[:10]}... (block {block_num})")

                # Quick check for affiliate involvement
                try:
                    receipt = w3.eth.get_transaction_receipt(tx_hash)

                    # Check if affiliate address appears in logs
                    affiliate_found = False
                    for log_entry in receipt["logs"]:
                        if log_entry["topics"]:
                            for topic in log_entry["topics"]:
                                topic_hex = topic.hex().lower()
                                if (
                                    shapeshift_affiliate.lower().replace("0x", "")
                                    in topic_hex
                                ):
                                    affiliate_found = True
                                    break

                        if (
                            log_entry["data"]
                            and shapeshift_affiliate.lower().replace("0x", "")
                            in log_entry["data"].hex().lower()
                        ):
                            affiliate_found = True
                            break

                    if affiliate_found:
                        print(f"      ✅ ShapeShift affiliate involved!")

                        # Get block timestamp
                        block_data = w3.eth.get_block(block_num)
                        block_time = datetime.fromtimestamp(block_data["timestamp"])
                        print(f"      📅 Block time: {block_time}")

                        # Check if it's within 24 hours
                        if block_data["timestamp"] >= hours_24_ago:
                            print(f"      🕐 Within last 24 hours!")
                        else:
                            print(f"      ⏰ Outside 24 hour window")
                    else:
                        print(f"      ❌ No ShapeShift affiliate involvement")

                except Exception as e:
                    print(f"      ⚠️ Error checking transaction: {e}")

                print()

        else:
            print("❌ No Relay router activity found in last 1000 blocks")

    except Exception as e:
        print(f"❌ Error fetching logs: {e}")


if __name__ == "__main__":
    start_time = time.time()
    quick_relay_check()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
