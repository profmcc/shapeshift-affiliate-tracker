#!/usr/bin/env python3
"""
Query Public Chainflip API for ShapeShift Affiliate Address Balance
"""

import requests
import json
from datetime import datetime

def query_public_chainflip():
    """Query public Chainflip APIs for address balance"""
    
    # ShapeShift affiliate address
    address = 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi'
    
    print(f'🔍 Querying Chainflip address: {address}')
    print(f'⏰ Time: {datetime.now().isoformat()}')
    
    results = {
        'queried_at': datetime.now().isoformat(),
        'address': address,
        'endpoints_tested': [],
        'balance_found': False,
        'balance': None,
        'errors': []
    }
    
    # Try different public API endpoints
    endpoints = [
        {
            'name': 'Chainflip API Status',
            'url': 'https://api.chainflip.io/status',
            'method': 'GET',
            'type': 'rest'
        },
        {
            'name': 'Chainflip API Transactions',
            'url': 'https://api.chainflip.io/transactions',
            'method': 'GET',
            'type': 'rest'
        },
        {
            'name': 'Scan Chainflip GraphQL',
            'url': 'https://scan.chainflip.io/graphql',
            'method': 'POST',
            'type': 'graphql',
            'query': '''
            query GetAccount($address: String!) {
                account(id: $address) {
                    id
                    balance
                    nonce
                }
            }
            ''',
            'variables': {'address': address}
        }
    ]
    
    for endpoint in endpoints:
        print(f'\n📍 Testing: {endpoint["name"]}')
        print(f'   URL: {endpoint["url"]}')
        
        try:
            if endpoint['type'] == 'graphql':
                response = requests.post(
                    endpoint['url'], 
                    json={
                        'query': endpoint['query'], 
                        'variables': endpoint['variables']
                    },
                    timeout=15
                )
            else:
                response = requests.get(endpoint['url'], timeout=15)
            
            print(f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f'   ✅ Success: {json.dumps(data, indent=2)[:300]}...')
                    
                    # Check if we found balance information
                    if endpoint['type'] == 'graphql' and 'data' in data:
                        account_data = data.get('data', {}).get('account')
                        if account_data:
                            balance = account_data.get('balance')
                            if balance:
                                results['balance_found'] = True
                                results['balance'] = balance
                                print(f'   💰 Found balance: {balance}')
                    
                    results['endpoints_tested'].append({
                        'name': endpoint['name'],
                        'url': endpoint['url'],
                        'status': response.status_code,
                        'response': data
                    })
                    
                except json.JSONDecodeError:
                    print(f'   ⚠️ Response not JSON: {response.text[:200]}...')
                    results['endpoints_tested'].append({
                        'name': endpoint['name'],
                        'url': endpoint['url'],
                        'status': response.status_code,
                        'response': response.text[:500]
                    })
            else:
                print(f'   ❌ HTTP Error: {response.text[:200]}...')
                results['endpoints_tested'].append({
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'status': response.status_code,
                    'error': response.text[:500]
                })
                
        except Exception as e:
            error_msg = str(e)
            print(f'   ❌ Exception: {error_msg}')
            results['errors'].append({
                'endpoint': endpoint['name'],
                'error': error_msg
            })
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"public_chainflip_query_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'\n💾 Results saved to: {filename}')
    
    # Display summary
    print(f'\n{'='*60}')
    print(f'💰 CHAINFLIP PUBLIC API QUERY SUMMARY')
    print(f'{'='*60}')
    print(f'Address: {results["address"]}')
    print(f'Balance Found: {"✅ YES" if results["balance_found"] else "❌ NO"}')
    if results['balance']:
        print(f'Balance: {results["balance"]}')
    print(f'Endpoints Tested: {len(results["endpoints_tested"])}')
    print(f'Errors: {len(results["errors"])}')
    
    return results

def main():
    """Main function"""
    try:
        results = query_public_chainflip()
        
        if results['balance_found']:
            print(f'\n🎯 Success! Found balance: {results["balance"]}')
        else:
            print(f'\n💡 No balance found in public APIs')
            print(f'   This suggests we need the local node setup')
            print(f'   or different API endpoints')
            
    except Exception as e:
        print(f'❌ Script error: {e}')

if __name__ == "__main__":
    main()
