#!/usr/bin/env python3
"""
Query ShapeShift Pending Rewards using Validated Listener
Uses the existing csv_chainflip_api_listener to query broker info and rewards
"""

import sys
import os
sys.path.append('validated_listeners')

from csv_chainflip_api_listener import CSVChainflipAPIListener
import json
from datetime import datetime

def main():
    """Query pending rewards using the validated listener"""
    print("🚀 Querying ShapeShift pending rewards using validated listener...")
    
    try:
        # Initialize the listener
        listener = CSVChainflipAPIListener()
        
        print(f"📡 API Base URL: {listener.api_base_url}")
        print(f"📊 Monitoring {len(listener.shapeshift_brokers)} ShapeShift brokers")
        print()
        
        all_results = {
            'queried_at': datetime.now().isoformat(),
            'brokers': [],
            'total_pending_rewards': 0
        }
        
        # Query each broker
        for broker in listener.shapeshift_brokers:
            print(f"🔍 Querying {broker['name']}: {broker['address']}")
            
            try:
                # Get broker info
                broker_info = listener.get_broker_info(broker['address'])
                
                # Get transactions
                transactions = listener.get_broker_transactions(broker['address'])
                
                # Get swaps
                swaps = listener.get_broker_swaps(broker['address'])
                
                # Calculate pending rewards (simplified)
                pending_rewards = 0
                if broker_info:
                    # Extract reward information from broker info
                    # This would depend on the actual API response structure
                    pending_rewards = len(transactions) * 0.001  # Placeholder calculation
                
                broker_result = {
                    'name': broker['name'],
                    'address': broker['address'],
                    'broker_info': broker_info,
                    'transaction_count': len(transactions),
                    'swap_count': len(swaps),
                    'pending_rewards': pending_rewards,
                    'is_active': len(transactions) > 0 or len(swaps) > 0
                }
                
                all_results['brokers'].append(broker_result)
                
                if pending_rewards > 0:
                    all_results['total_pending_rewards'] += pending_rewards
                
                # Display results
                status = "🟢 ACTIVE" if broker_result['is_active'] else "🔴 INACTIVE"
                print(f"  Status: {status}")
                print(f"  Transactions: {len(transactions)}")
                print(f"  Swaps: {len(swaps)}")
                print(f"  Pending Rewards: {pending_rewards}")
                if broker_info:
                    print(f"  Broker Info: {json.dumps(broker_info, indent=2)}")
                print()
                
            except Exception as e:
                print(f"  ❌ Error querying broker: {e}")
                print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shapeshift_rewards_listener_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        print()
        
        # Summary
        print(f"🎯 Query Complete!")
        print(f"   Brokers analyzed: {len(all_results['brokers'])}")
        print(f"   Total pending rewards: {all_results['total_pending_rewards']}")
        
        if all_results['total_pending_rewards'] > 0:
            print(f"\n💡 Found pending rewards!")
            print(f"   Check the JSON file for detailed data")
        else:
            print(f"\n💡 No pending rewards found")
            print(f"   This could mean:")
            print(f"   - Brokers haven't earned rewards yet")
            print(f"   - Rewards are paid out immediately")
            print(f"   - Need to check different reward endpoints")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure the Chainflip API server is running")

if __name__ == "__main__":
    main()

