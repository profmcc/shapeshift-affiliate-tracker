#!/usr/bin/env python3
"""
Find AffiliateFee Events - Search specifically for affiliate fee events in Relay
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def find_affiliate_fee_events():
    """Search specifically for AffiliateFee events in Relay transactions"""

    print("🎯 Find AffiliateFee Events - Relay Affiliate Detection")
    print("=" * 60)

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

    # AffiliateFee event signature
    affiliate_fee_topic = (
        "0x4a25d94a55df505cf9da1f1649d0381e2613c3c83c6a0a3df055ae0e82f6e4d7"
    )

    print(f"\n🔍 Searching for AffiliateFee events...")
    print(f"   Event signature: {affiliate_fee_topic}")

    # Search in recent blocks
    latest_block = w3.eth.block_number
    start_block = latest_block - 1000  # Last 1000 blocks

    print(f"\n📊 Search Strategy:")
    print(f"   Latest block: {latest_block}")
    print(f"   Start block: {start_block}")
    print(f"   Blocks to search: 1000")

    try:
        # Search for AffiliateFee events specifically
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
            "topics": [affiliate_fee_topic],  # Look for AffiliateFee events
        }

        print(f"\n🔍 Fetching AffiliateFee events...")
        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(f"✅ Found {len(logs)} AffiliateFee events!")

            # Analyze each AffiliateFee event
            for i, log in enumerate(logs):
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(f"\n💰 AffiliateFee Event {i+1}:")
                print(f"   Transaction: {tx_hash}")
                print(f"   Block: {block_num}")
                print(f"   Address: {log['address']}")

                # Check if this is from Relay router
                if log["address"].lower() == relay_router.lower():
                    print(f"   ✅ From Relay router!")
                else:
                    print(f"   ⚠️ From different contract: {log['address']}")

                # Parse topics
                if len(log["topics"]) > 1:
                    print(f"   Topics:")
                    for j, topic in enumerate(log["topics"]):
                        topic_hex = topic.hex()
                        print(f"      {j}: {topic_hex}")

                        # Check if topic 1 contains affiliate address
                        if j == 1:  # Topic 1 should be the affiliate address
                            if topic_hex == shapeshift_affiliate.lower().replace(
                                "0x", ""
                            ):
                                print(f"         🎯 SHAPESHIFT AFFILIATE FOUND!")
                            else:
                                print(f"         Other affiliate: 0x{topic_hex}")

                # Get block timestamp
                try:
                    block_data = w3.eth.get_block(block_num)
                    block_time = datetime.fromtimestamp(block_data["timestamp"])
                    print(f"   📅 Block time: {block_time}")

                    # Check if within 24 hours
                    hours_24_ago = datetime.now().timestamp() - (24 * 3600)
                    if block_data["timestamp"] >= hours_24_ago:
                        print(f"   🕐 Within last 24 hours!")
                    else:
                        print(f"   ⏰ Outside 24 hour window")

                except Exception as e:
                    print(f"   ⚠️ Error getting block time: {e}")

                # Small delay
                time.sleep(0.1)

            # Summary
            print(f"\n📊 Summary:")
            print(f"   Total AffiliateFee events found: {len(logs)}")

            # Count ShapeShift affiliate events
            shapeshift_events = 0
            recent_events = 0

            for log in logs:
                if len(log["topics"]) > 1:
                    affiliate_topic = log["topics"][1].hex()
                    if affiliate_topic == shapeshift_affiliate.lower().replace(
                        "0x", ""
                    ):
                        shapeshift_events += 1

                        # Check if recent
                        try:
                            block_data = w3.eth.get_block(log["blockNumber"])
                            hours_24_ago = datetime.now().timestamp() - (24 * 3600)
                            if block_data["timestamp"] >= hours_24_ago:
                                recent_events += 1
                        except:
                            pass

            print(f"   ShapeShift affiliate events: {shapeshift_events}")
            print(f"   Recent ShapeShift events (24h): {recent_events}")

            if shapeshift_events > 0:
                print(
                    f"\n✅ SUCCESS: Found {shapeshift_events} ShapeShift affiliate events!"
                )
                if recent_events > 0:
                    print(f"   {recent_events} events in the last 24 hours")
                else:
                    print(f"   All events are older than 24 hours")
            else:
                print(f"\n❌ No ShapeShift affiliate events found")
                print(f"   This suggests:")
                print(f"   1. Wrong affiliate address")
                print(f"   2. No recent ShapeShift affiliate activity")
                print(f"   3. Affiliate events use different signature")

        else:
            print(f"❌ No AffiliateFee events found in last 1000 blocks")
            print(f"   This suggests:")
            print(f"   1. No affiliate activity")
            print(f"   2. Different event signature")
            print(f"   3. Affiliate info stored differently")

            # Try alternative event signatures
            print(f"\n🔍 Trying alternative event signatures...")

            # Common alternative signatures
            alternative_signatures = [
                "0x4a25d94a55df505cf9da1f1649d0381e2613c3c83c6a0a3df055ae0e82f6e4d7",  # AffiliateFee
                "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # Approval
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer
            ]

            for sig in alternative_signatures:
                try:
                    filter_params = {
                        "fromBlock": start_block,
                        "toBlock": latest_block,
                        "topics": [sig],
                    }

                    logs = w3.eth.get_logs(filter_params)
                    if logs:
                        print(f"   Signature {sig}: {len(logs)} events")

                        # Check if any contain ShapeShift affiliate
                        for log in logs[:3]:  # Check first 3
                            if (
                                log["data"]
                                and shapeshift_affiliate.lower().replace("0x", "")
                                in log["data"].hex().lower()
                            ):
                                print(f"      🎯 ShapeShift affiliate found in data!")
                                break

                except Exception as e:
                    print(f"   Signature {sig}: Error - {e}")

                time.sleep(0.1)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    start_time = time.time()
    find_affiliate_fee_events()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
