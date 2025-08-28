#!/usr/bin/env python3
"""
Search for alternative methods of detecting affiliate transactions.
This includes looking for different addresses, patterns, or transaction types
that might indicate ShapeShift affiliate involvement.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def search_alternative_affiliate_methods():
    """Search for alternative methods of detecting affiliate transactions."""

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

    # Get latest block
    latest_block = w3.eth.block_number
    print(f"📊 Latest block: {latest_block}")

    # Known ShapeShift addresses (including potential alternatives)
    shapeshift_addresses = [
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",  # Current affiliate address
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".lower(),
        "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502".upper(),
        # Add other potential ShapeShift addresses here
    ]

    # Router addresses
    router_addresses = [
        "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
        "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
    ]

    print(f"\n🔍 Searching for alternative affiliate detection methods...")

    # Method 1: Look for transactions that involve both router and any ShapeShift address
    print(f"\n📋 Method 1: Router + ShapeShift address transactions")

    # Scan recent blocks for transactions involving both router and ShapeShift addresses
    start_block = latest_block - 500  # Look at last 500 blocks
    end_block = latest_block

    found_transactions = []

    for block_num in range(start_block, end_block + 1, 10):  # Check every 10th block
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                # Check if this transaction involves a router
                router_involved = False
                for router_addr in router_addresses:
                    if router_addr.lower() in tx["to"].lower() if tx["to"] else False:
                        router_involved = True
                        break

                if router_involved:
                    # Get transaction receipt to check for ShapeShift involvement
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx_hash)

                        # Look for any transfers involving ShapeShift addresses
                        shapeshift_involved = False
                        for log in receipt["logs"]:
                            if (
                                log.get("topics")
                                and len(log["topics"]) == 3
                                and log["topics"][0].hex()
                                == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                            ):
                                from_addr_raw = log["topics"][1].hex()
                                to_addr_raw = log["topics"][2].hex()

                                from_addr = "0x" + from_addr_raw[-40:]
                                to_addr = "0x" + to_addr_raw[-40:]

                                for shapeshift_addr in shapeshift_addresses:
                                    if (
                                        shapeshift_addr.lower() in from_addr.lower()
                                        or shapeshift_addr.lower() in to_addr.lower()
                                    ):
                                        shapeshift_involved = True
                                        found_transactions.append(
                                            {
                                                "tx_hash": tx_hash,
                                                "block": block_num,
                                                "from": from_addr,
                                                "to": to_addr,
                                                "shapeshift_addr": shapeshift_addr,
                                            }
                                        )
                                        break

                                if shapeshift_involved:
                                    break

                        if shapeshift_involved:
                            print(
                                f"   🎯 Found transaction with both router and ShapeShift: {tx_hash}"
                            )
                            print(f"      Block: {block_num}")
                            print(
                                f"      Status: {'Success' if receipt['status'] == 1 else 'Failed'}"
                            )

                    except Exception as e:
                        # Skip failed transactions
                        continue

        except Exception as e:
            print(f"❌ Error processing block {block_num}: {e}")
            continue

    print(
        f"\n📊 Found {len(found_transactions)} transactions with both router and ShapeShift involvement"
    )

    # Method 2: Look for specific transaction patterns that might indicate affiliate fees
    print(f"\n📋 Method 2: Analyzing transaction patterns for affiliate indicators")

    # Look for transactions with specific characteristics that might indicate affiliate involvement
    # This could include:
    # - Transactions with specific input data patterns
    # - Transactions with specific event signatures
    # - Transactions with specific token transfer patterns

    # Method 3: Check if affiliate fees are calculated from transaction differences
    print(f"\n📋 Method 3: Analyzing transaction input/output differences")

    # This would involve:
    # - Comparing input amounts to output amounts
    # - Looking for fee calculations in transaction data
    # - Checking for slippage or fee parameters

    # Method 4: Look for different affiliate addresses
    print(f"\n📋 Method 4: Searching for alternative affiliate addresses")

    # Common patterns for affiliate addresses or fee addresses
    potential_affiliate_patterns = [
        "shapeshift",
        "affiliate",
        "fee",
        "treasury",
        "dao",
        "gov",
    ]

    # Method 5: Check if affiliate information is in transaction input data
    print(f"\n📋 Method 5: Analyzing transaction input data for affiliate parameters")

    # This would involve:
    # - Decoding transaction input data
    # - Looking for affiliate parameters in function calls
    # - Checking for affiliate addresses in transaction parameters

    print(f"\n🔍 Search complete!")
    print(f"📊 Summary:")
    print(
        f"   - Found {len(found_transactions)} transactions with router + ShapeShift involvement"
    )
    print(f"   - Need to investigate alternative detection methods")
    print(f"   - May need to look at transaction input data more carefully")
    print(f"   - May need to check for different affiliate addresses")


if __name__ == "__main__":
    search_alternative_affiliate_methods()
