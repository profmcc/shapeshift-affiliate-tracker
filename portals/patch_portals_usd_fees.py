#!/usr/bin/env python3
"""
Patch Portals USDC/USDT Affiliate Fees in Database
"""

import sqlite3

DB_PATH = "shared/comprehensive_affiliate_data.db"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"

def patch_portals_usd_fees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Patch USDC
    cursor.execute(f"""
        UPDATE affiliate_fees
        SET affiliate_fee = affiliate_fee * 1e12
        WHERE protocol = 'Portals' AND affiliate_fee_asset = '{USDC}' AND affiliate_fee < 1
    """)
    # Patch USDT
    cursor.execute(f"""
        UPDATE affiliate_fees
        SET affiliate_fee = affiliate_fee * 1e12
        WHERE protocol = 'Portals' AND affiliate_fee_asset = '{USDT}' AND affiliate_fee < 1
    """)
    conn.commit()
    # Show results
    cursor.execute(f"""
        SELECT tx_hash, affiliate_fee, affiliate_fee_asset
        FROM affiliate_fees
        WHERE protocol = 'Portals' AND (affiliate_fee_asset = '{USDC}' OR affiliate_fee_asset = '{USDT}')
    """)
    rows = cursor.fetchall()
    print("Patched Portals USDC/USDT affiliate fees:")
    for row in rows:
        print(f"  TX: {row[0]}  Fee: {row[1]}  Asset: {row[2]}")
    conn.close()

if __name__ == "__main__":
    patch_portals_usd_fees()
