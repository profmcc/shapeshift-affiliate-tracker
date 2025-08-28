#!/usr/bin/env python3
"""
Test Enhanced Token Lookup System
Debug why the enhanced lookup isn't finding unknown tokens.
"""

import sys
import os
from typing import Dict, List, Optional

# Add shared directory to path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
)

from token_lookup_enhanced import EnhancedTokenLookup
from dotenv import load_dotenv

load_dotenv()


def test_enhanced_lookup():
    """Test the enhanced lookup system with unknown tokens"""
    lookup = EnhancedTokenLookup()

    # Test with some of the unknown tokens
    test_addresses = [
        "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
        "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
        "0x120edC8E391ba4c94Cb98bb65d8856Ae6eC1525F",
        "0x2b5050F01d64FBb3e4Ac44dc07f0732BFb5ecadF",
        "0x3D01Fe5A38ddBD307fDd635b4Cb0e29681226D6f",
        "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2",
        "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34",
        "0xF1fC9580784335B2613c1392a530C1aA2A69BA3D",
        "0xb8D98a102b0079B69FFbc760C8d857A31653e56e",
        "0xdB85677bc9bF138687Fa7b7F6c0Ba3Cd19EEcEf5",
        "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
    ]

    print("🚀 Testing Enhanced Token Lookup System")
    print("=" * 60)

    for i, address in enumerate(test_addresses, 1):
        print(f"\n🔍 Test {i}: {address}")

        # Test CoinMarketCap lookup
        print("   Testing CoinMarketCap...")
        cmc_info = lookup.get_cmc_token_info(address)
        if cmc_info:
            print(f"   ✅ CMC Found: {cmc_info['symbol']} ({cmc_info['name']})")
        else:
            print("   ❌ CMC Not found")

        # Test Uniswap LP detection
        print("   Testing Uniswap LP detection...")
        lp_info = lookup.detect_lp_token(address)
        if lp_info:
            print(f"   ✅ Uniswap Found: {lp_info['symbol']} ({lp_info['name']})")
        else:
            print("   ❌ Not a Uniswap LP token")

        # Test basic blockchain lookup
        print("   Testing blockchain lookup...")
        basic_info = lookup._get_basic_token_info(address)
        if basic_info:
            print(
                f"   ✅ Blockchain Found: {basic_info['symbol']} ({basic_info['name']})"
            )

            # Test bridge token detection
            bridge_info = lookup.detect_bridge_token(
                address, basic_info["symbol"], basic_info["name"]
            )
            if bridge_info:
                print(f"   ✅ Bridge Token: {bridge_info['type']}")

            # Test protocol token detection
            protocol_info = lookup.detect_protocol_token(
                address, basic_info["symbol"], basic_info["name"]
            )
            if protocol_info:
                print(f"   ✅ Protocol Token: {protocol_info['type']}")
        else:
            print("   ❌ Blockchain lookup failed")

        print("   " + "-" * 40)


def test_known_tokens():
    """Test with some known tokens to verify the system works"""
    lookup = EnhancedTokenLookup()

    # Test with some known tokens
    known_addresses = [
        "0x1111111111166b7FE7bd91427724B487980aFc69",  # ZORA
        "0x419c4dB4B9e25d6Db2AD9691ccb832C8D9fDA05E",  # DRGN
        "0x3b3fB9C57858EF816833dC91565EFcd85D96f634",  # PT-sUSDE-31JUL2025
    ]

    print("\n🧪 Testing with Known Tokens")
    print("=" * 40)

    for address in known_addresses:
        print(f"\n🔍 Known Token: {address}")
        result = lookup.identify_token_enhanced(address)
        if result:
            print(f"   ✅ Result: {result}")
        else:
            print(f"   ❌ Not found")


if __name__ == "__main__":
    test_enhanced_lookup()
    test_known_tokens()
