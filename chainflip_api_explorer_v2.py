#!/usr/bin/env python3
"""
Enhanced Chainflip API Explorer
Tries different API patterns to find working endpoints
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, method='GET', data=None, headers=None):
    """Test a specific API endpoint"""
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return {'error': f'Unsupported method: {method}'}
        
        return {
            'url': url,
            'method': method,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_type': response.headers.get('content-type', ''),
            'content_length': len(response.text),
            'is_json': False,
            'data': None,
            'text_preview': response.text[:500] if response.text else ''
        }
        
    except Exception as e:
        return {
            'url': url,
            'method': method,
            'error': str(e)
        }

def test_graphql_endpoints():
    """Test potential GraphQL endpoints"""
    
    print("🔍 Testing GraphQL endpoints...")
    
    # ShapeShift broker address
    broker_address = 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi'
    
    # GraphQL queries to try
    queries = [
        {
            'name': 'Account Info',
            'query': '''
            query GetAccount($address: String!) {
                account(id: $address) {
                    id
                    balance
                    nonce
                }
            }
            ''',
            'variables': {'address': broker_address}
        },
        {
            'name': 'Broker Info',
            'query': '''
            query GetBroker($address: String!) {
                broker(id: $address) {
                    id
                    balance
                    totalVolume
                    totalFees
                }
            }
            ''',
            'variables': {'address': broker_address}
        },
        {
            'name': 'Simple Account',
            'query': '''
            query {
                account(id: "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi") {
                    id
                    balance
                }
            }
            '''
        }
    ]
    
    # Potential GraphQL endpoints
    endpoints = [
        'https://scan.chainflip.io/graphql',
        'https://scan.chainflip.io/api/graphql',
        'https://scan.chainflip.io/_next/data/v1.10.18/graphql.json',
        'https://api.chainflip.io/graphql',
        'https://chainflip.io/api/graphql'
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📍 Testing: {endpoint}")
        
        for query_info in queries:
            print(f"  Query: {query_info['name']}")
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            payload = {
                'query': query_info['query']
            }
            
            if 'variables' in query_info:
                payload['variables'] = query_info['variables']
            
            result = test_api_endpoint(endpoint, 'POST', payload, headers)
            result['query_name'] = query_info['name']
            
            if result.get('status_code') == 200:
                print(f"    ✅ Success: {result['status_code']}")
                try:
                    json_data = json.loads(result['text_preview'])
                    result['is_json'] = True
                    result['data'] = json_data
                    print(f"    📊 JSON Response: {json.dumps(json_data, indent=2)[:200]}...")
                except json.JSONDecodeError:
                    print(f"    ⚠️ Not JSON: {result['text_preview'][:100]}...")
            else:
                print(f"    ❌ Failed: {result.get('status_code', 'Error')}")
            
            results.append(result)
            time.sleep(1)  # Rate limiting
    
    return results

def test_rest_endpoints():
    """Test potential REST API endpoints"""
    
    print("\n🔍 Testing REST API endpoints...")
    
    # ShapeShift broker address
    broker_address = 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi'
    
    # REST endpoints to try
    endpoints = [
        f'https://scan.chainflip.io/api/brokers/{broker_address}',
        f'https://scan.chainflip.io/api/accounts/{broker_address}',
        f'https://scan.chainflip.io/api/addresses/{broker_address}',
        f'https://scan.chainflip.io/brokers/{broker_address}/api',
        f'https://scan.chainflip.io/brokers/{broker_address}/data',
        f'https://scan.chainflip.io/brokers/{broker_address}/balance',
        f'https://scan.chainflip.io/brokers/{broker_address}/transactions',
        f'https://api.chainflip.io/brokers/{broker_address}',
        f'https://api.chainflip.io/accounts/{broker_address}',
        f'https://chainflip.io/api/brokers/{broker_address}',
        f'https://chainflip.io/api/accounts/{broker_address}',
        'https://scan.chainflip.io/api/status',
        'https://scan.chainflip.io/api/health',
        'https://api.chainflip.io/status',
        'https://api.chainflip.io/health'
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📍 Testing: {endpoint}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        result = test_api_endpoint(endpoint, 'GET', headers=headers)
        
        if result.get('status_code') == 200:
            print(f"  ✅ Success: {result['status_code']}")
            try:
                json_data = json.loads(result['text_preview'])
                result['is_json'] = True
                result['data'] = json_data
                print(f"  📊 JSON Response: {json.dumps(json_data, indent=2)[:200]}...")
            except json.JSONDecodeError:
                print(f"  ⚠️ Not JSON: {result['text_preview'][:100]}...")
        else:
            print(f"  ❌ Failed: {result.get('status_code', 'Error')}")
        
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    return results

def test_websocket_endpoints():
    """Test potential WebSocket endpoints"""
    
    print("\n🔍 Testing WebSocket endpoints...")
    
    # WebSocket endpoints to try
    endpoints = [
        'wss://scan.chainflip.io/ws',
        'wss://scan.chainflip.io/graphql',
        'wss://api.chainflip.io/ws',
        'wss://chainflip.io/ws'
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"📍 Testing: {endpoint}")
        print(f"  ⚠️ WebSocket testing requires different library")
        print(f"  💡 Endpoint identified for manual testing")
        
        results.append({
            'url': endpoint,
            'type': 'websocket',
            'note': 'Requires websocket-client library for testing'
        })
    
    return results

def main():
    """Main function to explore Chainflip APIs"""
    
    print("🚀 Starting Enhanced Chainflip API Exploration...")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    
    all_results = {
        'queried_at': datetime.now().isoformat(),
        'graphql_results': [],
        'rest_results': [],
        'websocket_results': []
    }
    
    # Test GraphQL endpoints
    all_results['graphql_results'] = test_graphql_endpoints()
    
    # Test REST endpoints
    all_results['rest_results'] = test_rest_endpoints()
    
    # Test WebSocket endpoints
    all_results['websocket_results'] = test_websocket_endpoints()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_chainflip_api_exploration_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"💰 ENHANCED CHAINFLIP API EXPLORATION SUMMARY")
    print(f"{'='*60}")
    
    working_graphql = [r for r in all_results['graphql_results'] if r.get('status_code') == 200 and r.get('is_json')]
    working_rest = [r for r in all_results['rest_results'] if r.get('status_code') == 200 and r.get('is_json')]
    
    print(f"GraphQL Endpoints Tested: {len(all_results['graphql_results'])}")
    print(f"Working GraphQL: {len(working_graphql)}")
    print(f"REST Endpoints Tested: {len(all_results['rest_results'])}")
    print(f"Working REST: {len(working_rest)}")
    
    if working_graphql:
        print(f"\n✅ Working GraphQL Endpoints:")
        for result in working_graphql:
            print(f"  - {result['url']} ({result['query_name']})")
    
    if working_rest:
        print(f"\n✅ Working REST Endpoints:")
        for result in working_rest:
            print(f"  - {result['url']}")
    
    if not working_graphql and not working_rest:
        print(f"\n❌ No working API endpoints found")
        print(f"💡 This suggests:")
        print(f"   1. APIs require authentication")
        print(f"   2. APIs are not publicly accessible")
        print(f"   3. Need to use local Chainflip node")
    
    print(f"{'='*60}")
    
    return all_results

if __name__ == "__main__":
    main()
