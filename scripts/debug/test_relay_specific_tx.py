#!/usr/bin/env python3
"""
Test Specific Relay Transaction
Tests the Relay listener with a known transaction hash that should contain affiliate fees.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from listeners.relay_listener_fixed import FixedRelayListener


def test_specific_transaction():
    """
    Test the Relay listener with a specific transaction hash.
    """
    print("🚀 Testing Relay Listener with specific transaction...")

    try:
        # Initialize the listener
        listener = FixedRelayListener()

        # Get chain config
        chain_config = listener._get_chain_config("base")
        if not chain_config:
            print("❌ Base chain config not found")
            return

        w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
        if not w3.is_connected():
            print("❌ Failed to connect to base chain")
            return

        print("✅ Connected to Base chain")

        # Test with a recent transaction hash (you can replace this with a known one)
        # Let's get a recent transaction from the latest block
        latest_block = w3.eth.block_number
        print(f"📊 Latest block: {latest_block}")

        # Get a recent block
        block = w3.eth.get_block(latest_block - 1, full_transactions=True)
        if block["transactions"]:
            test_tx = block["transactions"][0]["hash"].hex()
            print(f"🔍 Testing with recent transaction: {test_tx}")

            # Test transaction processing
            fees = listener._process_transaction(w3, test_tx, "base")
            print(f"💰 Found {len(fees)} fees in recent transaction")

            if fees:
                print("✅ Found affiliate fees!")
                for fee in fees:
                    print(f"   - Amount: {fee[7]}, Token: {fee[9]}")
            else:
                print("⚠️  No affiliate fees found in recent transaction")

        # Let's also try to find any Relay router transactions in recent blocks
        print("\n🔍 Looking for Relay router transactions...")

        for router_address in chain_config["router_addresses"]:
            print(f"   Checking router: {router_address}")

            try:
                # Look for logs from this router in the last 100 blocks
                filter_params = {
                    "fromBlock": latest_block - 100,
                    "toBlock": latest_block,
                    "address": router_address,
                }

                logs = w3.eth.get_logs(filter_params)
                print(f"   📊 Found {len(logs)} logs from router")

                if logs:
                    # Test with the first transaction
                    test_tx = logs[0]["transactionHash"].hex()
                    print(f"   🔍 Testing with router transaction: {test_tx}")

                    fees = listener._process_transaction(w3, test_tx, "base")
                    print(f"   💰 Found {len(fees)} fees in router transaction")

                    if fees:
                        print("   ✅ Found affiliate fees in router transaction!")
                        for fee in fees:
                            print(f"      - Amount: {fee[7]}, Token: {fee[9]}")
                        break

            except Exception as e:
                print(f"   ❌ Error checking router: {e}")
                continue

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_specific_transaction()
