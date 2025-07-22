#!/usr/bin/env python3
"""
Check exact THORChain API response structure
"""

import requests
import json

SPECIFIC_TX = 'F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A'

def check_api_response():
    """Check the exact API response structure"""
    print(f"🔍 Checking THORChain API Response Structure")
    print("=" * 60)
    
    try:
        url = f"https://midgard.ninerealms.com/v2/actions?txid={SPECIFIC_TX}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API Response received")
        print(f"Response keys: {list(data.keys())}")
        
        actions = data.get('actions', [])
        print(f"Number of actions: {len(actions)}")
        
        if actions:
            action = actions[0]
            print(f"\n📋 First Action Structure:")
            print(f"Action keys: {list(action.keys())}")
            
            # Print all top-level fields
            for key, value in action.items():
                if isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                        if value and isinstance(value[0], dict):
                            print(f"    First item keys: {list(value[0].keys())}")
                    else:
                        print(f"  {key}: dict with keys {list(value.keys())}")
                else:
                    print(f"  {key}: {value}")
            
            # Check if we can find the transaction ID anywhere
            print(f"\n🔍 Looking for Transaction ID...")
            
            def find_tx_id(obj, path=""):
                results = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if SPECIFIC_TX in str(value):
                            results.append((current_path, value))
                        if isinstance(value, (dict, list)):
                            results.extend(find_tx_id(value, current_path))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]"
                        results.extend(find_tx_id(item, current_path))
                return results
            
            tx_id_locations = find_tx_id(action)
            if tx_id_locations:
                print(f"Found transaction ID at:")
                for path, value in tx_id_locations:
                    print(f"  📍 {path}: {value}")
            else:
                print(f"❌ Transaction ID not found in response")
                
                # Let's check the 'in' transactions
                in_txs = action.get('in', [])
                if in_txs:
                    print(f"\nChecking 'in' transactions:")
                    for i, in_tx in enumerate(in_txs):
                        print(f"  In TX {i}: {list(in_tx.keys())}")
                        if 'txID' in in_tx:
                            print(f"    txID: {in_tx['txID']}")
        
        else:
            print(f"❌ No actions found")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    check_api_response()

if __name__ == "__main__":
    main() 