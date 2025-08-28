#!/usr/bin/env python3
"""
Analyze Top Trading Pairs by Volume
Query the THORChain consolidated database for top trading pairs in the last 30 days
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def get_asset_usd_prices():
    """Get approximate USD prices for major assets (simplified pricing)"""
    # This is a simplified price mapping - in production you'd want real-time prices
    prices = {
        "BTC": 65000,  # ~$65,000
        "ETH": 3500,  # ~$3,500
        "USDT": 1.00,  # $1.00
        "USDC": 1.00,  # $1.00
        "RUNE": 0.50,  # ~$0.50
        "TCY": 0.001,  # ~$0.001 (very small cap token)
        "LINK": 0.00,  # No minimum threshold
        "DOGE": 0.08,  # ~$0.08
        "LTC": 70.00,  # ~$70.00
        "ATOM": 7.50,  # ~$7.50
        "FOX": 0.15,  # ~$0.15
    }
    return prices


def get_top_trading_pairs(days=30):
    """Get top 10 trading pairs by volume in the last N days"""

    # Database path
    db_path = Path(__file__).parent.parent / "databases" / "thorchain_consolidated.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    # Calculate date threshold
    cutoff_date = datetime.now() - timedelta(days=days)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Query for top trading pairs by volume in last 30 days
        query = """
        SELECT 
            from_asset,
            to_asset,
            COUNT(*) as trade_count,
            SUM(COALESCE(from_amount, 0)) as total_from_amount,
            SUM(COALESCE(to_amount, 0)) as total_to_amount,
            MIN(timestamp) as earliest_trade,
            MAX(timestamp) as latest_trade
        FROM thorchain_transactions 
        WHERE timestamp >= ?
            AND from_asset IS NOT NULL 
            AND to_asset IS NOT NULL
            AND from_asset != to_asset
            AND status = 'Success'
        GROUP BY from_asset, to_asset
        ORDER BY trade_count DESC, total_from_amount DESC
        LIMIT 10
        """

        cursor.execute(query, (cutoff_date.strftime("%b %d %Y"),))
        results = cursor.fetchall()

        if not results:
            print(f"❌ No trading data found in the last {days} days")
            return

        # Get asset prices for USD conversion
        prices = get_asset_usd_prices()

        print(f"🔍 Top 10 Trading Pairs by Volume (Last {days} Days)")
        print("=" * 100)
        print(
            f"{'Rank':<4} {'From Asset':<8} {'To Asset':<8} {'Trades':<8} {'From Volume':<15} {'From USD':<12} {'To Volume':<15} {'To USD':<12} {'Date Range':<25}"
        )
        print("-" * 100)

        total_from_usd = 0
        total_to_usd = 0

        for rank, (
            from_asset,
            to_asset,
            trade_count,
            total_from,
            total_to,
            earliest,
            latest,
        ) in enumerate(results, 1):
            # Calculate USD values
            from_price = prices.get(from_asset, 0)
            to_price = prices.get(to_asset, 0)

            from_usd = total_from * from_price if total_from and from_price else 0
            to_usd = total_to * to_price if total_to and to_price else 0

            total_from_usd += from_usd
            total_to_usd += to_usd

            # Format volumes with appropriate precision
            from_vol = f"{total_from:,.2f}" if total_from else "0.00"
            to_vol = f"{total_to:,.2f}" if total_to else "0.00"

            # Format USD values
            from_usd_str = f"${from_usd:,.0f}" if from_usd else "$0"
            to_usd_str = f"${to_usd:,.0f}" if to_usd else "$0"

            # Format date range
            if earliest and latest:
                date_range = f"{earliest[:10]} to {latest[:10]}"
            else:
                date_range = "N/A"

            print(
                f"{rank:<4} {from_asset:<8} {to_asset:<8} {trade_count:<8} {from_vol:<15} {from_usd_str:<12} {to_vol:<15} {to_usd_str:<12} {date_range:<25}"
            )

        print("-" * 100)
        print(
            f"{'TOTAL':<4} {'':<8} {'':<8} {'':<8} {'':<15} {'${:,.0f}'.format(total_from_usd):<12} {'':<15} {'${:,.0f}'.format(total_to_usd):<12} {'':<25}"
        )
        print("=" * 100)

        # Additional statistics
        print(f"\n📊 Summary Statistics:")
        print(f"   • Total unique trading pairs: {len(results)}")
        print(f"   • Total trades analyzed: {sum(r[2] for r in results)}")
        print(
            f"   • Date range analyzed: {cutoff_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
        )
        print(f"   • Total from volume (USD): ${total_from_usd:,.0f}")
        print(f"   • Total to volume (USD): ${total_to_usd:,.0f}")

        # Asset popularity analysis
        print(f"\n🪙 Most Active Assets:")
        asset_stats = {}
        for from_asset, to_asset, trade_count, _, _, _, _ in results:
            asset_stats[from_asset] = asset_stats.get(from_asset, 0) + trade_count
            asset_stats[to_asset] = asset_stats.get(to_asset, 0) + trade_count

        # Sort assets by total activity
        sorted_assets = sorted(asset_stats.items(), key=lambda x: x[1], reverse=True)
        for asset, count in sorted_assets[:5]:
            print(f"   • {asset}: {count} trades")

    except Exception as e:
        print(f"❌ Error querying database: {e}")

    finally:
        conn.close()


def get_full_date_range():
    """Get the full date range covered by the entire dataset"""

    db_path = Path(__file__).parent.parent / "databases" / "thorchain_consolidated.db"

    if not db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get the full date range of the dataset
        cursor.execute(
            """
            SELECT 
                MIN(timestamp) as earliest_trade,
                MAX(timestamp) as latest_trade,
                COUNT(*) as total_transactions
            FROM thorchain_transactions 
            WHERE timestamp IS NOT NULL
        """
        )

        result = cursor.fetchone()
        if result:
            earliest, latest, total = result
            print(f"\n📅 Full Dataset Coverage:")
            print(f"   • Earliest transaction: {earliest}")
            print(f"   • Latest transaction: {latest}")
            print(f"   • Total transactions in database: {total:,}")

            # Calculate date range
            if earliest and latest:
                try:
                    # Parse the timestamp format
                    if earliest.startswith("Time"):
                        earliest = earliest.replace("Time", "").strip()
                    if latest.startswith("Time"):
                        latest = latest.replace("Time", "").strip()

                    # Try to parse dates
                    date_formats = [
                        "%b %d %Y %I:%M:%S %p (GMT-7)",
                        "%b %d %Y %I:%M:%S %p (GMT-8)",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                    ]

                    earliest_date = None
                    latest_date = None

                    for fmt in date_formats:
                        try:
                            earliest_date = datetime.strptime(earliest, fmt)
                            break
                        except ValueError:
                            continue

                    for fmt in date_formats:
                        try:
                            latest_date = datetime.strptime(latest, fmt)
                            break
                        except ValueError:
                            continue

                    if earliest_date and latest_date:
                        date_diff = (latest_date - earliest_date).days
                        print(f"   • Date span: {date_diff} days")
                        print(
                            f"   • Coverage period: {earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}"
                        )
                except Exception as e:
                    print(f"   • Date parsing error: {e}")

    except Exception as e:
        print(f"❌ Error getting full date range: {e}")

    finally:
        conn.close()


def get_recent_trading_activity(days=30):
    """Get recent trading activity summary"""

    db_path = Path(__file__).parent.parent / "databases" / "thorchain_consolidated.db"

    if not db_path.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=days)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get total trading activity in last N days
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_trades,
                COUNT(DISTINCT from_asset) as unique_from_assets,
                COUNT(DISTINCT to_asset) as unique_to_assets,
                COUNT(DISTINCT from_address) as unique_traders
            FROM thorchain_transactions 
            WHERE timestamp >= ?
                AND status = 'Success'
        """,
            (cutoff_date.strftime("%b %d %Y"),),
        )

        result = cursor.fetchone()
        if result:
            total_trades, unique_from, unique_to, unique_traders = result
            print(f"\n📈 Recent Trading Activity ({days} days):")
            print(f"   • Total successful trades: {total_trades:,}")
            print(f"   • Unique source assets: {unique_from}")
            print(f"   • Unique destination assets: {unique_to}")
            print(f"   • Unique trader addresses: {unique_traders}")

    except Exception as e:
        print(f"❌ Error getting recent activity: {e}")

    finally:
        conn.close()


def main():
    """Main function"""
    print("🚀 THORChain Trading Pair Analysis")
    print("=" * 50)

    # Get full dataset coverage first
    get_full_date_range()

    # Get top trading pairs
    get_top_trading_pairs(30)

    # Get recent activity summary
    get_recent_trading_activity(30)

    print(
        f"\n💡 To analyze different time periods, modify the days parameter in the script."
    )
    print(f"   Current analysis: Last 30 days")
    print(f"\n⚠️  Note: USD values are approximate using simplified pricing data.")
    print(f"   For accurate USD values, integrate with real-time price APIs.")


if __name__ == "__main__":
    main()
