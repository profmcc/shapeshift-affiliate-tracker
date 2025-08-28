#!/usr/bin/env python3
"""
Check Portals data in comprehensive database
"""

import sqlite3
from datetime import datetime


def check_portals_data():
    """Check Portals data in comprehensive database"""

    conn = sqlite3.connect("databases/comprehensive_affiliate.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT tx_hash, chain, volume_usd, affiliate_fee_usd, timestamp 
        FROM comprehensive_transactions 
        WHERE protocol = 'Portals' AND volume_usd > 0
        LIMIT 5
    """
    )

    results = cursor.fetchall()
    print("📊 Portals transactions in comprehensive database:")
    for tx_hash, chain, volume, fee, timestamp in results:
        date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        print(f"   TX: {tx_hash}")
        print(f"   Chain: {chain}")
        print(f"   Volume: ${volume:,.2f}")
        print(f"   Fee: ${fee:,.2f}")
        print(f"   Date: {date}")
        print()

    # Check all Portals data
    cursor.execute(
        """
        SELECT COUNT(*) as total,
               COUNT(DISTINCT chain) as chains,
               SUM(volume_usd) as total_volume,
               SUM(affiliate_fee_usd) as total_fees
        FROM comprehensive_transactions 
        WHERE protocol = 'Portals'
    """
    )

    total, chains, volume, fees = cursor.fetchone()
    print(f"📈 Portals Summary:")
    print(f"   Total transactions: {total}")
    print(f"   Chains: {chains}")
    print(f"   Total volume: ${volume:,.2f}")
    print(f"   Total fees: ${fees:,.2f}")

    # Check by chain
    cursor.execute(
        """
        SELECT chain, COUNT(*) as count, SUM(volume_usd) as volume, SUM(affiliate_fee_usd) as fees
        FROM comprehensive_transactions 
        WHERE protocol = 'Portals'
        GROUP BY chain
    """
    )

    print(f"\n📊 By Chain:")
    for chain, count, volume, fees in cursor.fetchall():
        print(f"   {chain}: {count} txs, ${volume:,.2f} volume, ${fees:,.2f} fees")

    conn.close()


if __name__ == "__main__":
    check_portals_data()
