#!/usr/bin/env python3
"""
Backfill Affiliate Fees Script

This script updates all existing transactions in the Chainflip database
with the correct ShapeShift affiliate fees based on their swap dates.

- Before May 31, 2024: 0.5% (50 bps)
- On/after May 31, 2024: 0.55% (55 bps)
"""

import sqlite3
from datetime import datetime
from chainflip_database import ChainflipDatabase


def calculate_affiliate_fee(from_amount_usd: float, timestamp: datetime) -> float:
    """
    Calculate the correct ShapeShift affiliate fee based on swap date.
    
    Args:
        from_amount_usd: The USD amount of the swap
        timestamp: The timestamp of the swap
        
    Returns:
        The calculated affiliate fee in USD
    """
    # Cutoff date for affiliate fee change (May 31, 2024)
    cutoff_date = datetime(2024, 5, 31, 0, 0, 0)
    
    if timestamp < cutoff_date:
        # Before May 31, 2024: 0.5% (50 bps)
        return from_amount_usd * 0.005
    else:
        # On/after May 31, 2024: 0.55% (55 bps)
        return from_amount_usd * 0.0055


def backfill_affiliate_fees(db_path: str = "chainflip_transactions.db"):
    """
    Backfill all existing transactions with correct affiliate fees.
    
    Args:
        db_path: Path to the SQLite database
    """
    print("🔄 Starting affiliate fee backfill...")
    print("=" * 60)
    
    try:
        # Initialize database to ensure schema is up to date
        database = ChainflipDatabase(db_path)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all transactions that need updating
            cursor.execute("""
                SELECT id, transaction_id, from_amount_usd, timestamp, affiliate_fee_usd
                FROM transactions 
                ORDER BY CAST(transaction_id AS INTEGER)
            """)
            
            transactions = cursor.fetchall()
            
            if not transactions:
                print("❌ No transactions found in database")
                return
            
            print(f"📊 Found {len(transactions)} transactions to process")
            
            # Process each transaction
            updated_count = 0
            total_old_fees = 0.0
            total_new_fees = 0.0
            
            for row in transactions:
                transaction_id, tx_id, from_amount_usd, timestamp_str, current_affiliate_fee = row
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    # Fallback for different timestamp formats
                    timestamp = datetime.now()
                
                # Calculate correct affiliate fee
                correct_affiliate_fee = calculate_affiliate_fee(from_amount_usd, timestamp)
                
                # Update if different
                if abs(correct_affiliate_fee - current_affiliate_fee) > 0.001:  # Allow for small floating point differences
                    cursor.execute("""
                        UPDATE transactions 
                        SET affiliate_fee_usd = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (correct_affiliate_fee, transaction_id))
                    
                    updated_count += 1
                    total_old_fees += current_affiliate_fee
                    total_new_fees += correct_affiliate_fee
                    
                    # Print progress for first few updates
                    if updated_count <= 5:
                        print(f"✅ Updated TX #{tx_id}: ${current_affiliate_fee:.2f} → ${correct_affiliate_fee:.2f}")
                    elif updated_count == 6:
                        print("... (continuing updates)")
            
            conn.commit()
            
            # Print summary
            print(f"\n📈 BACKFILL COMPLETE")
            print(f"Transactions updated: {updated_count:,}")
            print(f"Total old affiliate fees: ${total_old_fees:,.2f}")
            print(f"Total new affiliate fees: ${total_new_fees:,.2f}")
            print(f"Difference: ${total_new_fees - total_old_fees:+,.2f}")
            
            if updated_count > 0:
                print(f"\n💰 Expected ShapeShift affiliate revenue: ${total_new_fees:,.2f}")
            
            # Show updated database stats
            print("\n" + "=" * 60)
            database.print_stats()
            
    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        raise


def main():
    """Main function."""
    print("🔄 Chainflip Affiliate Fee Backfill")
    print("=" * 60)
    print("This script will update all existing transactions with the correct")
    print("ShapeShift affiliate fees based on their swap dates:")
    print("- Before May 31, 2024: 0.5% (50 bps)")
    print("- On/after May 31, 2024: 0.55% (55 bps)")
    print("=" * 60)
    
    # Run the backfill
    backfill_affiliate_fees()
    
    print(f"\n✅ Backfill completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main() 