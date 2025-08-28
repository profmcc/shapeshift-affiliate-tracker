#!/usr/bin/env python3
"""
Debug affiliate detection logic
"""

import os
import sys
from web3 import Web3


def debug_affiliate_detection():
    """Debug the affiliate detection logic"""

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
    known_tx = "f516c60bc7e8e5b10814817d625d967f56e1a18296ad863b287e88253ca86455"

    print(f"🔍 Debugging affiliate detection:")
    print(f"   Affiliate: {shapeshift_affiliate}")
    print(f"   TX: {known_tx}")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Ethereum")
            return

        # Get the transaction receipt
        receipt = w3.eth.get_transaction_receipt(known_tx)

        print(f"\n📋 Transaction Analysis:")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Logs: {len(receipt['logs'])}")

        # Check each log for affiliate address
        for i, log in enumerate(receipt["logs"]):
            print(f"\n   Log {i+1}:")
            print(f"     Address: {log['address']}")
            print(f"     Topics: {[topic.hex() for topic in log['topics']]}")

            # Check each topic for affiliate address
            for j, topic in enumerate(log["topics"]):
                topic_hex = topic.hex()
                print(f"     Topic {j}: {topic_hex}")

                # Check if affiliate address is in this topic
                if shapeshift_affiliate.lower() in topic_hex.lower():
                    print(f"       ✅ Found affiliate address!")
                else:
                    # Check if affiliate address is in the topic (padded)
                    affiliate_padded = (
                        "0x" + "0" * 24 + shapeshift_affiliate[2:].lower()
                    )
                    if affiliate_padded in topic_hex.lower():
                        print(f"       ✅ Found affiliate address (padded)!")
                    else:
                        print(f"       ❌ No affiliate address")

        # Test different affiliate address formats
        print(f"\n🔍 Testing different affiliate address formats:")
        affiliate_variants = [
            shapeshift_affiliate.lower(),
            shapeshift_affiliate.upper(),
            shapeshift_affiliate,
            "0x" + "0" * 24 + shapeshift_affiliate[2:].lower(),
            "0x" + "0" * 24 + shapeshift_affiliate[2:].upper(),
        ]

        for variant in affiliate_variants:
            print(f"   Testing: {variant}")
            found = False
            for log in receipt["logs"]:
                for topic in log["topics"]:
                    if variant in topic.hex().lower():
                        found = True
                        print(f"     ✅ Found in topic: {topic.hex()}")
                        break
                if found:
                    break
            if not found:
                print(f"     ❌ Not found")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔧 Debug Affiliate Detection")
    print("=" * 50)

    debug_affiliate_detection()
