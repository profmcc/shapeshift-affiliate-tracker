#!/usr/bin/env python3
"""
Test script to process specific blocks with known Portals transactions
"""

from portals_listener import CSVPortalsListener

def test_specific_blocks():
    """Test the portals listener with blocks that have known Portals transactions"""
    
    print("🧪 Testing Portals Listener with Known Transactions")
    print("==================================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    # Test specific block ranges with known Portals transactions
    test_cases = [
        {
            "name": "Block 22774492 (Known Portals)",
            "chain": "ethereum",
            "start_block": 22774490,
            "end_block": 22774500
        },
        {
            "name": "Block 23230059 (Known Portals)",
            "chain": "ethereum", 
            "start_block": 23230050,
            "end_block": 23230070
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Chain: {test_case['chain']}")
        print(f"   Blocks: {test_case['start_block']} to {test_case['end_block']}")
        
        try:
            # Get events from the specific block range
            events = listener.fetch_portals_events(
                test_case['chain'],
                test_case['start_block'],
                test_case['end_block']
            )
            
            print(f"   📋 Found {len(events)} Portals events")
            
            if events:
                for i, event in enumerate(events):
                    print(f"   Event {i+1}:")
                    print(f"     Tx Hash: {event['tx_hash']}")
                    print(f"     Block: {event['block_number']}")
                    print(f"     Chain: {event['chain']}")
                    print(f"     From: {event['from_address']}")
                    print(f"     To: {event['to_address']}")
                    print(f"     Token: {event['token_symbol']} ({event['token_address']})")
                    print(f"     Amount: {event['amount']}")
                    print(f"     Affiliate Fee: {event['affiliate_fee']}")
                    print()
            else:
                print("   ℹ️ No events found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test CSV file creation
    print("\n📊 Testing CSV File Creation")
    print("============================")
    
    try:
        # Create some sample events
        sample_events = [
            {
                "tx_hash": "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
                "block_number": 22774492,
                "timestamp": 0,
                "chain": "ethereum",
                "from_address": "0x36159d2343b992552263Bfbcd9185cD04098Ac69",
                "to_address": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
                "token_address": "0xA0b86a33E6441b8c4C8C1C1e0F5B3e4C8C1C1e0F5",
                "token_symbol": "USDC",
                "amount": 1000000,
                "amount_usd": 1000.0,
                "affiliate_address": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
                "affiliate_fee": 10000,
                "affiliate_fee_usd": 10.0,
                "bridge_type": "portals",
                "source_chain": "ethereum",
                "destination_chain": "polygon",
                "processed_at": "2025-08-28T09:15:00"
            }
        ]
        
        # Save to CSV
        listener.save_transactions_to_csv(sample_events)
        
        print("✅ Sample events saved to CSV")
        
        # Check CSV content
        import os
        csv_file = os.path.join(listener.csv_dir, "portals_transactions.csv")
        if os.path.exists(csv_file):
            with open(csv_file, 'r') as f:
                lines = f.readlines()
                print(f"📁 CSV file has {len(lines)} lines")
                if len(lines) > 1:
                    print("📋 First data row:")
                    print(f"   {lines[1].strip()}")
        
    except Exception as e:
        print(f"❌ Error testing CSV: {e}")
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    test_specific_blocks()
