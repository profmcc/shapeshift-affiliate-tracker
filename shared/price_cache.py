#!/usr/bin/env python3
"""
Price Cache with Hourly Updates
Caches token prices from CoinMarketCap and refreshes them at most once per hour.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict

# Add project root to path for module imports
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.utils.price_fetcher import PriceFetcher


class PriceCache:
    def __init__(
        self, api_key: str, cache_file: str = "databases/token_prices_cache.json"
    ):
        self.api_key = api_key
        self.cache_file = cache_file
        self.price_fetcher = PriceFetcher(api_key)
        self._load_cache()

    def _load_cache(self):
        """Load the price cache from a JSON file"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {"timestamp": 0, "prices": {}}

    def _save_cache(self):
        """Save the price cache to a JSON file"""
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=4)

    def get_prices(self) -> Dict[str, float]:
        """Get token prices, fetching from API if cache is stale"""
        current_time = time.time()

        # Check if cache is older than 1 hour (3600 seconds)
        if current_time - self.cache.get("timestamp", 0) > 3600:
            print("🔄 Price cache is stale, fetching new prices...")

            # Fetch prices for a comprehensive list of tokens
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
                "FOX",
                "YFI",
                "AAVE",
                "CRV",
                "SHIB",
            ]

            new_prices = self.price_fetcher.get_token_prices(token_symbols)

            if new_prices:
                self.cache["timestamp"] = current_time
                self.cache["prices"] = new_prices
                self._save_cache()
                print("✅ New prices fetched and cached.")
            else:
                print("⚠️  Failed to fetch new prices, using old cache.")
        else:
            print("✅ Using cached prices.")

        return self.cache.get("prices", {})


def main():
    """Main function for testing the price cache"""
    api_key = os.getenv("COINMARKETCAP_API_KEY")
    if not api_key:
        print("❌ COINMARKETCAP_API_KEY environment variable not set.")
        return

    price_cache = PriceCache(api_key)
    prices = price_cache.get_prices()

    print("\n📊 Current Token Prices:")
    for symbol, price in prices.items():
        print(f"   {symbol}: ${price:,.2f}")


if __name__ == "__main__":
    main()
