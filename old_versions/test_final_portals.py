#!/usr/bin/env python3
"""
Test final Portals listener on specific block range
"""

import os
import sys
from web3 import Web3


def test_final_portals_listener():
    """Test the final Portals listener on specific block range"""

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

    # Known transaction details
    known_tx = "f516c60bc7e8e5b10814817d625d967f56e1a18296ad863b287e88253ca86455"
    known_block = 22971641

    print(f"🔍 Testing Final Portals Listener:")
    print(f"   Known TX: {known_tx}")
    print(f"   Known Block: {known_block}")
    print(f"   Router: {portals_router}")
    print(f"   Affiliate: {shapeshift_affiliate}")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Ethereum")
            return

        print("✅ Connected to Ethereum")

        # Test the affiliate detection logic
        def check_affiliate_involvement(receipt, affiliate_address):
            """Check if a transaction involves the ShapeShift affiliate address"""
            # Remove 0x prefix and convert to lowercase for comparison
            affiliate_clean = affiliate_address.lower().replace("0x", "")

            for log in receipt["logs"]:
                if log["topics"]:
                    for topic in log["topics"]:
                        topic_hex = topic.hex().lower()
                        # Check if the affiliate address (without 0x) is in the topic
                        if affiliate_clean in topic_hex:
                            return True
            return False

        # Get the known transaction receipt
        receipt = w3.eth.get_transaction_receipt(known_tx)

        print(f"\n📋 Testing affiliate detection on known transaction:")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Logs: {len(receipt['logs'])}")

        # Test the affiliate detection
        affiliate_involved = check_affiliate_involvement(receipt, shapeshift_affiliate)

        if affiliate_involved:
            print(f"   ✅ Affiliate detection works!")
        else:
            print(f"   ❌ Affiliate detection failed")

        # Test scanning around the known block
        start_block = known_block - 100
        end_block = known_block + 100

        print(f"\n📊 Scanning blocks {start_block} to {end_block}")

        # Get all logs from Portals router
        filter_params = {
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": portals_router,
        }

        logs = w3.eth.get_logs(filter_params)
        print(f"📋 Found {len(logs)} logs from Portals router")

        # Check for affiliate involvement
        affiliate_logs = []
        for log in logs:
            tx_receipt = w3.eth.get_transaction_receipt(log["transactionHash"])

            # Use the improved affiliate detection
            if check_affiliate_involvement(tx_receipt, shapeshift_affiliate):
                affiliate_logs.append(log)

        print(f"📋 Found {len(affiliate_logs)} logs involving ShapeShift affiliate")

        for i, log in enumerate(affiliate_logs):
            print(f"\n   Affiliate Log {i+1}:")
            print(f"     TX: {log['transactionHash'].hex()}")
            print(f"     Block: {log['blockNumber']}")

            # Check if this is our known transaction
            if log["transactionHash"].hex() == known_tx:
                print(f"     🎉 This is our known transaction!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔧 Test Final Portals Listener")
    print("=" * 50)

    test_final_portals_listener()
