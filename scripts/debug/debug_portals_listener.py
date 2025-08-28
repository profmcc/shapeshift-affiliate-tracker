#!/usr/bin/env python3
"""
Debug Portals Listener
Tests the Portals listener to identify why affiliate fees are not being detected.
"""

import os
import sys
import time
from web3 import Web3
from datetime import datetime

# Add listeners directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../listeners"))


def test_portals_event_detection():
    """Test Portals event detection on a specific chain"""

    # Use Alchemy API key from environment
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found in environment")
        return

    # Test on Base chain (where we know there are Portals transactions)
    rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    shapeshift_affiliate = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

    print(f"🔍 Testing Portals event detection on Base")
    print(f"   RPC: {rpc_url[:50]}...")
    print(f"   Router: {portals_router}")
    print(f"   Affiliate: {shapeshift_affiliate}")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Base RPC")
            return

        print("✅ Connected to Base RPC")

        # Get current block
        latest_block = w3.eth.block_number
        start_block = latest_block - 1000  # Scan last 1000 blocks

        print(f"📊 Scanning blocks {start_block} to {latest_block}")

        # Test different event signatures
        event_signatures = [
            "0x9f69056fe2b57cf4ad9c5cdfd096e91b7b99ce05e44f6ed446ae6a3d6b5c0a1e",  # Current
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # ERC20 Transfer
            "0x7f4091b46c33e918a0f3aa42307641d17bb670294027a9a8b8c8c79c2c1e6f85",  # Another possible
        ]

        for sig in event_signatures:
            print(f"\n🔍 Testing event signature: {sig}")

            try:
                filter_params = {
                    "fromBlock": start_block,
                    "toBlock": latest_block,
                    "address": portals_router,
                    "topics": [sig],
                }

                logs = w3.eth.get_logs(filter_params)
                print(f"   Found {len(logs)} logs with this signature")

                if logs:
                    print(f"   📋 Sample logs:")
                    for i, log in enumerate(logs[:3]):  # Show first 3 logs
                        print(f"      Log {i+1}:")
                        print(f"        TX: {log['transactionHash'].hex()}")
                        print(f"        Block: {log['blockNumber']}")
                        print(
                            f"        Topics: {[topic.hex() for topic in log['topics']]}"
                        )

                        # Check if this involves ShapeShift affiliate
                        tx_receipt = w3.eth.get_transaction_receipt(
                            log["transactionHash"]
                        )

                        # Look for affiliate address in all logs
                        affiliate_found = False
                        for receipt_log in tx_receipt["logs"]:
                            if receipt_log["topics"]:
                                for topic in receipt_log["topics"]:
                                    if (
                                        shapeshift_affiliate.lower()
                                        in topic.hex().lower()
                                    ):
                                        affiliate_found = True
                                        print(
                                            f"        ✅ Found affiliate address in topic: {topic.hex()}"
                                        )
                                        break

                        if not affiliate_found:
                            print(
                                f"        ❌ No affiliate address found in transaction"
                            )

                        print()

            except Exception as e:
                print(f"   ❌ Error with signature {sig}: {e}")

        # Test without event signature filter
        print(f"\n🔍 Testing without event signature filter:")
        try:
            filter_params = {
                "fromBlock": start_block,
                "toBlock": latest_block,
                "address": portals_router,
            }

            logs = w3.eth.get_logs(filter_params)
            print(f"   Found {len(logs)} total logs from Portals router")

            if logs:
                print(f"   📋 Event signatures found:")
                signatures = set()
                for log in logs:
                    if log["topics"]:
                        signatures.add(log["topics"][0].hex())

                for sig in sorted(signatures):
                    print(f"      {sig}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_known_portals_transaction():
    """Test a known Portals transaction from the comprehensive database"""

    # Get a known Portals transaction from comprehensive database
    import sqlite3

    comp_db = "databases/comprehensive_affiliate.db"
    if not os.path.exists(comp_db):
        print(f"❌ Comprehensive database not found: {comp_db}")
        return

    conn = sqlite3.connect(comp_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT tx_hash, volume_usd, affiliate_fee_usd, timestamp 
        FROM comprehensive_transactions 
        WHERE protocol = 'Portals' AND volume_usd > 0
        LIMIT 1
    """
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        print("❌ No Portals transactions found in comprehensive database")
        return

    tx_hash, volume, fee, timestamp = result
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

    print(f"\n🔍 Testing known Portals transaction:")
    print(f"   TX: {tx_hash}")
    print(f"   Volume: ${volume:,.2f}")
    print(f"   Fee: ${fee:,.2f}")
    print(f"   Date: {date}")

    # Analyze this transaction
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found in environment")
        return

    rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}"

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Base RPC")
            return

        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"\n📋 Transaction Analysis:")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Logs: {len(receipt['logs'])}")

        # Analyze logs
        shapeshift_affiliate = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

        for i, log in enumerate(receipt["logs"]):
            print(f"\n   Log {i+1}:")
            print(f"     Address: {log['address']}")
            print(f"     Topics: {[topic.hex() for topic in log['topics']]}")
            print(f"     Data: {log['data'][:66]}...")

            # Check for affiliate address
            affiliate_found = False
            for topic in log["topics"]:
                if shapeshift_affiliate.lower() in topic.hex().lower():
                    affiliate_found = True
                    print(f"     ✅ Found affiliate address in topic")

            if not affiliate_found and log["data"]:
                # Check data for affiliate address
                if shapeshift_affiliate.lower() in log["data"].hex().lower():
                    print(f"     ✅ Found affiliate address in data")

    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")


if __name__ == "__main__":
    print("🔧 Debug Portals Listener")
    print("=" * 50)

    test_portals_event_detection()
    test_known_portals_transaction()
