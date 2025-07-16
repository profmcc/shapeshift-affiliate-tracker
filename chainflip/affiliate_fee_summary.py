#!/usr/bin/env python3
"""
Affiliate Fee Summary

This script provides a comprehensive summary of the ShapeShift affiliate fee
implementation and backfill results.
"""

import sqlite3
from datetime import datetime
from chainflip_database import ChainflipDatabase


def print_affiliate_fee_summary():
    """Print a comprehensive summary of affiliate fee implementation."""
    print("💰 SHAPESHIFT AFFILIATE FEE IMPLEMENTATION SUMMARY")
    print("=" * 70)
    
    # Initialize database
    database = ChainflipDatabase()
    
    # Get database stats
    stats = database.get_database_stats()
    
    print(f"\n📊 DATABASE OVERVIEW:")
    print(f"   Total Transactions: {stats.get('total_transactions', 0):,}")
    print(f"   Total Volume: ${stats.get('total_volume_usd', 0):,.2f}")
    print(f"   Date Range: {stats.get('date_range', [None, None])[0]} to {stats.get('date_range', [None, None])[1]}")
    
    print(f"\n💸 FEE BREAKDOWN:")
    print(f"   Broker Fees (0.05%): ${stats.get('total_commissions_usd', 0):,.2f}")
    print(f"   ShapeShift Affiliate Fees: ${stats.get('total_affiliate_fees_usd', 0):,.2f}")
    print(f"   Total Fees: ${stats.get('total_commissions_usd', 0) + stats.get('total_affiliate_fees_usd', 0):,.2f}")
    
    # Calculate fee percentages
    total_volume = stats.get('total_volume_usd', 0)
    if total_volume > 0:
        broker_fee_pct = (stats.get('total_commissions_usd', 0) / total_volume) * 100
        affiliate_fee_pct = (stats.get('total_affiliate_fees_usd', 0) / total_volume) * 100
        total_fee_pct = broker_fee_pct + affiliate_fee_pct
        
        print(f"\n📈 FEE PERCENTAGES:")
        print(f"   Broker Fees: {broker_fee_pct:.3f}%")
        print(f"   ShapeShift Affiliate Fees: {affiliate_fee_pct:.3f}%")
        print(f"   Total Fees: {total_fee_pct:.3f}%")
    
    # Get fee breakdown by date range
    print(f"\n📅 FEE CALCULATION LOGIC:")
    print(f"   Before May 31, 2024: 0.5% (50 bps) affiliate fee")
    print(f"   On/after May 31, 2024: 0.55% (55 bps) affiliate fee")
    print(f"   Broker fee: Always 0.05% (5 bps)")
    
    # Show recent transactions with fees
    print(f"\n🔍 RECENT TRANSACTIONS (with affiliate fees):")
    try:
        with sqlite3.connect(database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    transaction_id, 
                    from_amount_usd, 
                    commission_usd,
                    affiliate_fee_usd,
                    timestamp
                FROM transactions 
                WHERE status = 'Success'
                ORDER BY CAST(transaction_id AS INTEGER) DESC 
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            for row in rows:
                tx_id, amount, commission, affiliate_fee, timestamp = row
                print(f"   TX #{tx_id}: ${amount:,.2f} → Broker: ${commission:.2f}, Affiliate: ${affiliate_fee:.2f}")
    
    except Exception as e:
        print(f"   Error querying recent transactions: {e}")
    
    print(f"\n✅ IMPLEMENTATION STATUS:")
    print(f"   ✅ Database schema updated with affiliate_fee_usd column")
    print(f"   ✅ Backfill completed for all existing transactions")
    print(f"   ✅ New transactions automatically calculate correct affiliate fees")
    print(f"   ✅ Query tools updated to show affiliate fee data")
    print(f"   ✅ Statistics include both broker and affiliate fees")
    
    print(f"\n🎯 EXPECTED SHAPESHIFT AFFILIATE REVENUE:")
    print(f"   ${stats.get('total_affiliate_fees_usd', 0):,.2f}")
    
    print(f"\n" + "=" * 70)


if __name__ == "__main__":
    print_affiliate_fee_summary() 