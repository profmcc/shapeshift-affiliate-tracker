#!/usr/bin/env python3
"""
Quick Database Test

Simple script to test the Chainflip database without interactive prompts.
"""

import asyncio
from chainflip_database import ChainflipDatabase


def quick_test():
    """Quick test of the database."""
    print("🔍 QUICK DATABASE TEST")
    print("=" * 40)
    
    # Initialize database
    database = ChainflipDatabase()
    
    # Show stats
    print("\n1. Database Statistics:")
    database.print_stats()
    
    # Show recent transactions
    print("\n2. Recent Transactions:")
    try:
        import sqlite3
        import pandas as pd
        with sqlite3.connect(database.db_path) as conn:
            query = """
                SELECT 
                    transaction_id, from_currency, to_currency, from_amount, to_amount,
                    from_amount_usd, to_amount_usd, status, commission_usd, timestamp
                FROM transactions 
                ORDER BY CAST(transaction_id AS INTEGER) DESC 
                LIMIT 5
            """
            df = pd.read_sql_query(query, conn)
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Error querying: {e}")
    
    # Show volume by currency
    print("\n3. Volume by Currency (Last 7 days):")
    try:
        import sqlite3
        import pandas as pd
        with sqlite3.connect(database.db_path) as conn:
            query = """
                SELECT 
                    from_currency, to_currency,
                    SUM(from_amount_usd) as total_volume_usd,
                    COUNT(*) as transaction_count,
                    AVG(commission_usd) as avg_commission
                FROM transactions 
                WHERE timestamp >= datetime('now', '-7 days')
                AND status = 'Success'
                GROUP BY from_currency, to_currency
                ORDER BY total_volume_usd DESC
            """
            df = pd.read_sql_query(query, conn)
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Error querying: {e}")


if __name__ == "__main__":
    quick_test() 