#!/usr/bin/env python3
"""
July 2025 Affiliate Fee Analysis
Analyzes volume and affiliate fees for July 2025 from the comprehensive database.
"""

import sqlite3
from datetime import datetime
import os


def analyze_july_2025():
    """Analyze July 2025 affiliate fee data"""

    # Connect to the comprehensive database
    db_path = "databases/comprehensive_affiliate.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get July 2025 data (timestamp range)
    july_start = int(datetime(2025, 7, 1).timestamp())
    july_end = int(datetime(2025, 8, 1).timestamp())

    print("📊 July 2025 Affiliate Fee Analysis")
    print("=" * 50)

    # Query for July data
    cursor.execute(
        """
        SELECT 
            protocol,
            COUNT(*) as transaction_count,
            SUM(volume_usd) as total_volume,
            SUM(affiliate_fee_usd) as total_affiliate_fees,
            AVG(volume_usd) as avg_volume,
            AVG(affiliate_fee_usd) as avg_fee
        FROM comprehensive_transactions 
        WHERE timestamp >= ? AND timestamp < ?
        GROUP BY protocol
        ORDER BY total_volume DESC
    """,
        (july_start, july_end),
    )

    july_data = cursor.fetchall()

    if july_data:
        print(f"Found {len(july_data)} protocols with July 2025 data:")
        print()

        total_volume = 0
        total_fees = 0
        total_txs = 0

        for protocol, tx_count, volume, fees, avg_vol, avg_fee in july_data:
            volume = volume or 0
            fees = fees or 0
            avg_vol = avg_vol or 0
            avg_fee = avg_fee or 0

            print(f"🔸 {protocol}:")
            print(f"   Transactions: {tx_count:,}")
            print(f"   Volume: ${volume:,.2f}")
            print(f"   Affiliate Fees: ${fees:,.2f}")
            print(f"   Avg Volume per TX: ${avg_vol:,.2f}")
            print(f"   Avg Fee per TX: ${avg_fee:,.2f}")
            print()

            total_volume += volume
            total_fees += fees
            total_txs += tx_count

        print("📈 JULY 2025 SUMMARY:")
        print(f"   Total Transactions: {total_txs:,}")
        print(f"   Total Volume: ${total_volume:,.2f}")
        print(f"   Total Affiliate Fees: ${total_fees:,.2f}")
        if total_txs > 0:
            print(f"   Average Volume per Transaction: ${total_volume/total_txs:,.2f}")
            print(f"   Average Fee per Transaction: ${total_fees/total_txs:,.2f}")
        else:
            print("   Average Volume per Transaction: $0.00")
            print("   Average Fee per Transaction: $0.00")

        # Additional analysis
        print("\n📊 ADDITIONAL INSIGHTS:")

        # Top transactions by volume
        cursor.execute(
            """
            SELECT protocol, tx_hash, volume_usd, affiliate_fee_usd, timestamp
            FROM comprehensive_transactions 
            WHERE timestamp >= ? AND timestamp < ? AND volume_usd > 0
            ORDER BY volume_usd DESC
            LIMIT 5
        """,
            (july_start, july_end),
        )

        top_txs = cursor.fetchall()
        if top_txs:
            print("\n🏆 Top 5 Transactions by Volume:")
            for i, (protocol, tx_hash, volume, fee, ts) in enumerate(top_txs, 1):
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                print(f"   {i}. {protocol}: ${volume:,.2f} (Fee: ${fee:,.2f}) - {date}")
                print(f"      TX: {tx_hash}")

        # Daily breakdown
        cursor.execute(
            """
            SELECT 
                DATE(datetime(timestamp, 'unixepoch')) as date,
                COUNT(*) as tx_count,
                SUM(volume_usd) as daily_volume,
                SUM(affiliate_fee_usd) as daily_fees
            FROM comprehensive_transactions 
            WHERE timestamp >= ? AND timestamp < ?
            GROUP BY DATE(datetime(timestamp, 'unixepoch'))
            ORDER BY date
        """,
            (july_start, july_end),
        )

        daily_data = cursor.fetchall()
        if daily_data:
            print("\n📅 Daily Breakdown:")
            for date, tx_count, volume, fees in daily_data:
                volume = volume or 0
                fees = fees or 0
                print(
                    f"   {date}: {tx_count} txs, ${volume:,.2f} volume, ${fees:,.2f} fees"
                )

    else:
        print("❌ No July 2025 data found in the database")

        # Check what date ranges we have
        cursor.execute(
            """
            SELECT 
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                COUNT(*) as total_records
            FROM comprehensive_transactions
        """
        )

        earliest, latest, total = cursor.fetchone()

        if earliest and latest:
            earliest_date = datetime.fromtimestamp(earliest)
            latest_date = datetime.fromtimestamp(latest)
            print(
                f'📅 Available data range: {earliest_date.strftime("%Y-%m-%d")} to {latest_date.strftime("%Y-%m-%d")}'
            )
            print(f"📊 Total records in database: {total:,}")

            # Check if we have any data at all
            if total > 0:
                print("\n🔍 Checking for any recent data...")
                cursor.execute(
                    """
                    SELECT 
                        protocol,
                        COUNT(*) as tx_count,
                        SUM(volume_usd) as total_volume,
                        SUM(affiliate_fee_usd) as total_fees
                    FROM comprehensive_transactions 
                    GROUP BY protocol
                    ORDER BY total_volume DESC
                """
                )

                all_data = cursor.fetchall()
                if all_data:
                    print("\n📊 All Available Data by Protocol:")
                    for protocol, tx_count, volume, fees in all_data:
                        volume = volume or 0
                        fees = fees or 0
                        print(
                            f"   {protocol}: {tx_count:,} txs, ${volume:,.2f} volume, ${fees:,.2f} fees"
                        )
        else:
            print("❌ No data found in comprehensive database")

    conn.close()


