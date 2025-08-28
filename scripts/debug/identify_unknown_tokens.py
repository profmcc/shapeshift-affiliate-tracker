#!/usr/bin/env python3
"""
Identify Unknown Tokens in Trading Pairs
Uses the existing token cache, enhanced lookup system, and webscrape data to identify unknown token addresses.
"""

import sys
import os
import sqlite3
from typing import Dict, List, Optional

# Add shared directory to path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
)

from token_cache import get_token_info, init_web3
from token_lookup_enhanced import EnhancedTokenLookup
from token_lookup_with_webscrape import TokenLookupWithWebscrape
from dotenv import load_dotenv

load_dotenv()


def get_unknown_tokens_from_db() -> List[str]:
    """Get all unique token addresses from the comprehensive database"""
    conn = sqlite3.connect("databases/comprehensive_affiliate.db")
    cursor = conn.cursor()

    # Get all unique token addresses
    cursor.execute(
        """
        SELECT DISTINCT from_asset FROM comprehensive_transactions 
        WHERE from_asset != '' AND from_asset != '0x0000000000000000000000000000000000000000'
        UNION
        SELECT DISTINCT to_asset FROM comprehensive_transactions 
        WHERE to_asset != '' AND to_asset != '0x0000000000000000000000000000000000000000'
        UNION
        SELECT DISTINCT affiliate_fee_asset FROM comprehensive_transactions 
        WHERE affiliate_fee_asset != '' AND affiliate_fee_asset != '0x0000000000000000000000000000000000000000'
    """
    )

    tokens = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tokens


def identify_tokens_with_webscrape(token_addresses: List[str]) -> Dict[str, Dict]:
    """Identify tokens using enhanced lookup system with webscrape data"""
    # Initialize Web3 for fallback lookups
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    if alchemy_api_key:
        init_web3(f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}")
    else:
        print("⚠️  ALCHEMY_API_KEY not found. Only cached tokens will be identified.")

    # Initialize enhanced lookup
    enhanced_lookup = EnhancedTokenLookup()

    # Initialize webscrape lookup
    webscrape_lookup = TokenLookupWithWebscrape()

    identified_tokens = {}

    print(
        f"🔍 Enhanced identification with webscrape data for {len(token_addresses)} unique tokens..."
    )

    for i, address in enumerate(token_addresses, 1):
        try:
            # First try the original token cache
            token_info = get_token_info(address)
            if token_info:
                identified_tokens[address] = token_info
                print(
                    f"✅ {i}/{len(token_addresses)}: {address} -> {token_info['symbol']} ({token_info['name']}) [CACHE]"
                )
                continue

            # Try webscrape data lookup
            webscrape_info = webscrape_lookup.get_token_from_webscrape_data(address)
            if webscrape_info:
                identified_tokens[address] = webscrape_info
                source = webscrape_info.get("source", "unknown")
                print(
                    f"✅ {i}/{len(token_addresses)}: {address} -> {webscrape_info['symbol']} ({webscrape_info['name']}) [WEBSCRAPE - {source.upper()}]"
                )
                continue

            # If not in cache or webscrape, try enhanced lookup
            enhanced_info = enhanced_lookup.identify_token_enhanced(address)
            if enhanced_info:
                identified_tokens[address] = enhanced_info
                source = enhanced_info.get("source", "unknown")
                token_type = enhanced_info.get("type", "")
                print(
                    f"✅ {i}/{len(token_addresses)}: {address} -> {enhanced_info['symbol']} ({enhanced_info['name']}) [{source.upper()}{' - ' + token_type.upper() if token_type else ''}]"
                )
            else:
                print(f"❌ {i}/{len(token_addresses)}: {address} -> UNKNOWN")

        except Exception as e:
            print(f"⚠️  {i}/{len(token_addresses)}: {address} -> ERROR: {e}")

    return identified_tokens


def get_top_trading_pairs_with_names() -> List[Dict]:
    """Get top trading pairs with token names"""
    conn = sqlite3.connect("databases/comprehensive_affiliate.db")
    cursor = conn.cursor()

    # Get top trading pairs by volume
    cursor.execute(
        """
        SELECT from_asset, to_asset, COUNT(*) as tx_count, SUM(volume_usd) as total_volume 
        FROM comprehensive_transactions 
        WHERE from_asset != '' AND to_asset != '' 
        GROUP BY from_asset, to_asset 
        ORDER BY total_volume DESC 
        LIMIT 15
    """
    )

    pairs = []
    for row in cursor.fetchall():
        from_asset, to_asset, tx_count, total_volume = row
        pairs.append(
            {
                "from_asset": from_asset,
                "to_asset": to_asset,
                "tx_count": tx_count,
                "total_volume": total_volume or 0,
            }
        )

    conn.close()
    return pairs


def update_token_cache_with_all_data(identified_tokens: Dict[str, Dict]):
    """Update the token cache with all identification data"""
    print(f"\n💾 Updating token cache with {len(identified_tokens)} new tokens...")

    # Import token cache functions
    from token_cache import _get_conn

    conn = _get_conn()
    cursor = conn.cursor()

    updated_count = 0
    for address, info in identified_tokens.items():
        try:
            # Insert or update token info
            cursor.execute(
                """
                INSERT OR REPLACE INTO tokens (address, symbol, name, decimals, price, updated_at) 
                VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
            """,
                (
                    address,
                    info.get("symbol", ""),
                    info.get("name", ""),
                    info.get("decimals", 18),
                    info.get("price"),
                ),
            )
            updated_count += 1
        except Exception as e:
            print(f"Error updating cache for {address}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Updated token cache with {updated_count} tokens")


