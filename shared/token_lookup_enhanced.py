#!/usr/bin/env python3
"""
Enhanced Token Lookup System
Uses CoinMarketCap API for new tokens, bridge/wrapped tokens, and protocol tokens.
Uses Uniswap for LP tokens.
"""

import os
import requests
import sqlite3
import time
from typing import Dict, List, Optional
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


class EnhancedTokenLookup:
    def __init__(self):
        self.cmc_api_key = os.getenv("COINMARKETCAP_API_KEY")
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.infura_api_key = os.getenv("INFURA_API_KEY")

        # Initialize Web3 for Uniswap queries
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

        # Uniswap V2 Factory address
        self.uniswap_v2_factory = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

        # Uniswap V3 Factory address
        self.uniswap_v3_factory = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

        # Common bridge/wrapped token patterns
        self.bridge_patterns = {
            "wrapped": ["WETH", "WBTC", "WMATIC", "WAVAX", "WBNB"],
            "bridge": ["USDC", "USDT", "DAI", "BUSD"],
            "cross_chain": ["cbBTC", "cbETH", "cbUSDC", "cbUSDT"],
        }

        # Protocol token patterns
        self.protocol_patterns = {
            "defi": ["AAVE", "COMP", "UNI", "SUSHI", "CRV", "BAL", "SNX"],
            "governance": ["UNI", "AAVE", "COMP", "SUSHI", "CRV"],
            "yield": ["yv", "f", "st", "pt", "sd"],
        }

    def get_cmc_token_info(self, address: str) -> Optional[Dict]:
        """Get token info from CoinMarketCap API"""
        if not self.cmc_api_key:
            return None

        try:
            # First try by contract address
            url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
            params = {"address": address, "CMC_PRO_API_KEY": self.cmc_api_key}

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and address.lower() in data["data"]:
                    token_data = data["data"][address.lower()]
                    return {
                        "symbol": token_data["symbol"],
                        "name": token_data["name"],
                        "decimals": 18,  # Most tokens use 18 decimals
                        "price": token_data["quote"]["USD"]["price"]
                        if "quote" in token_data
                        else None,
                        "market_cap": token_data["quote"]["USD"]["market_cap"]
                        if "quote" in token_data
                        else None,
                        "source": "coinmarketcap",
                    }

            # If not found by address, try searching by symbol
            # This is useful for bridge tokens that might have different addresses
            return None

        except Exception as e:
            print(f"Error fetching from CoinMarketCap: {e}")
            return None

    def detect_lp_token(self, address: str) -> Optional[Dict]:
        """Detect if token is an LP token using Uniswap"""
        if not self.w3:
            return None

        try:
            # Check if it's a Uniswap V2 LP token
            v2_lp_info = self._check_uniswap_v2_lp(address)
            if v2_lp_info:
                return v2_lp_info

            # Check if it's a Uniswap V3 LP token
            v3_lp_info = self._check_uniswap_v3_lp(address)
            if v3_lp_info:
                return v3_lp_info

            return None

        except Exception as e:
            print(f"Error detecting LP token: {e}")
            return None

    def _check_uniswap_v2_lp(self, address: str) -> Optional[Dict]:
        """Check if token is a Uniswap V2 LP token"""
        try:
            # Uniswap V2 LP token ABI (minimal)
            lp_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token0",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token1",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "getReserves",
                    "outputs": [
                        {"name": "_reserve0", "type": "uint112"},
                        {"name": "_reserve1", "type": "uint112"},
                        {"name": "_blockTimestampLast", "type": "uint32"},
                    ],
                    "type": "function",
                },
            ]

            contract = self.w3.eth.contract(address=address, abi=lp_abi)

            # Try to call token0() - if it works, this is likely an LP token
            token0 = contract.functions.token0().call()
            token1 = contract.functions.token1().call()

            # Get token symbols
            token0_symbol = self._get_token_symbol(token0)
            token1_symbol = self._get_token_symbol(token1)

            return {
                "symbol": f"UNI-V2 {token0_symbol}-{token1_symbol}",
                "name": f"Uniswap V2 {token0_symbol}-{token1_symbol} LP",
                "decimals": 18,
                "token0": token0,
                "token1": token1,
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "type": "uniswap_v2_lp",
                "source": "uniswap",
            }

        except Exception as e:
            return None

    def _check_uniswap_v3_lp(self, address: str) -> Optional[Dict]:
        """Check if token is a Uniswap V3 LP token"""
        try:
            # Uniswap V3 LP token ABI (minimal)
            lp_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token0",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token1",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "fee",
                    "outputs": [{"name": "", "type": "uint24"}],
                    "type": "function",
                },
            ]

            contract = self.w3.eth.contract(address=address, abi=lp_abi)

            # Try to call token0() - if it works, this is likely an LP token
            token0 = contract.functions.token0().call()
            token1 = contract.functions.token1().call()
            fee = contract.functions.fee().call()

            # Get token symbols
            token0_symbol = self._get_token_symbol(token0)
            token1_symbol = self._get_token_symbol(token1)

            # Convert fee to percentage
            fee_pct = fee / 1000000  # Fee is in basis points

            return {
                "symbol": f"UNI-V3 {token0_symbol}-{token1_symbol}",
                "name": f"Uniswap V3 {token0_symbol}-{token1_symbol} LP ({fee_pct}%)",
                "decimals": 18,
                "token0": token0,
                "token1": token1,
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "fee": fee,
                "type": "uniswap_v3_lp",
                "source": "uniswap",
            }

        except Exception as e:
            return None

    def _get_token_symbol(self, address: str) -> str:
        """Get token symbol from contract"""
        try:
            # Minimal ERC-20 ABI for symbol
            abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function",
                }
            ]
            contract = self.w3.eth.contract(address=address, abi=abi)
            return contract.functions.symbol().call()
        except:
            return "UNKNOWN"

    def detect_bridge_token(
        self, address: str, symbol: str = None, name: str = None
    ) -> Optional[Dict]:
        """Detect if token is a bridge/wrapped token"""
        if not symbol and not name:
            return None

        text_to_check = f"{symbol or ''} {name or ''}".upper()

        # Check for wrapped token patterns
        for pattern in self.bridge_patterns["wrapped"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "wrapped_token",
                    "source": "pattern_match",
                }

        # Check for bridge token patterns
        for pattern in self.bridge_patterns["bridge"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "bridge_token",
                    "source": "pattern_match",
                }

        # Check for cross-chain bridge patterns
        for pattern in self.bridge_patterns["cross_chain"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "cross_chain_bridge",
                    "source": "pattern_match",
                }

        return None

    def detect_protocol_token(
        self, address: str, symbol: str = None, name: str = None
    ) -> Optional[Dict]:
        """Detect if token is a protocol token"""
        if not symbol and not name:
            return None

        text_to_check = f"{symbol or ''} {name or ''}".upper()

        # Check for DeFi protocol tokens
        for pattern in self.protocol_patterns["defi"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "defi_protocol",
                    "source": "pattern_match",
                }

        # Check for governance tokens
        for pattern in self.protocol_patterns["governance"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "governance_token",
                    "source": "pattern_match",
                }

        # Check for yield tokens
        for pattern in self.protocol_patterns["yield"]:
            if pattern in text_to_check:
                return {
                    "symbol": symbol,
                    "name": name,
                    "type": "yield_token",
                    "source": "pattern_match",
                }

        return None

    def identify_token_enhanced(self, address: str) -> Optional[Dict]:
        """Enhanced token identification using multiple sources"""
        print(f"🔍 Enhanced identification for: {address}")

        # 1. Try CoinMarketCap first
        cmc_info = self.get_cmc_token_info(address)
        if cmc_info:
            print(
                f"✅ Found via CoinMarketCap: {cmc_info['symbol']} ({cmc_info['name']})"
            )
            return cmc_info

        # 2. Try Uniswap LP detection
        lp_info = self.detect_lp_token(address)
        if lp_info:
            print(f"✅ Found via Uniswap: {lp_info['symbol']} ({lp_info['name']})")
            return lp_info

        # 3. Try to get basic token info from blockchain
        basic_info = self._get_basic_token_info(address)
        if basic_info:
            # 4. Check if it's a bridge token
            bridge_info = self.detect_bridge_token(
                address, basic_info["symbol"], basic_info["name"]
            )
            if bridge_info:
                print(
                    f"✅ Found bridge token: {bridge_info['symbol']} ({bridge_info['name']})"
                )
                return {**basic_info, **bridge_info}

            # 5. Check if it's a protocol token
            protocol_info = self.detect_protocol_token(
                address, basic_info["symbol"], basic_info["name"]
            )
            if protocol_info:
                print(
                    f"✅ Found protocol token: {protocol_info['symbol']} ({protocol_info['name']})"
                )
                return {**basic_info, **protocol_info}

            print(f"✅ Found basic token: {basic_info['symbol']} ({basic_info['name']})")
            return basic_info

        print(f"❌ Could not identify token: {address}")
        return None

    def _get_basic_token_info(self, address: str) -> Optional[Dict]:
        """Get basic token info from blockchain"""
        if not self.w3:
            return None

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

            return {
                "symbol": symbol,
                "name": name,
                "decimals": decimals,
                "source": "blockchain",
            }

        except Exception as e:
            return None


def main():
    """Test the enhanced token lookup"""
    lookup = EnhancedTokenLookup()

    # Test addresses
    test_addresses = [
        "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",  # Unknown token
        "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",  # Unknown token
        "0x1111111111166b7FE7bd91427724B487980aFc69",  # ZORA
        "0x3b3fB9C57858EF816833dC91565EFcd85D96f634",  # PT-sUSDE-31JUL2025
        "0x419c4dB4B9e25d6Db2AD9691ccb832C8D9fDA05E",  # DRGN
    ]

    print("🚀 Enhanced Token Lookup Test")
    print("=" * 50)

    for address in test_addresses:
        print(f"\n🔍 Testing: {address}")
        result = lookup.identify_token_enhanced(address)
        if result:
            print(f"   Result: {result}")
        else:
            print(f"   ❌ Not found")


if __name__ == "__main__":
    main()
