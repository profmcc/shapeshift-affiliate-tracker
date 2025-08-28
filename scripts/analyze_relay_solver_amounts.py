#!/usr/bin/env python3
"""
Analyze Relay Global Solver Amounts for ShapeShift Transactions
Extracts the actual global solver amounts that were paid to ShapeShift.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RelaySolverAnalyzer:
    def __init__(self):
        self.db_path = "databases/affiliate.db"
        self.shapeshift_affiliate = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

    def analyze_solver_amounts(self):
        """Analyze the actual global solver amounts for ShapeShift transactions"""
        print("🔍 Analyzing Relay Global Solver Amounts for ShapeShift...")

        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all Relay transactions
        cursor.execute(
            """
            SELECT tx_hash, log_index, chain, block_number, timestamp, 
                   event_type, affiliate_address, amount, token_address, 
                   solver_call_data, token_address_name
            FROM relay_affiliate_fees_conservative 
            WHERE event_type = 'ActualClaimed'  -- Focus on main solver events
            ORDER BY timestamp DESC
        """
        )

        transactions = cursor.fetchall()
        conn.close()

        print(f"📊 Found {len(transactions)} Relay ActualClaimed events")

        # Group by transaction hash to find unique transactions
        tx_groups = {}
        for tx in transactions:
            tx_hash = tx[0]
            if tx_hash not in tx_groups:
                tx_groups[tx_hash] = []
            tx_groups[tx_hash].append(tx)

        print(f"📊 Found {len(tx_groups)} unique SolverCallExecuted transactions")

        # Analyze the actual global solver amounts
        global_solver_amounts = []
        shapehift_global_amounts = []

        for tx_hash, tx_list in tx_groups.items():
            # Check if this involves ShapeShift
            involves_shapehift = any(
                tx[6].lower() == self.shapeshift_affiliate.lower() for tx in tx_list
            )

            if involves_shapehift:
                # Get the global solver amount (the main amount field)
                for tx in tx_list:
                    amount_str = tx[7]  # amount field
                    try:
                        amount_int = int(amount_str)
                        amount_eth = amount_int / 1e18

                        if amount_eth > 0:
                            global_solver_amounts.append(
                                {
                                    "tx_hash": tx_hash,
                                    "amount_wei": amount_int,
                                    "amount_eth": amount_eth,
                                    "amount_usd": amount_eth * 3500,
                                    "event_type": tx[5],
                                    "timestamp": tx[4],
                                    "chain": tx[2],
                                    "block_number": tx[3],
                                }
                            )

                            shapehift_global_amounts.append(
                                {
                                    "tx_hash": tx_hash,
                                    "amount_eth": amount_eth,
                                    "amount_usd": amount_eth * 3500,
                                    "timestamp": tx[4],
                                    "chain": tx[2],
                                }
                            )
                    except (ValueError, TypeError):
                        continue

        # Calculate totals
        total_eth = sum(tx["amount_eth"] for tx in global_solver_amounts)
        total_usd = sum(tx["amount_usd"] for tx in global_solver_amounts)

        print(f"\n📊 RELAY GLOBAL SOLVER AMOUNT ANALYSIS")
        print(f"=" * 60)
        print(f"ShapeShift Global Solver Transactions: {len(shapehift_global_amounts)}")
        print(f"Total Global Solver Amount: {total_eth:.6f} ETH")
        print(f"Total Global Solver Amount: ${total_usd:,.2f}")

        # Show breakdown by chain
        chain_totals = {}
        for tx in global_solver_amounts:
            chain = tx["chain"]
            if chain not in chain_totals:
                chain_totals[chain] = {"count": 0, "eth": 0, "usd": 0}
            chain_totals[chain]["count"] += 1
            chain_totals[chain]["eth"] += tx["amount_eth"]
            chain_totals[chain]["usd"] += tx["amount_usd"]

        print(f"\n📊 BREAKDOWN BY CHAIN:")
        for chain, totals in chain_totals.items():
            print(
                f"   {chain}: {totals['count']} txs, {totals['eth']:.6f} ETH (${totals['usd']:,.2f})"
            )

        # Show top transactions
        print(f"\n🏆 TOP 10 GLOBAL SOLVER TRANSACTIONS:")
        sorted_txs = sorted(
            global_solver_amounts, key=lambda x: x["amount_eth"], reverse=True
        )
        for i, tx in enumerate(sorted_txs[:10], 1):
            print(
                f"{i:2d}. {tx['amount_eth']:.6f} ETH (${tx['amount_usd']:,.2f}) - {tx['tx_hash'][:16]}..."
            )

        # Calculate July 2025 amounts
        july_start = int(datetime(2025, 7, 1).timestamp())
        july_end = int(datetime(2025, 7, 31).timestamp())

        july_transactions = [
            tx
            for tx in shapehift_global_amounts
            if july_start <= tx["timestamp"] <= july_end
        ]
        july_total_eth = sum(tx["amount_eth"] for tx in july_transactions)
        july_total_usd = sum(tx["amount_usd"] for tx in july_transactions)

        print(f"\n📊 JULY 2025 GLOBAL SOLVER ANALYSIS:")
        print(f"   July Global Solver Transactions: {len(july_transactions)}")
        print(f"   July Total Global Amount: {july_total_eth:.6f} ETH")
        print(f"   July Total Global Amount: ${july_total_usd:,.2f}")

        # Compare with current analysis
        print(f"\n📊 COMPARISON WITH CURRENT ANALYSIS:")
        print(
            f"   Actual Global Solver Amounts: {july_total_eth:.6f} ETH (${july_total_usd:,.2f})"
        )
        print(f"   Current Conservative Estimate: 3.787 ETH ($13,255)")
        print(f"   Difference: {july_total_eth - 3.787:.6f} ETH")

        # Save detailed results
        results = {
            "analysis_date": datetime.now().isoformat(),
            "total_global_solver_transactions": len(shapehift_global_amounts),
            "total_global_amount_eth": total_eth,
            "total_global_amount_usd": total_usd,
            "july_global_transactions": len(july_transactions),
            "july_global_amount_eth": july_total_eth,
            "july_global_amount_usd": july_total_usd,
            "chain_breakdown": chain_totals,
            "top_transactions": sorted_txs[:20],
            "all_global_transactions": shapehift_global_amounts,
        }

        with open("relay_global_solver_analysis.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✅ Analysis saved to: relay_global_solver_analysis.json")

        # Final analysis using direct SQL query
        print(f"\n🔍 FINAL ANALYSIS - DIRECT DATABASE QUERY:")
        print(f"=" * 60)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get total amount from GlobalSolverInvolvement events
        cursor.execute(
            """
            SELECT SUM(CAST(amount AS REAL)) 
            FROM relay_affiliate_fees 
            WHERE amount != '0' AND event_type = 'GlobalSolverInvolvement'
        """
        )

        total_wei = cursor.fetchone()[0] or 0
        total_eth_actual = total_wei / 1e18
        total_usd_actual = total_eth_actual * 3500

        print(f"Total Global Solver Amount (wei): {total_wei}")
        print(f"Total Global Solver Amount (ETH): {total_eth_actual:.6f} ETH")
        print(f"Total Global Solver Amount (USD): ${total_usd_actual:,.2f}")

        # Get count of transactions
        cursor.execute(
            """
            SELECT COUNT(DISTINCT tx_hash) 
            FROM relay_affiliate_fees 
            WHERE event_type = 'GlobalSolverInvolvement'
        """
        )

        tx_count = cursor.fetchone()[0] or 0
        print(f"Total Global Solver Transactions: {tx_count}")

        # Get July 2025 amounts
        july_start_ts = int(datetime(2025, 7, 1).timestamp())
        july_end_ts = int(datetime(2025, 7, 31).timestamp())

        cursor.execute(
            """
            SELECT SUM(CAST(amount AS REAL)) 
            FROM relay_affiliate_fees 
            WHERE amount != '0' 
            AND event_type = 'GlobalSolverInvolvement'
            AND timestamp >= ? AND timestamp <= ?
        """,
            (july_start_ts, july_end_ts),
        )

        july_wei = cursor.fetchone()[0] or 0
        july_eth_actual = july_wei / 1e18
        july_usd_actual = july_eth_actual * 3500

        print(f"\n📊 JULY 2025 ACTUAL GLOBAL SOLVER AMOUNTS:")
        print(f"July Global Solver Amount (wei): {july_wei}")
        print(f"July Global Solver Amount (ETH): {july_eth_actual:.6f} ETH")
        print(f"July Global Solver Amount (USD): ${july_usd_actual:,.2f}")

        # Compare with current analysis
        print(f"\n📊 COMPARISON WITH CURRENT ANALYSIS:")
        print(
            f"   Actual Global Solver Amounts: {july_eth_actual:.6f} ETH (${july_usd_actual:,.2f})"
        )
        print(f"   Current Conservative Estimate: 3.787 ETH ($13,255)")
        print(f"   Difference: {july_eth_actual - 3.787:.6f} ETH")

        conn.close()

        return results


def main():
    analyzer = RelaySolverAnalyzer()
    analyzer.analyze_solver_amounts()


if __name__ == "__main__":
    main()
