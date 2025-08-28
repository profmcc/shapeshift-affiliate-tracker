#!/usr/bin/env python3
"""
Debug Script for Portals Listener - Single Transaction Test
Tests the PortalsListener by processing a single, known ShapeShift-affiliated transaction.
"""

import os
import sys
import sqlite3
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from listeners.portals_listener_final import FinalPortalsListener


def test_single_portals_transaction():
    """
    Initializes the FinalPortalsListener, processes a single transaction,
    and verifies that the data is correctly stored in the database.
    """
    print("🚀 Starting Portals single transaction test...")

    # Initialize the listener
    listener = FinalPortalsListener()

    # Configuration for the 'ethereum' chain
    chain_name = "ethereum"
    chain_config = listener.chains[chain_name]

    # Connect to the chain
    w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
    if not w3.is_connected():
        print(f"❌ Failed to connect to {chain_name} RPC.")
        return

    # The transaction to test
    tx_hash = "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d"
    print(f"🔍 Processing transaction: {tx_hash} on {chain_name}")

    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    if not receipt:
        print("❌ Transaction receipt not found.")
        return

    # Check for affiliate involvement
    affiliate_address = listener.shapeshift_affiliates[chain_config["chain_id"]]
    if not listener.check_affiliate_involvement(receipt, affiliate_address):
        print("❌ No affiliate involvement found in the transaction.")
        return

    # Detect tokens
    token_info = listener.detect_portals_tokens(w3, receipt, chain_config)

    print(f"\n🔍 Token detection results:")
    print(f"  Input token: {token_info['input_token']}")
    print(f"  Input amount: {token_info['input_amount']}")
    print(f"  Output token: {token_info['output_token']}")
    print(f"  Output amount: {token_info['output_amount']}")
    print(f"  Affiliate token: {token_info['affiliate_token']}")
    print(f"  Affiliate amount: {token_info['affiliate_amount']}")

    # Prepare event data
    block = w3.eth.get_block(receipt["blockNumber"])
    event_data = {
        "chain": chain_name,
        "tx_hash": tx_hash,
        "block_number": receipt["blockNumber"],
        "block_timestamp": block["timestamp"],
        "input_token": token_info["input_token"],
        "input_amount": token_info["input_amount"],
        "output_token": token_info["output_token"],
        "output_amount": token_info["output_amount"],
        "sender": None,
        "broadcaster": None,
        "recipient": None,
        "partner": affiliate_address,
        "affiliate_token": token_info["affiliate_token"],
        "affiliate_amount": token_info["affiliate_amount"],
        "affiliate_fee_usd": 0.0,
        "volume_usd": 0.0,
    }

    print(f"\n📝 Event data to save:")
    for key, value in event_data.items():
        print(f"  {key}: {value}")

    print(f"\n💾 Database path: {listener.db_path}")

    # Save the event to the database
    listener.save_events_to_db([event_data])

    # Verify the data was saved
    print("\n✅ Verifying data in the database...")
    conn = sqlite3.connect(listener.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM portals_transactions WHERE tx_hash = ?", (tx_hash,))
    rows = cursor.fetchall()

    if not rows:
        print(
            "❌ Verification failed: No data found in the database for this transaction."
        )
    else:
        print(f"✅ Verification successful! Found {len(rows)} entries.")
        for row in rows:
            print(f"   - {row}")

    conn.close()


if __name__ == "__main__":
    test_single_portals_transaction()
