#!/usr/bin/env python3
"""
Chainflip Database Query Tool

Interactive tool for querying and analyzing Chainflip transaction data.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from chainflip_database import ChainflipDatabase


class ChainflipQueryTool:
    def __init__(self, db_path: str = "chainflip_transactions.db"):
        self.database = ChainflipDatabase(db_path)
    
    def get_recent_transactions(self, limit: int = 10):
        """Get recent transactions."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        transaction_id, from_currency, to_currency, from_amount, to_amount,
                        from_amount_usd, to_amount_usd, status, commission_usd, affiliate_fee_usd, timestamp
                    FROM transactions 
                    ORDER BY CAST(transaction_id AS INTEGER) DESC 
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
        except Exception as e:
            print(f"Error querying recent transactions: {e}")
            return pd.DataFrame()
    
    def get_volume_by_currency(self, days: int = 7):
        """Get trading volume by currency pair."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        from_currency, to_currency,
                        SUM(from_amount_usd) as total_volume_usd,
                        COUNT(*) as transaction_count,
                        AVG(commission_usd) as avg_commission
                    FROM transactions 
                    WHERE timestamp >= datetime('now', '-{} days')
                    AND status = 'Success'
                    GROUP BY from_currency, to_currency
                    ORDER BY total_volume_usd DESC
                """.format(days)
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error querying volume by currency: {e}")
            return pd.DataFrame()
    
    def get_top_addresses(self, limit: int = 10):
        """Get top addresses by transaction volume."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        address,
                        SUM(volume_usd) as total_volume_usd,
                        COUNT(*) as transaction_count
                    FROM (
                        SELECT from_address as address, from_amount_usd as volume_usd
                        FROM transactions WHERE status = 'Success'
                        UNION ALL
                        SELECT to_address as address, to_amount_usd as volume_usd
                        FROM transactions WHERE status = 'Success'
                    )
                    GROUP BY address
                    ORDER BY total_volume_usd DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
        except Exception as e:
            print(f"Error querying top addresses: {e}")
            return pd.DataFrame()
    
    def get_daily_stats(self, days: int = 30):
        """Get daily statistics."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as transaction_count,
                        SUM(from_amount_usd) as total_volume_usd,
                        SUM(commission_usd) as total_commissions_usd,
                        SUM(affiliate_fee_usd) as total_affiliate_fees_usd,
                        AVG(from_amount_usd) as avg_transaction_size
                    FROM transactions 
                    WHERE timestamp >= datetime('now', '-{} days')
                    AND status = 'Success'
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """.format(days)
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error querying daily stats: {e}")
            return pd.DataFrame()
    
    def search_transactions(self, search_term: str):
        """Search transactions by ID, address, or currency."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        transaction_id, from_address, to_address, from_currency, to_currency,
                        from_amount, to_amount, from_amount_usd, to_amount_usd, status, timestamp
                    FROM transactions 
                    WHERE transaction_id LIKE ? 
                    OR from_address LIKE ? 
                    OR to_address LIKE ? 
                    OR from_currency LIKE ? 
                    OR to_currency LIKE ?
                    ORDER BY CAST(transaction_id AS INTEGER) DESC
                    LIMIT 50
                """
                search_pattern = f"%{search_term}%"
                df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
                return df
        except Exception as e:
            print(f"Error searching transactions: {e}")
            return pd.DataFrame()
    
    def export_data(self, filename: str = None):
        """Export all data to CSV."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_export_{timestamp}.csv"
        
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                query = """
                    SELECT 
                        transaction_id, from_address, to_address, from_currency, to_currency,
                        from_amount, to_amount, from_amount_usd, to_amount_usd, status,
                        commission_usd, timestamp, duration_minutes, broker_address
                    FROM transactions 
                    ORDER BY CAST(transaction_id AS INTEGER) DESC
                """
                df = pd.read_sql_query(query, conn)
                df.to_csv(filename, index=False)
                print(f"✅ Exported {len(df)} transactions to {filename}")
                return filename
        except Exception as e:
            print(f"Error exporting data: {e}")
            return None


def main():
    """Interactive query tool."""
    tool = ChainflipQueryTool()
    
    print("🔍 Chainflip Database Query Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Show recent transactions")
        print("2. Show volume by currency (7 days)")
        print("3. Show top addresses")
        print("4. Show daily stats (30 days)")
        print("5. Search transactions")
        print("6. Export all data")
        print("7. Show database stats")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            limit = input("Number of transactions to show (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            df = tool.get_recent_transactions(limit)
            print(f"\nRecent {len(df)} transactions:")
            print(df.to_string(index=False))
            
        elif choice == "2":
            days = input("Number of days (default 7): ").strip()
            days = int(days) if days.isdigit() else 7
            df = tool.get_volume_by_currency(days)
            print(f"\nVolume by currency (last {days} days):")
            print(df.to_string(index=False))
            
        elif choice == "3":
            limit = input("Number of addresses to show (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            df = tool.get_top_addresses(limit)
            print(f"\nTop {len(df)} addresses by volume:")
            print(df.to_string(index=False))
            
        elif choice == "4":
            days = input("Number of days (default 30): ").strip()
            days = int(days) if days.isdigit() else 30
            df = tool.get_daily_stats(days)
            print(f"\nDaily stats (last {days} days):")
            print(df.to_string(index=False))
            
        elif choice == "5":
            search_term = input("Enter search term: ").strip()
            if search_term:
                df = tool.search_transactions(search_term)
                print(f"\nSearch results for '{search_term}':")
                print(df.to_string(index=False))
            else:
                print("Please enter a search term.")
                
        elif choice == "6":
            filename = input("Export filename (or press Enter for default): ").strip()
            if not filename:
                filename = None
            exported_file = tool.export_data(filename)
            if exported_file:
                print(f"Data exported to: {exported_file}")
                
        elif choice == "7":
            tool.database.print_stats()
            
        elif choice == "8":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main() 