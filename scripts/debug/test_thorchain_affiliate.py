#!/usr/bin/env python3
"""
Test THORChain Affiliate Data Collection
Verifies that we can fetch affiliate fee data from THORChain
Tests both address and affiliate name approaches
"""

import requests
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# THORChain Midgard API
MIDGARD_URL = "https://midgard.ninerealms.com"

def test_thorchain_affiliate_address():
    """Test THORChain affiliate data using address approach"""
    print("=== TESTING THORCHAIN AFFILIATE (ADDRESS) ===")
    
    # Test different affiliate addresses
    test_addresses = [
        "thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p",  # Original address
        "ss",  # Affiliate name
        "thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p",  # Full address
    ]
    
    results = {}
    
    for address in test_addresses:
        print(f"\n--- Testing address: {address} ---")
        
        try:
            # Fetch actions from Midgard
            url = f"{MIDGARD_URL}/v2/actions"
            params = {
                'limit': 100,
                'offset': 0
            }
            
            print(f"Fetching from: {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            actions = data.get('actions', [])
            
            print(f"Total actions fetched: {len(actions)}")
            
            # Filter for swap actions with our affiliate
            affiliate_swaps = []
            for action in actions:
                if action.get('type') == 'swap':
                    swap = action.get('metadata', {}).get('swap', {})
                    affiliate_address = swap.get('affiliateAddress')
                    
                    if affiliate_address == address:
                        affiliate_swaps.append({
                            'tx_hash': action.get('txID', ''),
                            'from_asset': swap.get('from', {}).get('asset', ''),
                            'to_asset': swap.get('to', {}).get('asset', ''),
                            'from_amount': float(swap.get('from', {}).get('amount', 0)) / 1e8,
                            'to_amount': float(swap.get('to', {}).get('amount', 0)) / 1e8,
                            'affiliate_fee': float(swap.get('affiliateFee', {}).get('amount', 0)) / 1e8,
                            'affiliate_fee_asset': swap.get('affiliateFee', {}).get('asset', ''),
                            'timestamp': action.get('date', 0),
                            'status': action.get('status', '')
                        })
            
            results[address] = affiliate_swaps
            print(f"✅ Found {len(affiliate_swaps)} affiliate swaps for {address}")
            
            if affiliate_swaps:
                print("Sample swaps:")
                for i, swap in enumerate(affiliate_swaps[:3]):
                    print(f"  {i+1}. {swap['from_asset']} -> {swap['to_asset']}, Fee: {swap['affiliate_fee']} {swap['affiliate_fee_asset']}")
            
        except Exception as e:
            print(f"❌ Error testing address {address}: {e}")
            results[address] = []
    
    return results

def test_thorchain_viewblock_api():
    """Test THORChain data using ViewBlock API approach"""
    print("\n=== TESTING THORCHAIN VIEWBLOCK API ===")
    
    try:
        # Try to fetch from ViewBlock API (if available)
        viewblock_url = "https://api.viewblock.io/thorchain/txs"
        params = {
            'affiliate': 'ss'
        }
        
        print(f"Fetching from ViewBlock: {viewblock_url}")
        response = requests.get(viewblock_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ViewBlock API response: {len(data) if isinstance(data, list) else 'object'}")
            return data
        else:
            print(f"⚠️ ViewBlock API returned status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing ViewBlock API: {e}")
        return None

def save_test_results(results: Dict, viewblock_data: Optional[List]):
    """Save test results to database"""
    print("\n=== SAVING TEST RESULTS ===")
    
    conn = sqlite3.connect('test_thorchain.db')
    cursor = conn.cursor()
    
    # Create test table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_thorchain_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_type TEXT,
            affiliate_address TEXT,
            tx_hash TEXT,
            from_asset TEXT,
            to_asset TEXT,
            from_amount REAL,
            to_amount REAL,
            affiliate_fee REAL,
            affiliate_fee_asset TEXT,
            timestamp INTEGER,
            status TEXT,
            created_at INTEGER
        )
    ''')
    
    total_saved = 0
    
    # Save Midgard results
    for address, swaps in results.items():
        for swap in swaps:
            cursor.execute('''
                INSERT INTO test_thorchain_fees 
                (test_type, affiliate_address, tx_hash, from_asset, to_asset, 
                 from_amount, to_amount, affiliate_fee, affiliate_fee_asset, 
                 timestamp, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'midgard',
                address,
                swap['tx_hash'],
                swap['from_asset'],
                swap['to_asset'],
                swap['from_amount'],
                swap['to_amount'],
                swap['affiliate_fee'],
                swap['affiliate_fee_asset'],
                swap['timestamp'],
                swap['status'],
                int(datetime.now().timestamp())
            ))
            total_saved += 1
    
    # Save ViewBlock results if available
    if viewblock_data:
        for tx in viewblock_data[:10]:  # Limit to first 10
            cursor.execute('''
                INSERT INTO test_thorchain_fees 
                (test_type, affiliate_address, tx_hash, from_asset, to_asset, 
                 from_amount, to_amount, affiliate_fee, affiliate_fee_asset, 
                 timestamp, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'viewblock',
                'ss',
                tx.get('hash', ''),
                tx.get('fromAsset', ''),
                tx.get('toAsset', ''),
                tx.get('fromAmount', 0),
                tx.get('toAmount', 0),
                tx.get('affiliateFee', 0),
                tx.get('affiliateFeeAsset', ''),
                tx.get('timestamp', 0),
                tx.get('status', ''),
                int(datetime.now().timestamp())
            ))
            total_saved += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Saved {total_saved} test records to database")
    return total_saved

def main():
    """Run all THORChain tests"""
    print("=== THORCHAIN AFFILIATE TESTING ===")
    
    # Test Midgard API with different addresses
    midgard_results = test_thorchain_affiliate_address()
    
    # Test ViewBlock API
    viewblock_data = test_thorchain_viewblock_api()
    
    # Save results
    total_saved = save_test_results(midgard_results, viewblock_data)
    
    # Summary
    print(f"\n=== TEST SUMMARY ===")
    for address, swaps in midgard_results.items():
        print(f"Address '{address}': {len(swaps)} swaps found")
    
    if viewblock_data:
        print(f"ViewBlock API: {len(viewblock_data)} transactions found")
    
    print(f"Total records saved: {total_saved}")
    
    return total_saved

if __name__ == "__main__":
    result = main()
    print(f"\n=== THORCHAIN TEST COMPLETE: {result} total records ===") 