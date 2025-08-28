#!/usr/bin/env python3
"""
Simple Relay Check - Minimal approach to find recent relay transactions
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()


def simple_relay_check():
    """Simple check for recent relay transactions"""

    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    print("🔍 Simple Relay Check - Base Chain")
    print("=" * 50)

    # Focus on Base chain
    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base")
        return

    # Get current block info
    latest_block = w3.eth.block_number
    latest_block_data = w3.eth.get_block(latest_block)
    latest_timestamp = latest_block_data["timestamp"]

    print(f"Latest block: {latest_block}")
    print(f"Latest timestamp: {datetime.fromtimestamp(latest_timestamp)}")

    # Check only the last 100 blocks (much smaller range)
    blocks_to_check = 100
    start_block = latest_block - blocks_to_check

    print(f"Checking last {blocks_to_check} blocks ({start_block} to {latest_block})")

    # Relay router address on Base
    relay_router = "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"

    try:
        # Get logs from last 100 blocks only
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
            "address": relay_router,
        }

        print("Fetching logs from last 100 blocks...")
        logs = w3.eth.get_logs(filter_params)

        if logs:
            print(
                f"✅ Found {len(logs)} Relay router logs in last {blocks_to_check} blocks"
            )

            # Check each transaction for affiliate involvement
            shapeshift_affiliate = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"
            affiliate_transactions = []

            for i, log in enumerate(logs):
                tx_hash = log["transactionHash"].hex()
                block_num = log["blockNumber"]

                print(
                    f"   Checking transaction {i+1}/{len(logs)}: {tx_hash[:10]}... (block {block_num})"
                )

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

                        affiliate_transactions.append(
                            {
                                "tx_hash": tx_hash,
                                "block": block_num,
                                "timestamp": block_data["timestamp"],
                                "time": block_time,
                            }
                        )
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
                print(f"\n🔍 Affiliate Transactions Found:")
                for tx in affiliate_transactions:
                    print(
                        f"   {tx['tx_hash'][:10]}... - Block {tx['block']} - {tx['time']}"
                    )
            else:
                print(
                    f"\n❌ No ShapeShift affiliate transactions found in last {blocks_to_check} blocks"
                )

        else:
            print("❌ No Relay router activity found in last 100 blocks")

    except Exception as e:
        print(f"❌ Error fetching logs: {e}")
        print(f"   This might be due to the block range being too large")
        print(f"   Try reducing the number of blocks to check")


if __name__ == "__main__":
    start_time = time.time()
    simple_relay_check()
    elapsed = time.time() - start_time
    print(f"\n⏱️ Total time: {elapsed:.1f} seconds")
