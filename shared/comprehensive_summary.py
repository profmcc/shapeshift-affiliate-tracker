#!/usr/bin/env python3
"""
Comprehensive Affiliate Data Summary
Shows all affiliate fee events across all platforms
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def comprehensive_summary():
    """Generate comprehensive summary of all affiliate data"""
    
    db_path = "comprehensive_affiliate_data.db"
    
    if not os.path.exists(db_path):
        print("Comprehensive database not found")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Query all events
    query = '''
    SELECT DISTINCT tx_hash, timestamp, protocol, chain, from_asset, to_asset, 
           from_amount, to_amount, affiliate_fee, affiliate_fee_asset, 
           affiliate_address, pool, status
    FROM affiliate_fees 
    WHERE timestamp IS NOT NULL
    ORDER BY timestamp DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("=" * 100)
    print("COMPREHENSIVE AFFILIATE FEE SUMMARY")
    print("=" * 100)
    
    # Overall statistics
    print(f"Total Unique Events: {len(df)}")
    
    # By platform
    platforms = df['protocol'].value_counts()
    print("\nEvents by Platform:")
    for platform, count in platforms.items():
        print(f"- {platform}: {count} events")
    
    # By chain
    chains = df['chain'].value_counts()
    print("\nEvents by Chain:")
    for chain, count in chains.items():
        print(f"- {chain}: {count} events")
    
    # Total affiliate fees by token
    print("\nTotal Affiliate Fees by Token:")
    affiliate_totals = df.groupby('affiliate_fee_asset')['affiliate_fee'].sum()
    for token, amount in affiliate_totals.items():
        if pd.notna(amount) and amount > 0:
            print(f"- {token}: {amount}")
    
    # Detailed table
    print("\n" + "=" * 100)
    print("DETAILED TRANSACTION TABLE")
    print("=" * 100)
    
    if not df.empty:
        for idx, row in df.iterrows():
            print(f"Transaction: {row['tx_hash']}")
            
            # Handle timestamp safely
            if pd.notna(row['timestamp']) and row['timestamp'] > 0:
                time_str = datetime.fromtimestamp(row['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown"
            print(f"Time: {time_str}")
            
            print(f"Platform: {row['protocol']}")
            print(f"Chain: {row.get('chain', 'Unknown')}")
            print(f"From Asset: {row['from_asset']}")
            print(f"To Asset: {row['to_asset']}")
            print(f"Input: {row['from_amount']} {row['from_asset']}")
            print(f"Output: {row['to_amount']} {row['to_asset']}")
            print(f"Affiliate Fee: {row.get('affiliate_fee', 0)} {row.get('affiliate_fee_asset', 'None')}")
            print(f"Affiliate Address: {row.get('affiliate_address', 'N/A')}")
            print("-" * 100)
    else:
        print("No events found")

if __name__ == "__main__":
    comprehensive_summary() 