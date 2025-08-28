#!/usr/bin/env python3
"""
Debug Specific Relay Transaction

Analyzes a known relay transaction hash to understand transfer parsing issues
"""

import requests
import json
from web3 import Web3
import os

# Configuration
ARBITRUM_RPC = f"https://arbitrum-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')}"
CMC_API_KEY = "64dfaca3-439f-440d-8540-f11e06840ccc"

# Use a specific known transaction hash
KNOWN_TX_HASH = "0xeb4f39a9722e1b2b5b8e2e8e3b1b3b1b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"  # From earlier output


def get_token_prices():
    """Get real-time token prices"""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": "USDC,ETH,USDT,WBTC,UNI,LINK,ARB", "convert": "USD"}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        prices = {}
        if data["status"]["error_code"] == 0:
            for symbol in ["USDC", "ETH", "USDT", "WBTC", "UNI", "LINK", "ARB"]:
                if symbol in data["data"]:
                    prices[symbol] = data["data"][symbol]["quote"]["USD"]["price"]
                    print(f"   {symbol}: ${prices[symbol]:.4f}")
        return prices
    except Exception as e:
        print(f"Price fetch error: {e}")
        return {}


def find_any_recent_relay_transaction():
    """Find ANY recent transaction to the relay contract"""

    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    relay_contract = "0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98"

    print(f"🔍 Searching for ANY transaction to {relay_contract}...")

    try:
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block}")

        # Search more blocks
        for block_num in range(latest_block, latest_block - 1000, -1):
            if block_num % 100 == 0:
                print(f"   Checking block {block_num}...")

            try:
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block["transactions"]:
                    if tx["to"] and tx["to"].lower() == relay_contract.lower():
                        tx_hash = tx["hash"].hex()
                        print(f"\n🎯 Found relay transaction: {tx_hash}")
                        return tx_hash

            except Exception as e:
                continue

        print("❌ No relay transactions found in last 1000 blocks")
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def debug_transaction(tx_hash):
    """Debug a specific transaction"""

    if not tx_hash:
        print("❌ No transaction hash provided")
        return

    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    token_prices = get_token_prices()

    # Expanded token dictionary - add more Arbitrum tokens
    tokens = {
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831": {
            "symbol": "USDC",
            "decimals": 6,
            "price": token_prices.get("USDC", 1.0),
        },
        "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {
            "symbol": "WETH",
            "decimals": 18,
            "price": token_prices.get("ETH", 3400),
        },
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {
            "symbol": "USDT",
            "decimals": 6,
            "price": token_prices.get("USDT", 1.0),
        },
        "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": {
            "symbol": "USDC.e",
            "decimals": 6,
            "price": token_prices.get("USDC", 1.0),
        },
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": {
            "symbol": "WBTC",
            "decimals": 8,
            "price": token_prices.get("WBTC", 65000),
        },
        "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0": {
            "symbol": "UNI",
            "decimals": 18,
            "price": token_prices.get("UNI", 8),
        },
        "0xf97f4df75117a78c1a5a0dbb814af92458539fb4": {
            "symbol": "LINK",
            "decimals": 18,
            "price": token_prices.get("LINK", 15),
        },
        "0x912ce59144191c1204e64559fe8253a0e49e6548": {
            "symbol": "ARB",
            "decimals": 18,
            "price": token_prices.get("ARB", 0.8),
        },
        # Add more potential tokens
        "0x17fc002b466eec40dae837fc4be5c67993ddbd6f": {
            "symbol": "FRAX",
            "decimals": 18,
            "price": 1.0,
        },
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {
            "symbol": "DAI",
            "decimals": 18,
            "price": 1.0,
        },
        "0x539bde0d7dbd336b79148aa742883198bbf60342": {
            "symbol": "MAGIC",
            "decimals": 18,
            "price": 0.5,
        },
        "0x11cdb42b0eb46d95f990bedd4695a6e3fa034978": {
            "symbol": "CRV",
            "decimals": 18,
            "price": 0.3,
        },
    }

    print(f"\n🔍 Analyzing transaction: {tx_hash}")

    try:
        # Get transaction and receipt
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {tx['value']} wei")
        print(f"   Status: {'✅ Success' if receipt['status'] else '❌ Failed'}")
        print(f"   Gas used: {receipt['gasUsed']}")
        print(f"   Total logs: {len(receipt['logs'])}")

        # Analyze all logs to understand what tokens are involved
        transfers = []
        unknown_tokens = set()
        TRANSFER_SIG = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        print(f"\n📊 Log Analysis:")

        for i, log in enumerate(receipt["logs"]):
            print(f"\n   Log {i+1}: {log['address']}")

            if len(log["topics"]) >= 3:
                topic0 = (
                    log["topics"][0].hex()
                    if hasattr(log["topics"][0], "hex")
                    else str(log["topics"][0])
                )

                if topic0 == TRANSFER_SIG:
                    print(f"     ✅ Transfer event found!")

                    # Parse transfer
                    try:
                        from_topic = (
                            log["topics"][1].hex()
                            if hasattr(log["topics"][1], "hex")
                            else str(log["topics"][1])
                        )
                        to_topic = (
                            log["topics"][2].hex()
                            if hasattr(log["topics"][2], "hex")
                            else str(log["topics"][2])
                        )

                        from_addr = "0x" + from_topic[-40:]
                        to_addr = "0x" + to_topic[-40:]

                        data_hex = (
                            log["data"].hex()
                            if hasattr(log["data"], "hex")
                            else str(log["data"])
                        )
                        if data_hex.startswith("0x"):
                            data_hex = data_hex[2:]

                        amount = int(data_hex, 16) if data_hex else 0

                        token_addr = log["address"].lower()
                        token_info = tokens.get(token_addr)

                        print(f"     Token: {log['address']}")
                        print(f"     Amount (raw): {amount}")

                        if token_info:
                            formatted_amount = amount / (10 ** token_info["decimals"])
                            usd_value = formatted_amount * token_info["price"]
                            print(
                                f"     ✅ Known: {formatted_amount:.6f} {token_info['symbol']} = ${usd_value:.2f}"
                            )

                            transfers.append(
                                {
                                    "token": log["address"],
                                    "symbol": token_info["symbol"],
                                    "amount": amount,
                                    "formatted_amount": formatted_amount,
                                    "usd_value": usd_value,
                                }
                            )
                        else:
                            print(f"     ❌ UNKNOWN TOKEN: {token_addr}")
                            unknown_tokens.add(token_addr)

                    except Exception as e:
                        print(f"     ❌ Parse error: {e}")

        print(f"\n💰 Summary:")
        print(f"   Total transfers: {len(transfers)}")
        print(f"   Unknown tokens: {len(unknown_tokens)}")

        if unknown_tokens:
            print(f"\n❌ Unknown tokens found:")
            for token in unknown_tokens:
                print(f"     {token}")
            print(f"\n💡 These tokens need to be added to our dictionary!")

        if transfers:
            print(f"\n✅ Recognized transfers:")
            for i, transfer in enumerate(transfers):
                print(
                    f"     {i+1}. {transfer['formatted_amount']:.6f} {transfer['symbol']} = ${transfer['usd_value']:.2f}"
                )

            # Calculate volume from first transfer
            first_transfer = transfers[0]
            print(f"\n🎯 Volume calculation (first transfer):")
            print(f"     Volume: ${first_transfer['usd_value']:.2f}")
        else:
            print(f"\n❌ No recognized transfers found!")
            print(f"     Either no transfers or all tokens are unknown")

    except Exception as e:
        print(f"Error analyzing transaction: {e}")
        import traceback

        traceback.print_exc()


def main():
    print("🔄 Getting token prices...")

    # First try to find any recent relay transaction
    tx_hash = find_any_recent_relay_transaction()

    if tx_hash:
        debug_transaction(tx_hash)
    else:
        # If no recent transaction found, we need to use a known working one
        print("\n⚠️  No recent relay transactions found.")
        print("This might mean:")
        print("1. ShapeShift isn't using this contract actively")
        print("2. The contract address is wrong")
        print("3. We need to search further back in history")


if __name__ == "__main__":
    main()
