#!/usr/bin/env python3
"""
Test Portals listener on specific block ranges
"""

import os
import sys
from web3 import Web3
from datetime import datetime


def test_portals_specific_blocks():
    """Test Portals listener on specific block ranges where we know transactions exist"""

    # Known transaction details
    known_tx = "f516c60bc7e8e5b10814817d625d967f56e1a18296ad863b287e88253ca86455"
    known_block = 22971641

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

    print(f"🔍 Testing Portals on specific block range:")
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

        # Scan around the known block
        start_block = known_block - 100
        end_block = known_block + 100

        print(f"📊 Scanning blocks {start_block} to {end_block}")

        # Get all logs from Portals router
        filter_params = {
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": portals_router,
        }

        logs = w3.eth.get_logs(filter_params)
        print(f"📋 Found {len(logs)} logs from Portals router")

        if logs:
            print(f"📋 Event signatures found:")
            signatures = set()
            for log in logs:
                if log["topics"]:
                    signatures.add(log["topics"][0].hex())

            for sig in sorted(signatures):
                print(f"   {sig}")

            # Check for affiliate involvement
            affiliate_logs = []
            for log in logs:
                tx_receipt = w3.eth.get_transaction_receipt(log["transactionHash"])

                # Check all logs in the transaction
                for receipt_log in tx_receipt["logs"]:
                    if receipt_log["topics"]:
                        for topic in receipt_log["topics"]:
                            if shapeshift_affiliate.lower() in topic.hex().lower():
                                affiliate_logs.append(log)
                                break
                        else:
                            continue
                        break

            print(
                f"\n📋 Found {len(affiliate_logs)} logs involving ShapeShift affiliate"
            )

            for i, log in enumerate(affiliate_logs):
                print(f"\n   Affiliate Log {i+1}:")
                print(f"     TX: {log['transactionHash'].hex()}")
                print(f"     Block: {log['blockNumber']}")
                print(f"     Topics: {[topic.hex() for topic in log['topics']]}")

                # Check if this is our known transaction
                if log["transactionHash"].hex() == known_tx:
                    print(f"     🎉 This is our known transaction!")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_portals_listener_logic():
    """Test the Portals listener logic on the known transaction"""

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
    known_tx = "f516c60bc7e8e5b10814817d625d967f56e1a18296ad863b287e88253ca86455"

    print(f"\n🔍 Testing Portals listener logic:")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Ethereum")
            return

        # Get the known transaction receipt
        receipt = w3.eth.get_transaction_receipt(known_tx)

        print(f"📋 Transaction Analysis:")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Logs: {len(receipt['logs'])}")

        # Test the affiliate detection logic
        affiliate_involved = False

        for receipt_log in receipt["logs"]:
            if receipt_log["topics"]:
                for topic in receipt_log["topics"]:
                    if shapeshift_affiliate.lower() in topic.hex().lower():
                        affiliate_involved = True
                        print(f"   ✅ Found affiliate address in topic: {topic.hex()}")
                        break
                if affiliate_involved:
                    break

        if not affiliate_involved:
            print(f"   ❌ No affiliate address found")

        # Test if this transaction involves the Portals router
        router_involved = False
        for log in receipt["logs"]:
            if log["address"].lower() == portals_router.lower():
                router_involved = True
                print(f"   ✅ Found Portals router involvement")
                break

        if not router_involved:
            print(f"   ❌ No Portals router involvement")

        if affiliate_involved and router_involved:
            print(f"   🎉 This transaction should be detected by the Portals listener!")
        else:
            print(f"   ❌ This transaction would not be detected")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔧 Test Portals Specific Blocks")
    print("=" * 50)

    test_portals_specific_blocks()
    test_portals_listener_logic()
