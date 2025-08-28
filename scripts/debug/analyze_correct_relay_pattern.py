#!/usr/bin/env python3
"""
Analyze Correct Relay Transaction Pattern
Based on user's information about 11 trades today by 6 users for 520,409 total.
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def analyze_relay_pattern():
    """
    Analyze the correct Relay transaction pattern based on user's information.
    """
    print("🔍 Analyzing Correct Relay Transaction Pattern...")
    print("Based on: 11 trades today by 6 users for 520,409 total")

    try:
        # Connect to Base chain
        w3 = Web3(
            Web3.HTTPProvider(
                "https://base-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"
            )
        )
        if not w3.is_connected():
            print("❌ Failed to connect to Base chain")
            return

        print("✅ Connected to Base chain")

        # Get current block and use smaller ranges
        latest_block = w3.eth.block_number
        print(f"📊 Latest block: {latest_block}")

        # Use smaller block ranges to avoid query limits
        block_ranges = [
            (latest_block - 1000, latest_block - 500),
            (latest_block - 500, latest_block - 100),
            (latest_block - 100, latest_block),
        ]

        # Look for Relay router transactions
        router_addresses = [
            "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222",
            "0xeeeeee9eC4769A09a76A83C7bC42b185872860eE",
        ]

        print(f"\n🔍 Looking for Relay transactions in smaller ranges...")

        total_transactions = 0
        user_addresses = set()
        affiliate_transactions = []

        for router_address in router_addresses:
            print(f"   Checking router: {router_address}")

            for start_block, end_block in block_ranges:
                try:
                    print(f"      📊 Scanning blocks {start_block} to {end_block}")

                    # Look for logs from this router
                    filter_params = {
                        "fromBlock": start_block,
                        "toBlock": end_block,
                        "address": router_address,
                    }

                    logs = w3.eth.get_logs(filter_params)
                    print(f"      📊 Found {len(logs)} logs from router")

                    # Analyze each transaction
                    for log in logs:
                        tx_hash = log["transactionHash"].hex()
                        print(f"      🔍 Analyzing transaction: {tx_hash}")

                        # Get transaction receipt
                        receipt = w3.eth.get_transaction_receipt(tx_hash)

                        # Look for ShapeShift affiliate address
                        affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"
                        has_affiliate_fee = False

                        # Look for ERC-20 transfers to identify users and affiliate fees
                        transfers = []
                        for receipt_log in receipt["logs"]:
                            try:
                                if (
                                    receipt_log.get("topics")
                                    and len(receipt_log["topics"]) == 3
                                    and receipt_log["topics"][0].hex()
                                    == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                                ):
                                    # Parse from and to addresses - extract actual addresses from padding
                                    from_addr_raw = receipt_log["topics"][1].hex()
                                    to_addr_raw = receipt_log["topics"][2].hex()

                                    # Remove padding and get actual addresses (take last 40 characters)
                                    from_addr = "0x" + from_addr_raw[-40:]
                                    to_addr = "0x" + to_addr_raw[-40:]

                                    # Check if this is a transfer to ShapeShift affiliate
                                    if to_addr.lower() == affiliate_address.lower():
                                        has_affiliate_fee = True
                                        print(
                                            f"         ✅ Found affiliate fee transfer to {to_addr}"
                                        )

                                    # Decode amount
                                    amount = 0
                                    if len(receipt_log["data"]) >= 32:
                                        try:
                                            amount = int.from_bytes(
                                                receipt_log["data"][:32], "big"
                                            )
                                        except:
                                            pass

                                    transfer = {
                                        "from": from_addr,
                                        "to": to_addr,
                                        "token": receipt_log["address"],
                                        "amount": amount,
                                    }
                                    transfers.append(transfer)

                                    # Track unique users (exclude router addresses and zero address)
                                    # The addresses are padded, so we need to check the actual address part
                                    actual_from_addr = (
                                        from_addr_raw[-40:]
                                        if len(from_addr_raw) >= 40
                                        else from_addr_raw
                                    )
                                    if (
                                        actual_from_addr
                                        != router_address.replace("0x", "")
                                        and actual_from_addr
                                        != "0000000000000000000000000000000000000000"
                                        and not actual_from_addr.startswith(
                                            "000000000000000000000000"
                                        )
                                    ):
                                        user_addresses.add("0x" + actual_from_addr)
                            except Exception as e:
                                print(f"         ❌ Error processing log: {e}")
                                continue

                        print(f"         📊 Found {len(transfers)} transfers")
                        print(f"         👥 Unique users so far: {len(user_addresses)}")

                        if has_affiliate_fee:
                            affiliate_transactions.append(
                                {
                                    "tx_hash": tx_hash,
                                    "transfers": transfers,
                                    "block_number": receipt["blockNumber"],
                                }
                            )
                            print(f"         💰 Found affiliate transaction!")

                        total_transactions += 1

                        # Limit analysis to first 50 transactions for speed
                        if total_transactions >= 50:
                            break

                except Exception as e:
                    print(
                        f"      ❌ Error scanning blocks {start_block}-{end_block}: {e}"
                    )
                    continue

                if total_transactions >= 50:
                    break

            if total_transactions >= 50:
                break

        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   Total transactions analyzed: {total_transactions}")
        print(f"   Unique users: {len(user_addresses)}")
        print(f"   Affiliate transactions found: {len(affiliate_transactions)}")

        # Show affiliate transactions
        if affiliate_transactions:
            print(f"\n💰 AFFILIATE TRANSACTIONS FOUND:")
            for i, tx in enumerate(affiliate_transactions, 1):
                print(f"   {i}. {tx['tx_hash']} (block {tx['block_number']})")
                print(f"      Transfers: {len(tx['transfers'])}")

        # Check if this matches the user's information
        print(f"\n🎯 COMPARISON WITH USER DATA:")
        print(f"   Expected: 11 trades by 6 users for 520,409 total")
        print(
            f"   Found: {len(affiliate_transactions)} affiliate transactions by {len(user_addresses)} users"
        )

        if len(affiliate_transactions) >= 11 and len(user_addresses) >= 6:
            print(f"   ✅ Transaction count and user count match expectations!")
        else:
            print(f"   ⚠️  Numbers don't match - may need to adjust search parameters")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_relay_pattern()