def analyze_all_available_data():
    """Analyze all available data in the database"""

    # Connect to the comprehensive database
    db_path = "databases/comprehensive_affiliate.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n📊 ALL AVAILABLE DATA ANALYSIS")
    print("=" * 50)

    # Get all data summary
    cursor.execute(
        """
        SELECT 
            protocol,
            COUNT(*) as transaction_count,
            SUM(volume_usd) as total_volume,
            SUM(affiliate_fee_usd) as total_affiliate_fees,
            AVG(volume_usd) as avg_volume,
            AVG(affiliate_fee_usd) as avg_fee,
            MIN(timestamp) as earliest_tx,
            MAX(timestamp) as latest_tx
        FROM comprehensive_transactions 
        GROUP BY protocol
        ORDER BY total_volume DESC
    """
    )

    all_data = cursor.fetchall()

    if all_data:
        total_volume = 0
        total_fees = 0
        total_txs = 0

        for (
            protocol,
            tx_count,
            volume,
            fees,
            avg_vol,
            avg_fee,
            earliest,
            latest,
        ) in all_data:
            volume = volume or 0
            fees = fees or 0
            avg_vol = avg_vol or 0
            avg_fee = avg_fee or 0

            earliest_date = datetime.fromtimestamp(earliest).strftime("%Y-%m-%d")
            latest_date = datetime.fromtimestamp(latest).strftime("%Y-%m-%d")

            print(f"🔸 {protocol}:")
            print(f"   Transactions: {tx_count:,}")
            print(f"   Volume: ${volume:,.2f}")
            print(f"   Affiliate Fees: ${fees:,.2f}")
            print(f"   Avg Volume per TX: ${avg_vol:,.2f}")
            print(f"   Avg Fee per TX: ${avg_fee:,.2f}")
            print(f"   Date Range: {earliest_date} to {latest_date}")
            print()

            total_volume += volume
            total_fees += fees
            total_txs += tx_count

        print("📈 OVERALL SUMMARY:")
        print(f"   Total Transactions: {total_txs:,}")
        print(f"   Total Volume: ${total_volume:,.2f}")
        print(f"   Total Affiliate Fees: ${total_fees:,.2f}")
        if total_txs > 0:
            print(f"   Average Volume per Transaction: ${total_volume/total_txs:,.2f}")
            print(f"   Average Fee per Transaction: ${total_fees/total_txs:,.2f}")

        # Top transactions overall
        cursor.execute(
            """
            SELECT protocol, tx_hash, volume_usd, affiliate_fee_usd, timestamp
            FROM comprehensive_transactions 
            WHERE volume_usd > 0
            ORDER BY volume_usd DESC
            LIMIT 10
        """
        )

        top_txs = cursor.fetchall()
        if top_txs:
            print("\n🏆 Top 10 Transactions by Volume:")
            for i, (protocol, tx_hash, volume, fee, ts) in enumerate(top_txs, 1):
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                print(f"   {i}. {protocol}: ${volume:,.2f} (Fee: ${fee:,.2f}) - {date}")
                print(f"      TX: {tx_hash}")

    conn.close()


if __name__ == "__main__":
    analyze_july_2025()
    analyze_all_available_data()
