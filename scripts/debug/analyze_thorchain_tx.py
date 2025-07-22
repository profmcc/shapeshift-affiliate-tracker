#!/usr/bin/env python3
"""
Analyze Specific THORChain Transaction
Analyze the specific transaction: F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A
"""

import requests
import json
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
THORCHAIN_MIDGARD_URL = 'https://midgard.ninerealms.com'
SPECIFIC_TX = 'F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A'

def fetch_specific_transaction(tx_id: str) -> Optional[Dict]:
    """Fetch a specific THORChain transaction"""
    logger.info(f"Fetching THORChain transaction: {tx_id}")
    
    try:
        # Try different endpoints to find the transaction
        endpoints = [
            f"{THORCHAIN_MIDGARD_URL}/v2/actions?txid={tx_id}",
            f"{THORCHAIN_MIDGARD_URL}/v2/transactions/{tx_id}",
            f"{THORCHAIN_MIDGARD_URL}/v2/tx/{tx_id}"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched transaction from: {endpoint}")
                    return data
                else:
                    logger.warning(f"Endpoint {endpoint} returned status: {response.status_code}")
            except Exception as e:
                logger.warning(f"Failed to fetch from {endpoint}: {e}")
        
        logger.error("Failed to fetch transaction from any endpoint")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching transaction: {e}")
        return None

def analyze_transaction_structure(data: Dict):
    """Analyze the structure of a transaction"""
    print(f"\n🔍 Transaction Structure Analysis")
    print("=" * 50)
    
    def print_nested_structure(obj, indent=0):
        spaces = "  " * indent
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    print(f"{spaces}{key}: {type(value).__name__}")
                    if isinstance(value, dict) and len(value) > 0:
                        print_nested_structure(value, indent + 1)
                    elif isinstance(value, list) and len(value) > 0:
                        print(f"{spaces}  [{len(value)} items]")
                        if len(value) > 0:
                            print_nested_structure(value[0], indent + 2)
                else:
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    print(f"{spaces}{key}: {str_value}")
        elif isinstance(obj, list):
            print(f"{spaces}List with {len(obj)} items")
            if len(obj) > 0:
                print_nested_structure(obj[0], indent + 1)
    
    print_nested_structure(data)

def search_for_affiliate_data(data: Dict):
    """Search for affiliate-related data in the transaction"""
    print(f"\n🎯 Searching for Affiliate Data")
    print("=" * 50)
    
    def search_recursive(obj, path=""):
        results = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look for affiliate-related keys
                if any(word in key.lower() for word in ['affiliate', 'ss', 'partner', 'fee']):
                    results.append((current_path, key, value))
                
                # Check string values for 'ss'
                if isinstance(value, str) and value == 'ss':
                    results.append((current_path, key, value))
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    results.extend(search_recursive(value, current_path))
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                results.extend(search_recursive(item, current_path))
        
        return results
    
    affiliate_data = search_recursive(data)
    
    if affiliate_data:
        print("Found affiliate-related data:")
        for path, key, value in affiliate_data:
            print(f"  📍 {path}")
            print(f"     Key: {key}")
            print(f"     Value: {value}")
            print()
    else:
        print("❌ No affiliate data found")

def fetch_recent_actions_sample():
    """Fetch a sample of recent actions to understand the data structure"""
    logger.info("Fetching sample of recent THORChain actions...")
    
    try:
        url = f"{THORCHAIN_MIDGARD_URL}/v2/actions"
        params = {
            'limit': 10,
            'offset': 0
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        print(f"\n📊 Sample Actions Analysis ({len(actions)} actions)")
        print("=" * 50)
        
        for i, action in enumerate(actions[:3]):  # Analyze first 3 actions
            print(f"\n--- Action {i+1} ---")
            print(f"Type: {action.get('type', 'Unknown')}")
            print(f"Status: {action.get('status', 'Unknown')}")
            print(f"TX ID: {action.get('txID', 'Unknown')}")
            
            # Check for affiliate data in this action
            search_for_affiliate_data(action)
        
        return actions
        
    except Exception as e:
        logger.error(f"Error fetching sample actions: {e}")
        return []

def main():
    """Main function to analyze THORChain transaction structure"""
    print("🔍 THORChain Transaction Analysis")
    print("=" * 60)
    
    # Try to fetch the specific transaction
    tx_data = fetch_specific_transaction(SPECIFIC_TX)
    
    if tx_data:
        print(f"\n✅ Successfully fetched transaction: {SPECIFIC_TX}")
        analyze_transaction_structure(tx_data)
        search_for_affiliate_data(tx_data)
    else:
        print(f"\n❌ Could not fetch specific transaction: {SPECIFIC_TX}")
    
    # Fetch sample actions to understand the general structure
    sample_actions = fetch_recent_actions_sample()
    
    print(f"\n💡 Next Steps:")
    print("1. Check if the specific transaction has affiliate data")
    print("2. Understand the correct API endpoints for affiliate data")
    print("3. Identify the correct field names for ShapeShift affiliate fees")

if __name__ == "__main__":
    main() 