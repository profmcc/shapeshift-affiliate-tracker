#!/usr/bin/env python3
"""
Test specific Portals transaction
"""

import os
import sys
from web3 import Web3
from datetime import datetime


def test_portals_transaction():
    """Test a specific Portals transaction"""

    # Known Portals transaction from comprehensive database
    tx_hash = "f516c60bc7e8e5b10814817d625d967f56e1a18296ad863b287e88253ca86455"

    # Use Alchemy API
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    # Try different chains
    chains = {
        "ethereum": f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
        "base": f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
        "polygon": f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
        "arbitrum": f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
        "optimism": f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
    }

    shapeshift_affiliate = (
        "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"  # Ethereum affiliate
    )

    for chain_name, rpc_url in chains.items():
        print(f"\n🔍 Testing on {chain_name.upper()}:")
        print(f"   RPC: {rpc_url[:50]}...")

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                print(f"   ❌ Failed to connect to {chain_name}")
                continue

            print(f"   ✅ Connected to {chain_name}")

            # Try to get transaction receipt
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                print(f"   ✅ Transaction found on {chain_name}")
                print(f"   📋 Block: {receipt['blockNumber']}")
                print(
                    f"   📋 Status: {'Success' if receipt['status'] == 1 else 'Failed'}"
                )
                print(f"   📋 Logs: {len(receipt['logs'])}")

                # Check if this involves ShapeShift affiliate
                affiliate_found = False
                for i, log in enumerate(receipt["logs"]):
                    print(f"\n   Log {i+1}:")
                    print(f"     Address: {log['address']}")
                    print(f"     Topics: {[topic.hex() for topic in log['topics']]}")
                    print(f"     Data: {log['data'][:66]}...")

                    # Check for affiliate address
                    for topic in log["topics"]:
                        if shapeshift_affiliate.lower() in topic.hex().lower():
                            affiliate_found = True
                            print(f"     ✅ Found affiliate address in topic")

                    if not affiliate_found and log["data"]:
                        if shapeshift_affiliate.lower() in log["data"].hex().lower():
                            affiliate_found = True
                            print(f"     ✅ Found affiliate address in data")

                if affiliate_found:
                    print(
                        f"\n   🎉 This is a ShapeShift affiliate transaction on {chain_name}!"
                    )
                    return chain_name
                else:
                    print(f"\n   ❌ No affiliate address found on {chain_name}")

            except Exception as e:
                print(f"   ❌ Transaction not found on {chain_name}: {e}")

        except Exception as e:
            print(f"   ❌ Error connecting to {chain_name}: {e}")

    print(f"\n❌ Transaction not found on any chain")
    return None


def test_portals_router_events():
    """Test Portals router events on Ethereum"""

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found")
        return

    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    shapeshift_affiliate = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"

    print(f"\n🔍 Testing Portals router events on Ethereum:")
    print(f"   Router: {portals_router}")
    print(f"   Affiliate: {shapeshift_affiliate}")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Ethereum")
            return

        print("✅ Connected to Ethereum")

        # Get current block
        latest_block = w3.eth.block_number
        start_block = latest_block - 1000  # Last 1000 blocks

        print(f"📊 Scanning blocks {start_block} to {latest_block}")

        # Get all logs from Portals router
        filter_params = {
            "fromBlock": start_block,
            "toBlock": latest_block,
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

            for i, log in enumerate(affiliate_logs[:3]):  # Show first 3
                print(f"\n   Affiliate Log {i+1}:")
                print(f"     TX: {log['transactionHash'].hex()}")
                print(f"     Block: {log['blockNumber']}")
                print(f"     Topics: {[topic.hex() for topic in log['topics']]}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔧 Test Portals Transaction")
    print("=" * 50)

    # Test the specific transaction
    chain = test_portals_transaction()

    # Test Portals router events
    test_portals_router_events()
