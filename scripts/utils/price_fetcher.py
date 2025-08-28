#!/usr/bin/env python3
"""
Real-time price fetcher using CoinMarketCap API
"""

import requests
import json
from typing import Dict, Optional


class PriceFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": api_key,
        }

    def get_token_prices(self, symbols: list) -> Dict[str, float]:
        """Get current prices for a list of token symbols"""

        symbol_string = ",".join(symbols)

        url = f"{self.base_url}/cryptocurrency/quotes/latest"
        params = {"symbol": symbol_string, "convert": "USD"}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            prices = {}

            if data["status"]["error_code"] == 0:
                for symbol in symbols:
                    if symbol in data["data"]:
                        price = data["data"][symbol]["quote"]["USD"]["price"]
                        prices[symbol] = price
                    else:
                        prices[symbol] = 0

            return prices

        except Exception as e:
            print(f"Error fetching prices: {e}")
            return {}

    def update_arbitrum_token_prices(self) -> Dict[str, Dict]:
        """Update prices for Arbitrum tokens and return updated token dict"""

        print("🔄 Fetching real-time prices from CoinMarketCap...")

        token_symbols = [
            "USDC",
            "ETH",
            "USDT",
            "WBTC",
            "UNI",
            "LINK",
            "ARB",
            "FRAX",
            "DAI",
        ]

        prices = self.get_token_prices(token_symbols)

        updated_tokens = {
            "0xaf88d065e77c8cc2239327c5edb3a432268e5831": {
                "symbol": "USDC",
                "decimals": 6,
                "price": prices.get("USDC", 1.0),
            },
            "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {
                "symbol": "WETH",
                "decimals": 18,
                "price": prices.get("ETH", 3400),
            },
            "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {
                "symbol": "USDT",
                "decimals": 6,
                "price": prices.get("USDT", 1.0),
            },
            "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": {
                "symbol": "USDC.e",
                "decimals": 6,
                "price": prices.get("USDC", 1.0),
            },
            "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": {
                "symbol": "WBTC",
                "decimals": 8,
                "price": prices.get("WBTC", 65000),
            },
            "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0": {
                "symbol": "UNI",
                "decimals": 18,
                "price": prices.get("UNI", 8),
            },
            "0xf97f4df75117a78c1a5a0dbb814af92458539fb4": {
                "symbol": "LINK",
                "decimals": 18,
                "price": prices.get("LINK", 15),
            },
            "0x912ce59144191c1204e64559fe8253a0e49e6548": {
                "symbol": "ARB",
                "decimals": 18,
                "price": prices.get("ARB", 0.8),
            },
            "0x17fc002b466eec40dae837fc4be5c67993ddbd6f": {
                "symbol": "FRAX",
                "decimals": 18,
                "price": prices.get("FRAX", 1.0),
            },
            "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": {
                "symbol": "DAI",
                "decimals": 18,
                "price": prices.get("DAI", 1.0),
            },
        }

        return updated_tokens