def show_webscrape_data_summary():
    """Show summary of webscrape data"""
    try:
        webscrape_lookup = TokenLookupWithWebscrape()
        all_tokens = webscrape_lookup.get_all_webscrape_tokens()

        print(f"\n📊 Webscrape Data Summary:")
        print(f"   THORChain tokens: {len(all_tokens['thorchain_tokens'])}")
        print(f"   CoW Swap tokens: {len(all_tokens['cowswap_tokens'])}")
        print(f"   Mapped tokens: {len(all_tokens['mapped_tokens'])}")
        print(f"   Cross-chain tokens: {len(all_tokens['cross_chain_tokens'])}")

        # Show some sample tokens
        print(f"\n   Sample THORChain tokens: {all_tokens['thorchain_tokens'][:10]}")
        print(f"   Sample CoW Swap tokens: {all_tokens['cowswap_tokens'][:10]}")
        print(f"   Cross-chain tokens: {all_tokens['cross_chain_tokens']}")

    except Exception as e:
        print(f"❌ Error loading webscrape data: {e}")


def test_cross_chain_tokens():
    """Test cross-chain token identification"""
    print(f"\n🌐 Testing Cross-Chain Token Identification:")

    try:
        webscrape_lookup = TokenLookupWithWebscrape()

        # Test BTC on different chains
        test_chains = ["ethereum", "polygon", "arbitrum", "optimism", "base"]
        for chain in test_chains:
            btc_info = webscrape_lookup.get_cross_chain_token_info("BTC", chain)
            if btc_info:
                print(
                    f"   ✅ BTC on {chain}: {btc_info['address']} ({btc_info['name']})"
                )
            else:
                print(f"   ❌ BTC on {chain}: Not found")

        # Test other cross-chain tokens
        test_tokens = ["ETH", "USDC", "USDT", "DAI"]
        for token in test_tokens:
            eth_info = webscrape_lookup.get_cross_chain_token_info(token, "ethereum")
            if eth_info:
                print(
                    f"   ✅ {token} on Ethereum: {eth_info['address']} ({eth_info['name']})"
                )
            else:
                print(f"   ❌ {token} on Ethereum: Not found")

    except Exception as e:
        print(f"❌ Error testing cross-chain tokens: {e}")


def main():
    """Main function"""
    print("🚀 Enhanced Token Identification with Webscrape Data & Cross-Chain Support")
    print("=" * 80)

    # Show webscrape data summary
    show_webscrape_data_summary()

    # Test cross-chain tokens
    test_cross_chain_tokens()

    # Get all unknown tokens
    token_addresses = get_unknown_tokens_from_db()
    print(f"\nFound {len(token_addresses)} unique token addresses to identify")

    # Identify tokens with enhanced system including webscrape data
    identified_tokens = identify_tokens_with_webscrape(token_addresses)

    print(f"\n📊 Enhanced Identification Results:")
    print(f"   Total tokens: {len(token_addresses)}")
    print(f"   Identified: {len(identified_tokens)}")
    print(f"   Unknown: {len(token_addresses) - len(identified_tokens)}")

    # Update token cache with new data
    if identified_tokens:
        update_token_cache_with_all_data(identified_tokens)

    # Show top trading pairs with token names
    print(f"\n🏆 Top Trading Pairs (with enhanced token names):")
    pairs = get_top_trading_pairs_with_names()

    for i, pair in enumerate(pairs, 1):
        from_token = identified_tokens.get(pair["from_asset"], {"symbol": "UNKNOWN"})
        to_token = identified_tokens.get(pair["to_asset"], {"symbol": "UNKNOWN"})

        from_symbol = from_token["symbol"] if from_token else "UNKNOWN"
        to_symbol = to_token["symbol"] if to_token else "UNKNOWN"

        # Add token type info if available
        from_type = from_token.get("type", "")
        to_type = to_token.get("type", "")

        from_display = (
            f"{from_symbol}{' (' + from_type.upper() + ')' if from_type else ''}"
        )
        to_display = f"{to_symbol}{' (' + to_type.upper() + ')' if to_type else ''}"

        print(f"{i:2d}. {from_display} → {to_display}")
        print(
            f"    Volume: ${pair['total_volume']:,.2f} ({pair['tx_count']} transactions)"
        )
        print(f"    From: {pair['from_asset']}")
        print(f"    To:   {pair['to_asset']}")
        print()

    # Show identified tokens by source
    sources = {}
    for address, info in identified_tokens.items():
        source = info.get("source", "unknown")
        if source not in sources:
            sources[source] = []
        sources[source].append(info)

    print(f"\n📋 Identified Tokens by Source:")
    for source, tokens in sources.items():
        print(f"\n   {source.upper()} ({len(tokens)} tokens):")
        for token in tokens:
            token_type = token.get("type", "")
            type_display = f" [{token_type.upper()}]" if token_type else ""
            print(f"     {token['symbol']} ({token['name']}){type_display}")

    # Show unknown tokens
    unknown_tokens = [addr for addr in token_addresses if addr not in identified_tokens]
    if unknown_tokens:
        print(f"\n❓ Unknown Tokens ({len(unknown_tokens)}):")
        for address in unknown_tokens:
            print(f"   {address}")


if __name__ == "__main__":
    main()
