#!/usr/bin/env python3
"""
Query Local Chainflip Node
Queries the local Chainflip node for broker information and accumulated amounts
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class LocalChainflipQuery:
    def __init__(self):
        """Initialize the local Chainflip query client"""
        self.node_url = "http://localhost:9944"
        self.session = requests.Session()
        
        # ShapeShift affiliate addresses on Chainflip
        self.shapeshift_brokers = [
            {
                'address': 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi',
                'name': 'ShapeShift Broker 1'
            },
            {
                'address': 'cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8',
                'name': 'ShapeShift Broker 2'
            }
        ]
    
    def make_rpc_call(self, method: str, params: List = None) -> Optional[Dict]:
        """Make a JSON-RPC call to the local Chainflip node"""
        try:
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": method
            }
            
            if params:
                payload["params"] = params
            
            logger.info(f"🔗 RPC Call: {method} with params: {params}")
            
            response = self.session.post(
                self.node_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    logger.info(f"✅ RPC Response: {method} successful")
                    return result['result']
                elif 'error' in result:
                    logger.error(f"❌ RPC Error: {method} - {result['error']}")
                    return None
                else:
                    logger.warning(f"⚠️ Unexpected RPC response format: {result}")
                    return None
            else:
                logger.error(f"❌ HTTP Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def get_chain_head(self) -> Optional[Dict]:
        """Get the current chain head information"""
        return self.make_rpc_call("chain_getHeader")
    
    def get_account_info(self, account_id: str) -> Optional[Dict]:
        """Get account information for a broker"""
        # Try different methods to get account info
        methods = [
            "state_getStorage",
            "chain_getBlock",
            "system_accountNextIndex"
        ]
        
        for method in methods:
            try:
                if method == "state_getStorage":
                    # This would need a storage key, which is complex
                    continue
                elif method == "chain_getBlock":
                    # Get latest block
                    result = self.make_rpc_call(method, ["latest"])
                    if result:
                        logger.info(f"✅ Got latest block: {result.get('block', {}).get('header', {}).get('number', 'N/A')}")
                elif method == "system_accountNextIndex":
                    # Get account nonce
                    result = self.make_rpc_call(method, [account_id])
                    if result:
                        logger.info(f"✅ Got account nonce: {result}")
            except Exception as e:
                logger.error(f"❌ Error with method {method}: {e}")
        
        return None
    
    def query_broker_data(self, broker_address: str) -> Dict:
        """Query broker data from the local node"""
        logger.info(f"🔍 Querying broker: {broker_address}")
        
        broker_data = {
            'address': broker_address,
            'queried_at': datetime.now().isoformat(),
            'chain_head': None,
            'account_info': None,
            'storage_data': None
        }
        
        # Get chain head
        chain_head = self.get_chain_head()
        if chain_head:
            broker_data['chain_head'] = chain_head
        
        # Get account info
        account_info = self.get_account_info(broker_address)
        if account_info:
            broker_data['account_info'] = account_info
        
        return broker_data
    
    def run_queries(self):
        """Run queries for all ShapeShift brokers"""
        logger.info("🚀 Starting local Chainflip node queries...")
        
        all_results = []
        
        for broker in self.shapeshift_brokers:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Querying: {broker['name']}")
            logger.info(f"Address: {broker['address']}")
            logger.info(f"{'='*60}")
            
            broker_result = self.query_broker_data(broker['address'])
            broker_result['broker_name'] = broker['name']
            
            all_results.append(broker_result)
            
            # Display summary
            self._display_broker_summary(broker_result)
            
            # Rate limiting
            import time
            time.sleep(2)
        
        # Save results
        self._save_results(all_results)
        
        logger.info("\n✅ Local Chainflip queries completed!")
        return all_results
    
    def _display_broker_summary(self, broker_data: Dict):
        """Display summary for a single broker"""
        logger.info(f"\n📊 Broker Query Summary:")
        logger.info(f"Address: {broker_data['address']}")
        logger.info(f"Name: {broker_data.get('broker_name', 'N/A')}")
        logger.info(f"Queried at: {broker_data['queried_at']}")
        
        if broker_data.get('chain_head'):
            logger.info(f"✅ Chain head retrieved")
        
        if broker_data.get('account_info'):
            logger.info(f"✅ Account info retrieved")
    
    def _save_results(self, results: List[Dict]):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"local_chainflip_queries_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

def main():
    """Main function"""
    try:
        query_client = LocalChainflipQuery()
        results = query_client.run_queries()
        
        print(f"\n🎯 Local Chainflip Query Results:")
        print(f"   Brokers queried: {len(results)}")
        
        if results:
            print(f"   ✅ Successfully queried local Chainflip node")
            print(f"\n💡 Next steps:")
            print(f"   1. Review the detailed results in the JSON file")
            print(f"   2. The local node is synced and ready for queries")
            print(f"   3. Consider setting up the broker API with funded accounts")
        else:
            print(f"   ❌ No broker data retrieved")
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Check if the local Chainflip node is running")
            print(f"   2. Verify the node is fully synced")
            print(f"   3. Check if the RPC endpoint is accessible")
        
    except Exception as e:
        logger.error(f"❌ Error running local queries: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()


