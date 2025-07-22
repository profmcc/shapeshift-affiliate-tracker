#!/usr/bin/env python3
"""
Debug THORChain Timestamp Format
The successful transaction had: date: 1752028334620703867
"""

import requests
from datetime import datetime

# The timestamp from the successful ShapeShift transaction
THORCHAIN_TIMESTAMP = 1752028334620703867
SPECIFIC_TX = 'F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A'

def analyze_timestamp_format():
    """Analyze the THORChain timestamp format"""
    print(f"🕐 Analyzing THORChain Timestamp: {THORCHAIN_TIMESTAMP}")
    print("=" * 60)
    
    # Try different timestamp interpretations
    timestamp_formats = [
        ("Unix seconds", THORCHAIN_TIMESTAMP),
        ("Unix milliseconds", THORCHAIN_TIMESTAMP / 1000),
        ("Unix microseconds", THORCHAIN_TIMESTAMP / 1000000),
        ("Unix nanoseconds", THORCHAIN_TIMESTAMP / 1000000000),
        ("THORChain block time", THORCHAIN_TIMESTAMP / 1000000000),
    ]
    
    for format_name, timestamp_value in timestamp_formats:
        try:
            if timestamp_value > 0 and timestamp_value < 2147483647:  # Valid Unix timestamp range
                date_str = datetime.fromtimestamp(timestamp_value).isoformat()
                print(f"{format_name:20}: {timestamp_value:15.0f} -> {date_str}")
            else:
                print(f"{format_name:20}: {timestamp_value:15.0f} -> Out of range")
        except Exception as e:
            print(f"{format_name:20}: {timestamp_value:15.0f} -> Error: {e}")

def fetch_recent_actions_with_timestamps():
    """Fetch recent actions and analyze their timestamps"""
    print(f"\n📊 Analyzing Recent Action Timestamps")
    print("=" * 60)
    
    try:
        url = "https://midgard.ninerealms.com/v2/actions"
        params = {'limit': 5, 'type': 'swap'}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        for i, action in enumerate(actions):
            tx_id = action.get('txID', 'Unknown')[:20]
            date_raw = action.get('date', 0)
            status = action.get('status', 'Unknown')
            
            print(f"\nAction {i+1}: {tx_id}...")
            print(f"  Status: {status}")
            print(f"  Raw date: {date_raw}")
            
            # Try to convert timestamp
            if date_raw:
                # THORChain uses nanoseconds since Unix epoch
                timestamp_seconds = int(date_raw) / 1000000000
                try:
                    date_str = datetime.fromtimestamp(timestamp_seconds).isoformat()
                    print(f"  Converted: {date_str}")
                except:
                    print(f"  Conversion failed")
            
            # Check for affiliate data
            metadata = action.get('metadata', {})
            swap = metadata.get('swap', {})
            affiliate_addr = swap.get('affiliateAddress', '')
            affiliate_fee = swap.get('affiliateFee', 0)
            
            if affiliate_addr:
                print(f"  🎯 Affiliate: {affiliate_addr} (fee: {affiliate_fee})")
            
    except Exception as e:
        print(f"Error fetching actions: {e}")

def test_specific_transaction():
    """Test the specific ShapeShift transaction we know works"""
    print(f"\n🔍 Testing Specific ShapeShift Transaction")
    print("=" * 60)
    
    try:
        url = f"https://midgard.ninerealms.com/v2/actions?txid={SPECIFIC_TX}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        if actions:
            action = actions[0]
            print(f"✅ Found transaction: {SPECIFIC_TX}")
            
            # Check all the key fields
            date_raw = action.get('date', 0)
            status = action.get('status', '')
            
            print(f"Status: {status}")
            print(f"Raw timestamp: {date_raw}")
            
            # Convert timestamp properly
            timestamp_seconds = int(date_raw) / 1000000000
            date_str = datetime.fromtimestamp(timestamp_seconds).isoformat()
            print(f"Converted date: {date_str}")
            
            # Check affiliate data
            metadata = action.get('metadata', {})
            swap = metadata.get('swap', {})
            
            affiliate_addr = swap.get('affiliateAddress', '')
            affiliate_fee = swap.get('affiliateFee', 0)
            
            print(f"Affiliate address: '{affiliate_addr}'")
            print(f"Affiliate fee: {affiliate_fee}")
            print(f"Is ShapeShift: {affiliate_addr == 'ss'}")
            print(f"Has fee: {affiliate_fee > 0}")
            
        else:
            print(f"❌ Transaction not found")
    
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("🐛 THORChain Timestamp Debug Tool")
    print("=" * 60)
    
    analyze_timestamp_format()
    fetch_recent_actions_with_timestamps()
    test_specific_transaction()

if __name__ == "__main__":
    main() 