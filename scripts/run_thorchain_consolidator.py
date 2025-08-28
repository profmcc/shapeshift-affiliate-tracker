#!/usr/bin/env python3
"""
Simple wrapper to run the THORChain Data Consolidator
"""

import sys
import os

# Add the scripts directory to the path so we can import the consolidator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from thorchain_data_consolidator_fixed import THORChainDataConsolidator


def main():
    """Run the consolidator with default settings"""

    # Default paths
    downloads_dir = "/Users/chrismccarthy/Downloads"
    database_dir = "databases"

    print("🚀 THORChain Data Consolidator")
    print("=" * 50)
    print(f"📁 Downloads directory: {downloads_dir}")
    print(f"💾 Database directory: {database_dir}")
    print("=" * 50)

    # Initialize and run consolidator
    consolidator = THORChainDataConsolidator(downloads_dir, database_dir)

    # Run consolidation
    print("\n🔄 Starting consolidation...")
    results = consolidator.consolidate_all_files()

    # Show results
    print(f"\n✅ Consolidation complete!")
    print(f"📊 Files processed: {results.get('files_processed', 0)}")
    print(f"📈 New transactions: {results.get('transactions_inserted', 0)}")
    print(f"⏭️ Skipped (duplicates): {results.get('transactions_skipped', 0)}")

    # Show final database statistics
    consolidator.print_database_stats()


if __name__ == "__main__":
    main()
