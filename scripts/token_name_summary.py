#!/usr/bin/env python3
"""
Token Name Summary
Shows statistics about token names across all affiliate tracking databases.
"""

import sqlite3
import os
from typing import Dict, List


def get_token_stats(db_path: str, table_name: str, token_columns: List[str]) -> Dict:
    """Get token statistics for a database table"""
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {"total_records": 0, "token_columns": {}, "top_tokens": {}}

    try:
        # Get total records
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        stats["total_records"] = cursor.fetchone()[0]

        # Get stats for each token column
        for token_col in token_columns:
            name_col = f"{token_col}_name"

            # Check if name column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            if name_col in columns:
                # Get unique token names
                cursor.execute(
                    f"""
                    SELECT {name_col}, COUNT(*) as count 
                    FROM {table_name} 
                    WHERE {name_col} IS NOT NULL 
                    GROUP BY {name_col} 
                    ORDER BY count DESC 
                    LIMIT 10
                """
                )

                token_counts = cursor.fetchall()
                stats["token_columns"][token_col] = {
                    "total_with_names": sum(count for _, count in token_counts),
                    "top_tokens": token_counts,
                }

        conn.close()
        return stats

    except Exception as e:
        print(f"Error getting stats for {db_path}: {e}")
        conn.close()
        return {}


def main():
    """Main function to show token name statistics"""
    print("🔍 TOKEN NAME STATISTICS")
    print("=" * 50)

    # Database configurations
    db_configs = [
        {
            "name": "Relay Affiliate Fees",
            "path": "databases/affiliate.db",
            "table": "relay_affiliate_fees",
            "token_columns": ["token_address"],
        },
        {
            "name": "Relay Claiming Transactions",
            "path": "databases/affiliate.db",
            "table": "relay_claiming_transactions",
            "token_columns": ["token_address"],
        },
        {
            "name": "Portals Transactions",
            "path": "databases/portals_transactions.db",
            "table": "portals_transactions",
            "token_columns": ["input_token", "output_token", "affiliate_token"],
        },
        {
            "name": "CowSwap Transactions",
            "path": "databases/cowswap_transactions.db",
            "table": "cowswap_transactions",
            "token_columns": ["sell_token", "buy_token"],
        },
        {
            "name": "THORChain Transactions",
            "path": "databases/thorchain_transactions.db",
            "table": "thorchain_transactions",
            "token_columns": ["from_asset", "to_asset"],
        },
    ]

    total_records = 0
    total_tokens_with_names = 0

    for config in db_configs:
        print(f"\n📊 {config['name']}")
        print("-" * 30)

        stats = get_token_stats(
            config["path"], config["table"], config["token_columns"]
        )

        if not stats:
            print("   Database not found or empty")
            continue

        total_records += stats["total_records"]
        print(f"   Total records: {stats['total_records']:,}")

        for token_col, token_stats in stats["token_columns"].items():
            print(
                f"   {token_col}: {token_stats['total_with_names']:,} tokens with names"
            )
            total_tokens_with_names += token_stats["total_with_names"]

            if token_stats["top_tokens"]:
                print("   Top tokens:")
                for token_name, count in token_stats["top_tokens"][:5]:
                    print(f"     {token_name}: {count:,}")

    print(f"\n📈 SUMMARY")
    print("=" * 30)
    print(f"Total records across all databases: {total_records:,}")
    print(f"Total tokens with resolved names: {total_tokens_with_names:,}")

    if total_records > 0:
        coverage = (total_tokens_with_names / total_records) * 100
        print(f"Token name coverage: {coverage:.1f}%")


if __name__ == "__main__":
    main()
