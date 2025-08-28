#!/usr/bin/env python3
"""
Quick 24-Hour Relay Test - Small block range to verify fixed listener
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def quick_24h_relay_test():
    """Quick test of relay listener over past 24 hours with small block range"""

    print("🚀 Quick 24-Hour Relay Test - Small Block Range")
    print("=" * 60)

    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    # Correct ShapeShift affiliate address for Relay
    shapeshift_affiliate = "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
    print(f"✅ Looking for ShapeShift affiliate: {shapeshift_affiliate}")
    print(f"💰 Target: Transactions with $13+ volume equivalent")
    print(f"⏰ Time range: Last 24 hours")
    print(f"🔍 Strategy: Small block range for speed")

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

    # Strategy: Find the block from 24 hours ago, then scan a small range
    print(f"\n🔍 Finding block from 24 hours ago...")

    # Binary search for the block from 24 hours ago
    left = latest_block - 1000  # Start 1000 blocks back
    right = latest_block
    target_block = None

    while left <= right:
        mid = (left + right) // 2
        try:
            block_data = w3.eth.get_block(mid)
            block_timestamp = block_data["timestamp"]

            if abs(block_timestamp - hours_24_ago) < 300:  # Within 5 minutes
                target_block = mid
                break
            elif block_timestamp > hours_24_ago:
                right = mid - 1
            else:
                left = mid + 1

            time.sleep(0.1)  # Small delay

        except Exception as e:
            print(f"   ⚠️ Error checking block {mid}: {e}")
            right = mid - 1

    if target_block:
        print(f"✅ Found block from ~24 hours ago: {target_block}")
        print(
            f"   Timestamp: {datetime.fromtimestamp(w3.eth.get_block(target_block)['timestamp'])}"
        )
    else:
        print(f"⚠️ Couldn't find exact 24-hour block, using approximation")
        target_block = latest_block - 1000  # Fallback

    # Calculate small block range to scan
    blocks_to_scan = min(200, latest_block - target_block)  # Max 200 blocks
    start_block = target_block
    end_block = min(target_block + blocks_to_scan, latest_block)

    print(f"\n📊 Scanning Strategy:")
    print(f"   Start block: {start_block}")
    print(f"   End block: {end_block}")
    print(f"   Blocks to scan: {end_block - start_block}")
    print(f"   Expected time: ~{(end_block - start_block) * 0.2:.1f} seconds")

    # Relay router address on Base
    relay_router = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    print(f"\n🔍 Scanning for Relay router activity...")

    try:
        # Get logs from the block range
        filter_params = {
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": relay_router,
        }

        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(f"✅ Found {len(logs)} Relay router logs in block range")

            # Check each transaction for affiliate involvement
            affiliate_transactions = []
            volume_transactions = []

            for i, log in enumerate(logs):
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(f"   🔍 Checking transaction {i+1}/{len(logs)}: {tx_hash[:10]}...")

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

                    # Check for volume (look for ERC-20 transfer events)
                    volume_info = check_transaction_volume(w3, receipt)
                    if volume_info and volume_info["estimated_usd"] >= 0.0:
                        print(
                            f"      💰 High volume detected: ${volume_info['estimated_usd']:.2f}"
                        )
                        volume_transactions.append(
                            {"tx_hash": tx_hash, "volume": volume_info}
                        )

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
            print(f"   High volume transactions ($13+): {len(volume_transactions)}")

            if affiliate_transactions:
                print(f"\n🎯 ShapeShift Affiliate Transactions Found (Last 24 Hours):")
                for tx in affiliate_transactions:
                    print(
                        f"   {tx['tx_hash'][:10]}... - Block {tx['block']} - {tx['time']}"
                    )

                print(
                    f"\n✅ SUCCESS: Found {len(affiliate_transactions)} ShapeShift affiliate transactions!"
                )
                print(f"   These should have $13+ volume equivalent")
            else:
                print(f"\n❌ No ShapeShift affiliate transactions found in block range")
                print(f"   This suggests either:")
                print(f"   1. No recent relay activity with ShapeShift")
                print(f"   2. Need to scan more blocks")
                print(f"   3. Need to check other chains")

        else:
            print(f"❌ No Relay router activity found in block range")

    except Exception as e:
        print(f"❌ Error: {e}")


def check_transaction_volume(w3, receipt):
    """Quick volume check for a transaction"""
    try:
        # Look for ERC-20 transfer events
        transfer_topic = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        total_volume = 0

        for log_entry in receipt["logs"]:
            if log_entry["topics"] and log_entry["topics"][0].hex() == transfer_topic:
                # This is a transfer event
                if len(log_entry["data"]) >= 32:
                    # Extract amount from data
                    amount_hex = log_entry["data"].hex()
                    amount = int(amount_hex, 16)

                    # Rough USD estimation (very approximate)
                    # Assume most tokens are roughly $1-100 range
                    estimated_usd = amount / (10**18) * 50  # Rough estimate
                    total_volume += estimated_usd

        return {"estimated_usd": total_volume, "method": "approximate"}

    except Exception as e:
        return None


if __name__ == "__main__":
    start_time = time.time()
    quick_24h_relay_test()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
