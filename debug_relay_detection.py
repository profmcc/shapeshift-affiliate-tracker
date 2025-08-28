#!/usr/bin/env python3
"""
Debug Relay Detection - Examine actual transactions to see why ShapeShift detection fails
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def debug_relay_detection():
    """Debug why ShapeShift affiliate detection is failing"""

    print("🔍 Debug Relay Detection - Why ShapeShift Transactions Not Found")
    print("=" * 70)

    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    # Correct ShapeShift affiliate address for Relay
    shapeshift_affiliate = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
    print(f"✅ Looking for ShapeShift affiliate: {shapeshift_affiliate}")

    # Focus on Base chain
    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base")
        return

    print(f"🔗 Connected to Base chain")

    # Relay router address on Base
    relay_router = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    # Get a small sample of recent Relay transactions
    latest_block = w3.eth.block_number
    start_block = latest_block - 100  # Last 100 blocks

    print(f"\n📊 Sampling Strategy:")
    print(f"   Latest block: {latest_block}")
    print(f"   Start block: {start_block}")
    print(f"   Sample size: 100 blocks")

    try:
        # Get logs from recent blocks
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
            "address": relay_router,
        }

        print(f"\n🔍 Fetching recent Relay router logs...")
        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(f"✅ Found {len(logs)} Relay router logs in last 100 blocks")

            # Sample a few transactions for detailed analysis
            sample_size = min(5, len(logs))
            print(f"\n🔬 Analyzing {sample_size} sample transactions...")

            for i in range(sample_size):
                log = logs[i]
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(f"\n📋 Transaction {i+1}: {tx_hash}")
                print(f"   Block: {block_num}")

                try:
                    # Get full transaction receipt
                    receipt = w3.eth.get_transaction_receipt(tx_hash)

                    # Get transaction details
                    tx = w3.eth.get_transaction(tx_hash)

                    print(f"   From: {tx['from']}")
                    print(f"   To: {tx['to']}")
                    print(f"   Value: {w3.from_wei(tx['value'], 'ether')} ETH")

                    # Check all logs for affiliate information
                    print(f"   📝 Logs found: {len(receipt['logs'])}")

                    affiliate_found = False
                    for j, log_entry in enumerate(receipt["logs"]):
                        print(f"      Log {j+1}:")
                        print(f"         Address: {log_entry['address']}")
                        print(
                            f"         Topics: {[topic.hex() for topic in log_entry['topics']]}"
                        )

                        # Check if ShapeShift affiliate appears anywhere
                        if log_entry["data"]:
                            data_hex = log_entry["data"].hex()
                            if (
                                shapeshift_affiliate.lower().replace("0x", "")
                                in data_hex.lower()
                            ):
                                print(f"         🎯 SHAPESHIFT AFFILIATE FOUND IN DATA!")
                                affiliate_found = True

                        # Check topics for affiliate address
                        for topic in log_entry["topics"]:
                            topic_hex = topic.hex().lower()
                            if (
                                shapeshift_affiliate.lower().replace("0x", "")
                                in topic_hex
                            ):
                                print(
                                    f"         🎯 SHAPESHIFT AFFILIATE FOUND IN TOPIC!"
                                )
                                affiliate_found = True

                    if affiliate_found:
                        print(f"   ✅ ShapeShift affiliate detected!")
                    else:
                        print(f"   ❌ No ShapeShift affiliate detected")

                        # Check if we're looking at the wrong data
                        print(f"   🔍 Checking if affiliate info is elsewhere...")

                        # Look for common affiliate patterns
                        if receipt["logs"]:
                            # Check for AffiliateFee event signature
                            affiliate_fee_topic = "0x4a25d94a55df505cf9da1f1649d0381e2613c3c83c6a0a3df055ae0e82f6e4d7"

                            for log_entry in receipt["logs"]:
                                if (
                                    log_entry["topics"]
                                    and log_entry["topics"][0].hex()
                                    == affiliate_fee_topic
                                ):
                                    print(f"      🎯 Found AffiliateFee event!")
                                    print(
                                        f"         This should contain affiliate information"
                                    )

                                    # Parse affiliate fee event data
                                    if len(log_entry["topics"]) > 1:
                                        print(
                                            f"         Topic 1 (affiliate): {log_entry['topics'][1].hex()}"
                                        )
                                        if log_entry["topics"][
                                            1
                                        ].hex() == shapeshift_affiliate.lower().replace(
                                            "0x", ""
                                        ):
                                            print(
                                                f"         🎯 SHAPESHIFT AFFILIATE FOUND IN AFFILIATEFEE EVENT!"
                                            )
                                        else:
                                            print(
                                                f"         Other affiliate: 0x{log_entry['topics'][1].hex()}"
                                            )

                except Exception as e:
                    print(f"   ⚠️ Error analyzing transaction: {e}")

                # Small delay
                time.sleep(0.2)

            print(f"\n📊 Summary:")
            print(f"   Total logs found: {len(logs)}")
            print(f"   Sample analyzed: {sample_size}")
            print(
                f"   ShapeShift affiliate found: {'Yes' if affiliate_found else 'No'}"
            )

            if not affiliate_found:
                print(f"\n❌ ISSUE IDENTIFIED:")
                print(
                    f"   ShapeShift affiliate address {shapeshift_affiliate} not found in sample"
                )
                print(f"   This suggests:")
                print(f"   1. Wrong affiliate address")
                print(f"   2. Wrong detection method")
                print(f"   3. Affiliate info stored differently")
                print(f"   4. No recent ShapeShift affiliate activity")

        else:
            print(f"❌ No Relay router activity found in last 100 blocks")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    start_time = time.time()
    debug_relay_detection()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
