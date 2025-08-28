#!/usr/bin/env python3
"""
Manually add the affiliate transaction we found to the database to verify our detection logic.
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def manual_add_transaction():
    """Manually add the affiliate transaction to the database."""

    # Initialize Web3 connection
    infura_key = os.getenv("INFURA_API_KEY")
    if not infura_key:
        print("❌ INFURA_API_KEY not found in environment variables")
        return

    w3 = Web3(Web3.HTTPProvider(f"https://base-mainnet.infura.io/v3/{infura_key}"))

    if not w3.is_connected():
        print("❌ Failed to connect to Base chain")
        return

    print("✅ Connected to Base chain")

    # The specific transaction we found
    tx_hash = "0x82e227c1a0ad367e05de21fd49bc375a261a7dd6cfd6d7e0196365e70e884bb0"
    affiliate_address = "0x2905d7e4d048d29954f81b02171dd313f457a4a4"

    print(f"\n🔍 Manually adding transaction: {tx_hash}")

    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(
            f"📊 Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}"
        )
        print(f"📊 Block number: {receipt['blockNumber']}")

        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"📊 Transaction to: {tx['to']}")

        # Find the affiliate fee transfer
        affiliate_fee_data = None

        for idx, log in enumerate(receipt["logs"]):
            if (
                log.get("topics")
                and len(log["topics"]) == 3
                and log["topics"][0].hex()
                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):
                to_address = "0x" + log["topics"][2].hex()[-40:]

                if to_address.lower() == affiliate_address.lower():
                    token_address = log["address"]

                    # Parse amount
                    amount = "0"
                    if len(log["data"]) >= 32:
                        try:
                            amount_int = int.from_bytes(log["data"][:32], "big")
                            amount = str(amount_int)
                        except:
                            pass

                    affiliate_fee_data = {
                        "tx_hash": tx_hash,
                        "log_index": idx,
                        "chain": "base",
                        "block_number": receipt["blockNumber"],
                        "timestamp": receipt["blockNumber"],  # Simplified timestamp
                        "event_type": "ERC20AffiliateFee",
                        "affiliate_address": affiliate_address,
                        "amount": amount,
                        "token_address": token_address,
                        "solver_call_data": "",
                        "from_token": "0x0000000000000000000000000000000000000000",  # Placeholder
                        "to_token": "0x0000000000000000000000000000000000000000",  # Placeholder
                        "from_amount": "0",
                        "to_amount": "0",
                    }

                    print(f"✅ Found affiliate fee transfer!")
                    print(f"   Token: {token_address}")
                    print(f"   Amount: {amount}")
                    print(f"   Log Index: {idx}")
                    break

        if not affiliate_fee_data:
            print("❌ No affiliate fee found in transaction")
            return

        # Add to database
        print(f"\n💾 Adding to database...")

        db_path = "databases/affiliate.db"

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relay_affiliate_fees (
                tx_hash TEXT NOT NULL,
                log_index INTEGER NOT NULL,
                chain TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                affiliate_address TEXT NOT NULL,
                amount TEXT NOT NULL,
                token_address TEXT NOT NULL,
                solver_call_data TEXT NOT NULL,
                from_token TEXT NOT NULL,
                to_token TEXT NOT NULL,
                from_amount TEXT NOT NULL,
                to_amount TEXT NOT NULL,
                PRIMARY KEY (tx_hash, log_index)
            )
        """
        )

        # Insert the affiliate fee data
        cursor.execute(
            """
            INSERT OR REPLACE INTO relay_affiliate_fees 
            (tx_hash, log_index, chain, block_number, timestamp, event_type, 
             affiliate_address, amount, token_address, solver_call_data,
             from_token, to_token, from_amount, to_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                affiliate_fee_data["tx_hash"],
                affiliate_fee_data["log_index"],
                affiliate_fee_data["chain"],
                affiliate_fee_data["block_number"],
                affiliate_fee_data["timestamp"],
                affiliate_fee_data["event_type"],
                affiliate_fee_data["affiliate_address"],
                affiliate_fee_data["amount"],
                affiliate_fee_data["token_address"],
                affiliate_fee_data["solver_call_data"],
                affiliate_fee_data["from_token"],
                affiliate_fee_data["to_token"],
                affiliate_fee_data["from_amount"],
                affiliate_fee_data["to_amount"],
            ),
        )

        conn.commit()
        conn.close()

        print(f"✅ Successfully added transaction to database!")

        # Verify it was added
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM relay_affiliate_fees WHERE tx_hash = ?", (tx_hash,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            print(f"✅ Transaction verified in database!")
            print(f"   TX Hash: {result[0]}")
            print(f"   Amount: {result[7]}")
            print(f"   Token: {result[8]}")
        else:
            print(f"❌ Transaction not found in database")

    except Exception as e:
        print(f"❌ Error processing transaction: {e}")


if __name__ == "__main__":
    manual_add_transaction()
