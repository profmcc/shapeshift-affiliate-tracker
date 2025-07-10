#!/usr/bin/env python3
"""
0x Protocol Affiliate Data Extractor
Extracts and displays 0x Protocol-specific affiliate fee events
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def extract_0x_data():
    """Extract 0x Protocol-specific data from the comprehensive database"""
    
    db_path = "../shared/comprehensive_affiliate_data.db"
    
    if not os.path.exists(db_path):
        print("Comprehensive database not found")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Query 0x Protocol events
    query = '''
    SELECT DISTINCT tx_hash, timestamp, protocol, chain, from_asset, to_asset, 
           from_amount, to_amount, affiliate_fee, affiliate_fee_asset, 
           affiliate_address, pool, status
    FROM affiliate_fees 
    WHERE protocol = '0x Protocol' AND timestamp IS NOT NULL
    ORDER BY timestamp DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("=" * 80)
    print("0X PROTOCOL AFFILIATE EVENTS")
    print("=" * 80)
    
    if not df.empty:
        for idx, row in df.iterrows():
            print(f"Transaction: {row['tx_hash']}")
            
            # Handle timestamp safely
            if pd.notna(row['timestamp']) and row['timestamp'] > 0:
                time_str = datetime.fromtimestamp(row['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown"
            print(f"Time: {time_str}")
            
            print(f"Chain: {row.get('chain', 'Unknown')}")
            print(f"From Asset: {row['from_asset']}")
            print(f"To Asset: {row['to_asset']}")
            print(f"Input: {row['from_amount']} {row['from_asset']}")
            print(f"Output: {row['to_amount']} {row['to_asset']}")
            print(f"Affiliate Fee: {row.get('affiliate_fee', 0)} {row.get('affiliate_fee_asset', 'None')}")
            print(f"Affiliate Address: {row.get('affiliate_address', 'N/A')}")
            print("-" * 80)
    else:
        print("No 0x Protocol events found")
    
    print(f"\nTotal 0x Protocol Events: {len(df)}")
    
    if not df.empty:
        # Show total affiliate fees by token
        print("\nTotal Affiliate Fees by Token:")
        affiliate_totals = df.groupby('affiliate_fee_asset')['affiliate_fee'].sum()
        for token, amount in affiliate_totals.items():
            if pd.notna(amount) and amount > 0:
                print(f"- {token}: {amount}")

if __name__ == "__main__":
    extract_0x_data() 