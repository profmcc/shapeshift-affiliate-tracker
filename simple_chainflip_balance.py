#!/usr/bin/env python3
"""
Simple Chainflip Balance Query
Uses HTTP requests to query Chainflip balance information
"""

import requests
import json
import time
from datetime import datetime

def query_chainflip_balance():
    """Query Chainflip balance information using available methods"""
    
    # ShapeShift affiliate addresses
    addresses = [
        'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi',
        'cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8'
    ]
    
    print("🚀 Starting Simple Chainflip Balance Query...")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    
    results = {
        'queried_at': datetime.now().isoformat(),
        'addresses': {},
        'summary': {}
    }
    
    # Method 1: Try the working health endpoint and see if we can get more info
    print(f"\n{'='*60}")
    print(f"🔍 Method 1: Testing Chainflip API endpoints")
    print(f"{'='*60}")
    
    api_endpoints = [
        'https://api.chainflip.io/health',
        'https://api.chainflip.io/status',
        'https://api.chainflip.io/info'
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"\n📍 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ Success: {response.status_code}")
                try:
                    data = response.json()
                    print(f"  📊 Response: {json.dumps(data, indent=2)}")
                    
                    # Store successful responses
                    if endpoint not in results['summary']:
                        results['summary'][endpoint] = data
                        
                except json.JSONDecodeError:
                    print(f"  ⚠️ Not JSON: {response.text[:200]}...")
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Method 2: Try to get broker information from scan.chainflip.io
    print(f"\n{'='*60}")
    print(f"🔍 Method 2: Testing scan.chainflip.io endpoints")
    print(f"{'='*60}")
    
    for address in addresses:
        print(f"\n📍 Testing address: {address}")
        
        scan_endpoints = [
            f'https://scan.chainflip.io/brokers/{address}',
            f'https://scan.chainflip.io/accounts/{address}',
            f'https://scan.chainflip.io/addresses/{address}'
        ]
        
        address_results = {
            'address': address,
            'endpoints_tested': [],
            'balance_found': False,
            'balance': None
        }
        
        for endpoint in scan_endpoints:
            try:
                print(f"  🔍 Testing: {endpoint}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                response = requests.get(endpoint, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    print(f"    ✅ Success: {response.status_code}")
                    
                    # Look for balance information in the HTML
                    content = response.text.lower()
                    
                    # Check for common balance patterns
                    balance_patterns = [
                        r'balance[:\s]*(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*flip',
                        r'(\d+\.?\d*)\s*chainflip',
                        r'total[:\s]*(\d+\.?\d*)'
                    ]
                    
                    import re
                    balance_found = False
                    for pattern in balance_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"    💰 Potential balance found: {matches[0]}")
                            address_results['balance_found'] = True
                            address_results['balance'] = matches[0]
                            balance_found = True
                            break
                    
                    if not balance_found:
                        print(f"    ⚠️ No balance pattern found in content")
                    
                    # Store endpoint result
                    address_results['endpoints_tested'].append({
                        'url': endpoint,
                        'status': response.status_code,
                        'content_length': len(response.text),
                        'balance_found': balance_found
                    })
                    
                else:
                    print(f"    ❌ Failed: {response.status_code}")
                    address_results['endpoints_tested'].append({
                        'url': endpoint,
                        'status': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                address_results['endpoints_tested'].append({
                    'url': endpoint,
                    'error': str(e)
                })
        
        results['addresses'][address] = address_results
    
    # Method 3: Try alternative Chainflip domains
    print(f"\n{'='*60}")
    print(f"🔍 Method 3: Testing alternative Chainflip domains")
    print(f"{'='*60}")
    
    alt_domains = [
        'https://chainflip.io',
        'https://chainflip.network',
        'https://chainflip.com'
    ]
    
    for domain in alt_domains:
        try:
            print(f"\n📍 Testing: {domain}")
            response = requests.get(domain, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ Success: {response.status_code}")
                print(f"  📊 Content length: {len(response.text)}")
                
                # Look for API endpoints mentioned
                content = response.text.lower()
                if 'api' in content:
                    print(f"  🔗 API endpoints mentioned in content")
                    
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_chainflip_balance_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"💰 SIMPLE CHAINFLIP BALANCE QUERY SUMMARY")
    print(f"{'='*60}")
    
    for address, address_data in results['addresses'].items():
        print(f"\n📍 Address: {address}")
        print(f"  Balance Found: {'✅ YES' if address_data['balance_found'] else '❌ NO'}")
        
        if address_data['balance']:
            print(f"  Balance: {address_data['balance']}")
        
        successful_endpoints = len([ep for ep in address_data['endpoints_tested'] if ep.get('status') == 200])
        print(f"  Successful Endpoints: {successful_endpoints}/{len(address_data['endpoints_tested'])}")
    
    print(f"\n{'='*60}")
    
    return results

def main():
    """Main function"""
    try:
        results = query_chainflip_balance()
        
        if any(addr_data['balance_found'] for addr_data in results['addresses'].values()):
            print(f"\n🎯 Success! Found balance information!")
        else:
            print(f"\n💡 No balance information found")
            print(f"   This confirms that Chainflip broker balances are not publicly accessible")
            print(f"   Next steps:")
            print(f"   1. Set up local Chainflip node (requires Docker)")
            print(f"   2. Contact Chainflip team for API access")
            print(f"   3. Monitor transactions to calculate accumulated amounts")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
