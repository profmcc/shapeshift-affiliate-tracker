#!/usr/bin/env python3
"""
Check Broker Volumes Script

This script checks the actual volumes shown on each broker page to understand
the discrepancy between what's displayed and what's in our database.
"""

import asyncio
import sys
from datetime import datetime
from chainflip_comprehensive_scraper import ChainflipComprehensiveScraper


# Known ShapeShift affiliate broker addresses
BROKER_URLS = [
    "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
    "https://scan.chainflip.io/brokers/cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8"
]

# Broker address mappings (extract from URLs)
BROKER_ADDRESSES = {
    "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi": "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",
    "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8": "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8"
}


async def check_broker_volume(broker_url: str):
    """Check the volume and transaction count for a specific broker."""
    broker_address = BROKER_ADDRESSES[broker_url.split('/')[-1]]
    
    print(f"\n🔍 Checking broker: {broker_address}")
    print(f"   URL: {broker_url}")
    
    try:
        # Create scraper for this broker
        scraper = ChainflipComprehensiveScraper(broker_url)
        
        # Scrape data
        scraped_data = await scraper.scrape_with_full_addresses()
        
        if not scraped_data:
            print(f"   ❌ No data scraped for {broker_address}")
            return None
        
        # Calculate totals
        total_transactions = 0
        total_volume = 0.0
        transaction_ids = []
        
        for row in scraped_data:
            # Check if this is a table row (has cell_0, cell_1, etc.)
            if 'cell_0' in row and 'cell_1' in row:
                cell_0_content = row.get('cell_0', '').strip()
                
                # Extract transaction ID (first line starting with #)
                lines = cell_0_content.split('\n')
                transaction_id = None
                usd_amount = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('#'):
                        # Extract transaction ID
                        transaction_id = line.split()[0].replace('#', '')
                    elif line.startswith('$') and ',' in line:
                        # Extract USD amount (look for lines like "$1,799.80")
                        try:
                            amount_clean = line.replace('$', '').replace(',', '')
                            usd_amount = float(amount_clean)
                            break  # Use the first USD amount found
                        except (ValueError, AttributeError):
                            continue
                
                if transaction_id and usd_amount:
                    total_transactions += 1
                    total_volume += usd_amount
                    transaction_ids.append(transaction_id)
        
        print(f"   📊 Results for {broker_address}:")
        print(f"      Total Transactions: {total_transactions:,}")
        print(f"      Total Volume: ${total_volume:,.2f}")
        print(f"      Transaction ID Range: {min(transaction_ids) if transaction_ids else 'N/A'} to {max(transaction_ids) if transaction_ids else 'N/A'}")
        
        return {
            'broker': broker_address,
            'transactions': total_transactions,
            'volume': total_volume,
            'min_id': min(transaction_ids) if transaction_ids else None,
            'max_id': max(transaction_ids) if transaction_ids else None
        }
        
    except Exception as e:
        print(f"   ❌ Error checking {broker_address}: {e}")
        return None


async def main():
    """Main function to check broker volumes."""
    print(f"🔍 Checking Broker Volumes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        results = []
        
        for broker_url in BROKER_URLS:
            result = await check_broker_volume(broker_url)
            if result:
                results.append(result)
        
        # Show summary
        print(f"\n🎯 SUMMARY:")
        total_volume = sum(r['volume'] for r in results)
        total_transactions = sum(r['transactions'] for r in results)
        
        print(f"   Combined Volume: ${total_volume:,.2f}")
        print(f"   Combined Transactions: {total_transactions:,}")
        
        for result in results:
            print(f"   {result['broker']}: ${result['volume']:,.2f} ({result['transactions']:,} transactions)")
        
        print(f"\n✅ Volume check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during volume check: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 