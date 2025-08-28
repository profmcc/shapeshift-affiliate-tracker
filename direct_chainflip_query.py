#!/usr/bin/env python3
"""
Direct Chainflip Network Query
Queries the Chainflip network directly for address balance information
"""

import json
import asyncio
import websockets
import time
from datetime import datetime
from typing import Dict, Optional

class DirectChainflipQuery:
    def __init__(self):
        """Initialize the direct Chainflip query client"""
        
        # ShapeShift affiliate addresses
        self.shapeshift_addresses = [
            'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi',
            'cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8'
        ]
        
        # Public Chainflip RPC endpoints
        self.rpc_endpoints = [
            'wss://rpc.chainflip.io',
            'wss://chainflip-rpc.publicnode.com',
            'wss://chainflip-rpc.dwellir.com'
        ]
        
        # RPC methods to try
        self.rpc_methods = [
            {
                'name': 'Account Info',
                'method': 'system_account',
                'params': []
            },
            {
                'name': 'Account Next Index',
                'method': 'system_accountNextIndex',
                'params': []
            },
            {
                'name': 'Chain Head',
                'method': 'chain_getHeader',
                'params': []
            },
            {
                'name': 'Chain Block',
                'method': 'chain_getBlock',
                'params': []
            }
        ]
    
    async def query_rpc_endpoint(self, endpoint: str, address: str) -> Dict:
        """Query a specific RPC endpoint for address information"""
        
        print(f"🔍 Querying {endpoint} for address: {address}")
        
        try:
            async with websockets.connect(endpoint, timeout=15) as websocket:
                
                results = {
                    'endpoint': endpoint,
                    'address': address,
                    'queried_at': datetime.now().isoformat(),
                    'methods': {}
                }
                
                # Test basic connection
                try:
                    # Test chain_getHeader first
                    header_request = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "chain_getHeader",
                        "params": []
                    }
                    
                    await websocket.send(json.dumps(header_request))
                    header_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    header_data = json.loads(header_response)
                    
                    if 'result' in header_data:
                        print(f"  ✅ Connected successfully")
                        print(f"  📊 Latest block: {header_data['result'].get('number', 'N/A')}")
                        
                        # Store header info
                        results['methods']['chain_getHeader'] = {
                            'success': True,
                            'data': header_data['result']
                        }
                        
                        # Now try to get account information
                        for method_info in self.rpc_methods:
                            if method_info['method'] == 'system_account':
                                # Try to get account info
                                account_request = {
                                    "id": 2,
                                    "jsonrpc": "2.0",
                                    "method": "system_account",
                                    "params": [address]
                                }
                                
                                try:
                                    await websocket.send(json.dumps(account_request))
                                    account_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                                    account_data = json.loads(account_response)
                                    
                                    if 'result' in account_data:
                                        print(f"  💰 Account found: {account_data['result']}")
                                        results['methods']['system_account'] = {
                                            'success': True,
                                            'data': account_data['result']
                                        }
                                    else:
                                        print(f"  ⚠️ No account result: {account_data.get('error', 'Unknown error')}")
                                        results['methods']['system_account'] = {
                                            'success': False,
                                            'error': account_data.get('error', 'Unknown error')
                                        }
                                        
                                except Exception as e:
                                    print(f"  ❌ Account query failed: {e}")
                                    results['methods']['system_account'] = {
                                        'success': False,
                                        'error': str(e)
                                    }
                                
                                break
                        
                        # Try to get account nonce
                        nonce_request = {
                            "id": 3,
                            "jsonrpc": "2.0",
                            "method": "system_accountNextIndex",
                            "params": [address]
                        }
                        
                        try:
                            await websocket.send(json.dumps(nonce_request))
                            nonce_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                            nonce_data = json.loads(nonce_response)
                            
                            if 'result' in nonce_data:
                                print(f"  🔢 Account nonce: {nonce_data['result']}")
                                results['methods']['system_accountNextIndex'] = {
                                    'success': True,
                                    'data': nonce_data['result']
                                }
                            else:
                                print(f"  ⚠️ No nonce result: {nonce_data.get('error', 'Unknown error')}")
                                results['methods']['system_accountNextIndex'] = {
                                    'success': False,
                                    'error': nonce_data.get('error', 'Unknown error')
                                }
                                
                        except Exception as e:
                            print(f"  ❌ Nonce query failed: {e}")
                            results['methods']['system_accountNextIndex'] = {
                                'success': False,
                                'error': str(e)
                            }
                        
                    else:
                        print(f"  ❌ Header query failed: {header_data.get('error', 'Unknown error')}")
                        results['methods']['chain_getHeader'] = {
                            'success': False,
                            'error': header_data.get('error', 'Unknown error')
                        }
                        
                except Exception as e:
                    print(f"  ❌ Connection test failed: {e}")
                    results['error'] = str(e)
                
                return results
                
        except Exception as e:
            print(f"  ❌ WebSocket connection failed: {e}")
            return {
                'endpoint': endpoint,
                'address': address,
                'queried_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def query_all_endpoints(self) -> Dict:
        """Query all RPC endpoints for all addresses"""
        
        print("🚀 Starting direct Chainflip network queries...")
        print(f"⏰ Time: {datetime.now().isoformat()}")
        
        all_results = {
            'queried_at': datetime.now().isoformat(),
            'addresses': {},
            'endpoints_tested': len(self.rpc_endpoints)
        }
        
        for address in self.shapeshift_addresses:
            print(f"\n{'='*60}")
            print(f"🔍 Querying address: {address}")
            print(f"{'='*60}")
            
            address_results = []
            
            for endpoint in self.rpc_endpoints:
                result = await self.query_rpc_endpoint(endpoint, address)
                address_results.append(result)
                
                # Rate limiting between endpoints
                await asyncio.sleep(1)
            
            all_results['addresses'][address] = address_results
        
        return all_results
    
    def save_results(self, results: Dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"direct_chainflip_query_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    def display_summary(self, results: Dict):
        """Display a summary of the results"""
        
        print(f"\n{'='*60}")
        print(f"💰 DIRECT CHAINFLIP QUERY SUMMARY")
        print(f"{'='*60}")
        print(f"Query Time: {results['queried_at']}")
        print(f"Endpoints Tested: {results['endpoints_tested']}")
        
        for address, address_results in results['addresses'].items():
            print(f"\n📍 Address: {address}")
            
            successful_queries = 0
            for result in address_results:
                if 'error' not in result:
                    successful_queries += 1
                    
                    # Check if we got account info
                    if 'methods' in result:
                        for method_name, method_result in result['methods'].items():
                            if method_result.get('success'):
                                if method_name == 'system_account':
                                    account_data = method_result['data']
                                    if account_data:
                                        print(f"  ✅ Account Info: {account_data}")
                                    else:
                                        print(f"  ⚠️ Account exists but no data")
                                elif method_name == 'system_accountNextIndex':
                                    nonce = method_result['data']
                                    print(f"  🔢 Account Nonce: {nonce}")
            
            print(f"  📊 Successful queries: {successful_queries}/{len(address_results)}")
        
        print(f"{'='*60}")

async def main():
    """Main async function"""
    try:
        query_client = DirectChainflipQuery()
        results = await query_client.query_all_endpoints()
        
        # Save results
        query_client.save_results(results)
        
        # Display summary
        query_client.display_summary(results)
        
        return results
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        return None

def run_sync():
    """Run the async function in sync mode"""
    try:
        return asyncio.run(main())
    except Exception as e:
        print(f"❌ Error running async: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting Direct Chainflip Network Query...")
    print("💡 This will query the Chainflip network directly via WebSocket")
    print("💡 No local Docker setup required")
    
    results = run_sync()
    
    if results:
        print(f"\n🎯 Query completed successfully!")
    else:
        print(f"\n❌ Query failed")
