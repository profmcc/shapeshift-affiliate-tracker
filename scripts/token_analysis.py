#!/usr/bin/env python3
"""
Token Analysis
Analyzes the most common tokens across all affiliate tracking protocols.
"""

import sqlite3
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def get_all_token_names() -> Dict[str, int]:
    """Get all token names and their counts across all databases"""
    token_counts = defaultdict(int)

    # Database configurations
    db_configs = [
        {
            "path": "databases/affiliate.db",
            "table": "relay_affiliate_fees",
            "token_columns": ["token_address"],
        },
        {
            "path": "databases/affiliate.db",
            "table": "relay_claiming_transactions",
            "token_columns": ["token_address"],
        },
        {
            "path": "databases/portals_transactions.db",
            "table": "portals_transactions",
            "token_columns": ["input_token", "output_token", "affiliate_token"],
        },
        {
            "path": "databases/cowswap_transactions.db",
            "table": "cowswap_transactions",
            "token_columns": ["sell_token", "buy_token"],
        },
        {
            "path": "databases/thorchain_transactions.db",
            "table": "thorchain_transactions",
            "token_columns": ["from_asset", "to_asset"],
        },
    ]

    for config in db_configs:
        if not os.path.exists(config["path"]):
            continue

        conn = sqlite3.connect(config["path"])
        cursor = conn.cursor()

        for token_col in config["token_columns"]:
            name_col = f"{token_col}_name"

            # Check if name column exists
            cursor.execute(f"PRAGMA table_info({config['table']})")
            columns = [row[1] for row in cursor.fetchall()]

            if name_col in columns:
                cursor.execute(
                    f"""
                    SELECT {name_col}, COUNT(*) as count 
                    FROM {config['table']} 
                    WHERE {name_col} IS NOT NULL 
                    GROUP BY {name_col}
                """
                )

                for token_name, count in cursor.fetchall():
                    if (
                        token_name
                        and token_name != "0x0000000000000000000000000000000000000000"
                    ):
                        token_counts[token_name] += count

        conn.close()

    return dict(token_counts)


def analyze_token_distribution():
    """Analyze token distribution across protocols"""
    print("🔍 TOKEN DISTRIBUTION ANALYSIS")
    print("=" * 50)

    token_counts = get_all_token_names()

    if not token_counts:
        print("No token data found")
        return

    # Sort by count
    sorted_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\n📊 Top 20 Tokens by Affiliate Fee Volume:")
    print("-" * 40)

    total_fees = sum(token_counts.values())

    for i, (token_name, count) in enumerate(sorted_tokens[:20], 1):
        percentage = (count / total_fees) * 100
        print(f"{i:2d}. {token_name:15} {count:8,} fees ({percentage:5.1f}%)")

    print(f"\n📈 SUMMARY:")
    print(f"Total unique tokens: {len(token_counts)}")
    print(f"Total affiliate fees: {total_fees:,}")

    # Analyze by token type
    stablecoins = ["USDC", "USDT", "DAI", "BUSD", "TUSD", "FRAX"]
    wrapped_tokens = ["WETH", "WBTC", "WMATIC", "WAVAX"]
    native_tokens = ["ETH", "MATIC", "AVAX", "BNB"]

    stablecoin_fees = sum(
        count for token, count in token_counts.items() if token in stablecoins
    )
    wrapped_fees = sum(
        count for token, count in token_counts.items() if token in wrapped_tokens
    )
    native_fees = sum(
        count for token, count in token_counts.items() if token in native_tokens
    )
    other_fees = total_fees - stablecoin_fees - wrapped_fees - native_fees

    print(f"\n💰 Token Type Breakdown:")
    print(
        f"   Stablecoins: {stablecoin_fees:,} fees ({(stablecoin_fees/total_fees)*100:.1f}%)"
    )
    print(
        f"   Wrapped tokens: {wrapped_fees:,} fees ({(wrapped_fees/total_fees)*100:.1f}%)"
    )
    print(
        f"   Native tokens: {native_fees:,} fees ({(native_fees/total_fees)*100:.1f}%)"
    )
    print(f"   Other tokens: {other_fees:,} fees ({(other_fees/total_fees)*100:.1f}%)")


def main():
    """Main function"""
    analyze_token_distribution()


if __name__ == "__main__":
    main()
