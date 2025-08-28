#!/usr/bin/env python3
"""
Efficient Relay Finder - Find recent relay transactions without heavy scanning
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def efficient_relay_finder():
    """Efficiently find recent relay transactions"""

    print("🚀 Efficient Relay Finder - Quick Search")
    print("=" * 60)

    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    # Correct ShapeShift affiliate address for Relay
    shapeshift_affiliate = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
    print(f"✅ Looking for transactions involving: {shapeshift_affiliate}")

    # Focus on Base chain (most active for Relay)
    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base")
        return

    print(f"🔗 Connected to Base chain")

    # Get current block info
    latest_block = w3.eth.block_number
    latest_block_data = w3.eth.get_block(latest_block)
    latest_timestamp = latest_block_data["timestamp"]

    print(f"📊 Latest block: {latest_block}")
    print(f"🕐 Latest timestamp: {datetime.fromtimestamp(latest_timestamp)}")

    # Calculate 24 hours ago
    hours_24_ago = latest_timestamp - (24 * 3600)
    print(f"⏰ 24 hours ago: {datetime.fromtimestamp(hours_24_ago)}")

    # Strategy: Look for recent transactions in smaller chunks
    print(f"\n🔍 Strategy: Check recent blocks in small chunks...")

    # Check last 50 blocks first (very recent)
    blocks_to_check = 50
    start_block = latest_block - blocks_to_check

    print(
        f"   Checking blocks {start_block} to {latest_block} (last {blocks_to_check} blocks)"
    )

    # Relay router address on Base
    relay_router = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    try:
        # Get logs from last 50 blocks
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
            "address": relay_router,
        }

        print("   Fetching logs...")
        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(
                f"   ✅ Found {len(logs)} Relay router logs in last {blocks_to_check} blocks"
            )

            # Check each transaction for affiliate involvement
            affiliate_transactions = []

            for i, log in enumerate(logs):
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(f"   🔍 Checking transaction {i+1}/{len(logs)}: {tx_hash[:10]}...")

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
                        print(f"      🎯 ShapeShift affiliate involved!")

                        # Get block timestamp
                        block_data = w3.eth.get_block(block_num)
                        block_time = datetime.fromtimestamp(block_data["timestamp"])
                        print(f"      📅 Block time: {block_time}")

                        # Check if it's within 24 hours
                        if block_data["timestamp"] >= hours_24_ago:
                            print(f"      🕐 Within last 24 hours!")

                            affiliate_transactions.append(
                                {
                                    "tx_hash": tx_hash,
                                    "block": block_num,
                                    "timestamp": block_data["timestamp"],
                                    "time": block_time,
                                    "within_24h": True,
                                }
                            )
                        else:
                            print(f"      ⏰ Outside 24 hour window")

                    else:
                        print(f"      ❌ No ShapeShift affiliate involvement")

                except Exception as e:
                    print(f"      ⚠️ Error checking transaction: {e}")

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            # Summary
            print(f"\n📊 Summary:")
            print(f"   Total Relay transactions checked: {len(logs)}")
            print(
                f"   ShapeShift affiliate transactions found: {len(affiliate_transactions)}"
            )

            if affiliate_transactions:
                print(f"\n🎯 Affiliate Transactions Found (Last 24 Hours):")
                for tx in affiliate_transactions:
                    print(
                        f"   {tx['tx_hash'][:10]}... - Block {tx['block']} - {tx['time']}"
                    )

                print(
                    f"\n✅ SUCCESS: Found {len(affiliate_transactions)} ShapeShift affiliate transactions!"
                )
                print(f"   These should have $13+ volume equivalent")
            else:
                print(
                    f"\n❌ No ShapeShift affiliate transactions found in last {blocks_to_check} blocks"
                )
                print(f"   This suggests either:")
                print(f"   1. No recent relay activity")
                print(f"   2. No recent ShapeShift affiliate involvement")
                print(f"   3. Need to check more blocks")

        else:
            print(
                f"   ❌ No Relay router activity found in last {blocks_to_check} blocks"
            )

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    start_time = time.time()
    efficient_relay_finder()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
