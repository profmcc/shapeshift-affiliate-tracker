#!/usr/bin/env python3
"""
Enhanced Token Lookup with Webscrape Data
Uses CSV and XLSX data from webscrape folder to improve token identification.
"""

import os
import pandas as pd
import sqlite3
from typing import Dict, List, Optional, Set
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


class TokenLookupWithWebscrape:
    def __init__(self):
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.infura_api_key = os.getenv("INFURA_API_KEY")

        # Initialize Web3 for blockchain lookups
        if self.alchemy_api_key:
            self.w3 = Web3(
                Web3.HTTPProvider(
                    f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
                )
            )
        elif self.infura_api_key:
            self.w3 = Web3(
                Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{self.infura_api_key}")
            )
        else:
            self.w3 = None

        # Load webscrape data
        self.thorchain_tokens = self._load_thorchain_tokens()
        self.cowswap_tokens = self._load_cowswap_tokens()

        # Create token mapping dictionaries
        self.token_symbol_to_address = {}
        self.token_address_to_symbol = {}
        self.cross_chain_tokens = {}
        self._build_token_mappings()

    def _load_thorchain_tokens(self) -> Set[str]:
        """Load unique tokens from THORChain CSV data"""
        try:
            df = pd.read_csv(
                "webscrape/viewblock_thorchain_combined_dedup_2025-07-29.csv"
            )

            # Get unique tokens from both from_asset and to_asset columns
            from_assets = set(df["from_asset"].dropna().unique())
            to_assets = set(df["to_asset"].dropna().unique())

            all_tokens = from_assets.union(to_assets)
            print(f"📊 Loaded {len(all_tokens)} unique tokens from THORChain data")
            print(f"   Sample tokens: {list(all_tokens)[:10]}")

            return all_tokens

        except Exception as e:
            print(f"❌ Error loading THORChain data: {e}")
            return set()

    def _load_cowswap_tokens(self) -> Set[str]:
        """Load unique tokens from CoW Swap XLSX data"""
        try:
            df = pd.read_excel(
                "webscrape/CoW Swap Partner Dashboard Table.xlsx", sheet_name=0
            )

            # Get unique tokens from both Sell Token and Buy Token columns
            sell_tokens = set(df["Sell Token"].dropna().unique())
            buy_tokens = set(df["Buy Token"].dropna().unique())

            all_tokens = sell_tokens.union(buy_tokens)
            print(f"📊 Loaded {len(all_tokens)} unique tokens from CoW Swap data")
            print(f"   Sample tokens: {list(all_tokens)[:10]}")

            return all_tokens

        except Exception as e:
            print(f"❌ Error loading CoW Swap data: {e}")
            return set()

    def _build_token_mappings(self):
        """Build mappings between token symbols and addresses"""
        # Common token mappings
        common_tokens = {
            # Major tokens
            "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            # DeFi tokens
            "BAL": "0xba100000625a3754423978a60c9317c58a424e3D",
            "AURA": "0xC0c293ce456fF0ED870ADd3aFf0D1bBd3Bf3D8a2",
            "LIT": "0xfd0205066521550D7d7AB546DA51B6fD5d7Ee9e0",
            "auraBAL": "0x616e8BfA43F920657B3497DBf40D6b1A02D4608d",
            "swETH": "0xf951E335afb289353dc249e82926178EaC7DEd78",
            "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
            "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
            "MPL": "0x33349B282065b0284d756F0577FB39c158F935e6",
            # THORChain tokens
            "RUNE": "0x3155BA85D5F96b2d030a4966AF206230e46849cb",
            "TCY": "0x0000000000000000000000000000000000000000",  # Unknown
            "DOGE": "0x3832d2F059EaF559e208bDcE1d0C1c8A8C8C8C8C",  # Placeholder
            "LTC": "0x0000000000000000000000000000000000000000",  # Unknown
            "BCH": "0x0000000000000000000000000000000000000000",  # Unknown
            "ATOM": "0x0000000000000000000000000000000000000000",  # Unknown
        }

        # Cross-chain token mappings (tokens that exist on multiple chains)
        self.cross_chain_tokens = {
            "BTC": {
                "ethereum": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                "polygon": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",  # WBTC on Polygon
                "arbitrum": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",  # WBTC on Arbitrum
                "optimism": "0x68f180fcCe6836688e9084f035309E29Bf0A2095",  # WBTC on Optimism
                "base": "0x4200000000000000000000000000000000000006",  # WETH on Base (proxy)
                "description": "Bitcoin (Wrapped BTC)",
            },
            "ETH": {
                "ethereum": "0x0000000000000000000000000000000000000000",  # Native ETH
                "polygon": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # WETH on Polygon
                "arbitrum": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH on Arbitrum
                "optimism": "0x4200000000000000000000000000000000000006",  # WETH on Optimism
                "base": "0x4200000000000000000000000000000000000006",  # WETH on Base
                "description": "Ethereum (Native/Wrapped)",
            },
            "USDC": {
                "ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "arbitrum": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                "optimism": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
                "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "description": "USD Coin",
            },
            "USDT": {
                "ethereum": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "polygon": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "arbitrum": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "optimism": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
                "base": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
                "description": "Tether USD",
            },
            "DAI": {
                "ethereum": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "polygon": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "arbitrum": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "optimism": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "base": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
                "description": "Dai Stablecoin",
            },
        }

        # Build forward mapping (symbol -> address)
        self.token_symbol_to_address = common_tokens.copy()

        # Build reverse mapping (address -> symbol)
        for symbol, address in common_tokens.items():
            self.token_address_to_symbol[address.lower()] = symbol

        # Add cross-chain tokens to mappings
        for symbol, chain_data in self.cross_chain_tokens.items():
            # Use Ethereum address as default
            if "ethereum" in chain_data:
                self.token_symbol_to_address[symbol] = chain_data["ethereum"]
                self.token_address_to_symbol[chain_data["ethereum"].lower()] = symbol

        print(f"📋 Built token mappings: {len(self.token_symbol_to_address)} symbols")
        print(f"🌐 Cross-chain tokens: {len(self.cross_chain_tokens)} tokens")

    def get_cross_chain_token_info(
        self, symbol: str, chain: str = "ethereum"
    ) -> Optional[Dict]:
        """Get cross-chain token information"""
        symbol_upper = symbol.upper()

        if symbol_upper in self.cross_chain_tokens:
            chain_data = self.cross_chain_tokens[symbol_upper]
            if chain.lower() in chain_data:
                return {
                    "symbol": symbol_upper,
                    "name": chain_data["description"],
                    "address": chain_data[chain.lower()],
                    "chain": chain.lower(),
                    "decimals": 18,
                    "source": "cross_chain_mapping",
                    "type": "cross_chain",
                }

        return None

    def get_token_from_webscrape_data(
        self, address: str, chain: str = "ethereum"
    ) -> Optional[Dict]:
        """Try to identify token using webscrape data"""
        address_lower = address.lower()

        # Check if we have a direct address mapping
        if address_lower in self.token_address_to_symbol:
            symbol = self.token_address_to_symbol[address_lower]
            return {
                "symbol": symbol,
                "name": symbol,
                "decimals": 18,
                "source": "webscrape_mapping",
            }

        # Try to get basic token info from blockchain
        if self.w3:
            try:
                # Minimal ERC-20 ABI
                abi = [
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "symbol",
                        "outputs": [{"name": "", "type": "string"}],
                        "type": "function",
                    },
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "name",
                        "outputs": [{"name": "", "type": "string"}],
                        "type": "function",
                    },
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "decimals",
                        "outputs": [{"name": "", "type": "uint8"}],
                        "type": "function",
                    },
                ]

                contract = self.w3.eth.contract(address=address, abi=abi)
                symbol = contract.functions.symbol().call()
                name = contract.functions.name().call()
                decimals = contract.functions.decimals().call()

                # Check if this symbol appears in our webscrape data
                if symbol in self.thorchain_tokens or symbol in self.cowswap_tokens:
                    source = "webscrape_verified"
                else:
                    source = "blockchain"

                return {
                    "symbol": symbol,
                    "name": name,
                    "decimals": decimals,
                    "source": source,
                }

            except Exception as e:
                return None

        return None

    def get_token_by_symbol(
        self, symbol: str, chain: str = "ethereum"
    ) -> Optional[Dict]:
        """Get token info by symbol from webscrape data"""
        symbol_upper = symbol.upper()

        # First check if it's a cross-chain token
        cross_chain_info = self.get_cross_chain_token_info(symbol_upper, chain)
        if cross_chain_info:
            return cross_chain_info

        # Check if symbol exists in our mappings
        if symbol_upper in self.token_symbol_to_address:
            address = self.token_symbol_to_address[symbol_upper]
            return {
                "symbol": symbol_upper,
                "name": symbol_upper,
                "address": address,
                "decimals": 18,
                "source": "webscrape_symbol",
            }

        # Check if symbol appears in webscrape data
        if symbol_upper in self.thorchain_tokens or symbol_upper in self.cowswap_tokens:
            return {
                "symbol": symbol_upper,
                "name": symbol_upper,
                "decimals": 18,
                "source": "webscrape_data",
            }

        return None

    def get_all_webscrape_tokens(self) -> Dict[str, List[str]]:
        """Get all tokens from webscrape data categorized by source"""
        return {
            "thorchain_tokens": list(self.thorchain_tokens),
            "cowswap_tokens": list(self.cowswap_tokens),
            "mapped_tokens": list(self.token_symbol_to_address.keys()),
            "cross_chain_tokens": list(self.cross_chain_tokens.keys()),
        }

    def update_token_cache_with_webscrape_data(self):
        """Update the token cache with webscrape data"""
        print(f"💾 Updating token cache with webscrape data...")

        # Import token cache functions
        import sys

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
        from token_cache import _get_conn

        conn = _get_conn()
        cursor = conn.cursor()

        updated_count = 0

        # Add THORChain tokens
        for symbol in self.thorchain_tokens:
            if symbol in self.token_symbol_to_address:
                address = self.token_symbol_to_address[symbol]
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) 
                        VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
                    """,
                        (address, symbol, symbol, 18, None),
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating cache for {symbol}: {e}")

        # Add CoW Swap tokens
        for symbol in self.cowswap_tokens:
            if symbol in self.token_symbol_to_address:
                address = self.token_symbol_to_address[symbol]
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) 
                        VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
                    """,
                        (address, symbol, symbol, 18, None),
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating cache for {symbol}: {e}")

        # Add cross-chain tokens
        for symbol, chain_data in self.cross_chain_tokens.items():
            if "ethereum" in chain_data:
                address = chain_data["ethereum"]
                name = chain_data["description"]
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) 
                        VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
                    """,
                        (address, symbol, name, 18, None),
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating cache for {symbol}: {e}")

        conn.commit()
        conn.close()
        print(f"✅ Updated token cache with {updated_count} tokens from webscrape data")


def main():
    """Test the webscrape-enhanced token lookup"""
    lookup = TokenLookupWithWebscrape()

    print("🚀 Webscrape-Enhanced Token Lookup Test")
    print("=" * 60)

    # Test cross-chain tokens
    test_cross_chain_tokens = ["BTC", "ETH", "USDC", "USDT", "DAI"]
    print(f"\n🔍 Testing cross-chain token lookups:")
    for token in test_cross_chain_tokens:
        for chain in ["ethereum", "polygon", "arbitrum", "optimism", "base"]:
            result = lookup.get_cross_chain_token_info(token, chain)
            if result:
                print(
                    f"   ✅ {token} on {chain}: {result['address']} ({result['name']})"
                )
            else:
                print(f"   ❌ {token} on {chain}: Not found")

    # Test with some unknown tokens
    test_addresses = [
        "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
        "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
        "0x1111111111166b7FE7bd91427724B487980aFc69",  # ZORA
        "0x419c4dB4B9e25d6Db2AD9691ccb832C8D9fDA05E",  # DRGN
    ]

    for i, address in enumerate(test_addresses, 1):
        print(f"\n🔍 Test {i}: {address}")
        result = lookup.get_token_from_webscrape_data(address)
        if result:
            print(f"   ✅ Found: {result}")
        else:
            print(f"   ❌ Not found")

    # Test symbol lookup
    test_symbols = ["ETH", "USDC", "BAL", "AURA", "RUNE", "BTC"]
    print(f"\n🔍 Testing symbol lookups:")
    for symbol in test_symbols:
        result = lookup.get_token_by_symbol(symbol)
        if result:
            print(f"   ✅ {symbol}: {result}")
        else:
            print(f"   ❌ {symbol}: Not found")

    # Show webscrape data summary
    all_tokens = lookup.get_all_webscrape_tokens()
    print(f"\n📊 Webscrape Data Summary:")
    print(f"   THORChain tokens: {len(all_tokens['thorchain_tokens'])}")
    print(f"   CoW Swap tokens: {len(all_tokens['cowswap_tokens'])}")
    print(f"   Mapped tokens: {len(all_tokens['mapped_tokens'])}")
    print(f"   Cross-chain tokens: {len(all_tokens['cross_chain_tokens'])}")

    # Update token cache
    lookup.update_token_cache_with_webscrape_data()


if __name__ == "__main__":
    main()
