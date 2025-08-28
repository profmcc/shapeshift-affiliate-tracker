#!/usr/bin/env python3
"""
Query ShapeShift Affiliate Transactions
Queries the local Chainflip node for recent transactions involving ShapeShift affiliate addresses
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

class ShapeShiftTransactionQuery:
    def __init__(self):
        """Initialize the ShapeShift transaction query client"""
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
            
            response = self.session.post(
                self.node_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
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
    
    def get_latest_block_number(self) -> Optional[int]:
        """Get the latest block number"""
        try:
            result = self.make_rpc_call("chain_getHeader")
            if result and 'number' in result:
                block_number = int(result['number'], 16)
                logger.info(f"📊 Latest block: {block_number}")
                return block_number
        except Exception as e:
            logger.error(f"❌ Error getting latest block: {e}")
        return None
    
    def get_block_by_number(self, block_number: int) -> Optional[Dict]:
        """Get block by number"""
        try:
            result = self.make_rpc_call("chain_getBlock", [hex(block_number)])
            return result
        except Exception as e:
            logger.error(f"❌ Error getting block {block_number}: {e}")
            return None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        """Get block by hash"""
        try:
            result = self.make_rpc_call("chain_getBlock", [block_hash])
            return result
        except Exception as e:
            logger.error(f"❌ Error getting block by hash {block_hash}: {e}")
            return None
    
    def get_account_nonce(self, account_id: str) -> Optional[int]:
        """Get account nonce (transaction count)"""
        try:
            result = self.make_rpc_call("system_accountNextIndex", [account_id])
            return result
        except Exception as e:
            logger.error(f"❌ Error getting account nonce: {e}")
            return None
    
    def analyze_block_for_broker_activity(self, block_data: Dict, broker_addresses: List[str]) -> Dict:
        """Analyze a block for broker-related activity"""
        broker_activity = {
            'block_number': None,
            'block_hash': None,
            'broker_transactions': [],
            'total_extrinsics': 0
        }
        
        try:
            if 'block' in block_data:
                block = block_data['block']
                header = block.get('header', {})
                
                broker_activity['block_number'] = int(header.get('number', '0'), 16)
                broker_activity['block_hash'] = header.get('hash', 'N/A')
                
                # Get extrinsics (transactions)
                extrinsics = block.get('extrinsics', [])
                broker_activity['total_extrinsics'] = len(extrinsics)
                
                logger.info(f"🔍 Block {broker_activity['block_number']}: {len(extrinsics)} extrinsics")
                
                # Look for broker-related activity in extrinsics
                for i, extrinsic in enumerate(extrinsics):
                    try:
                        # Check if extrinsic involves any of our broker addresses
                        extrinsic_str = str(extrinsic)
                        
                        for broker_addr in broker_addresses:
                            if broker_addr in extrinsic_str:
                                logger.info(f"🎯 Found broker activity in extrinsic {i} of block {broker_activity['block_number']}")
                                
                                broker_activity['broker_transactions'].append({
                                    'extrinsic_index': i,
                                    'broker_address': broker_addr,
                                    'extrinsic_data': extrinsic_str[:200] + "..." if len(extrinsic_str) > 200 else extrinsic_str
                                })
                                
                    except Exception as e:
                        logger.error(f"❌ Error analyzing extrinsic {i}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error analyzing block: {e}")
        
        return broker_activity
    
    def query_recent_broker_transactions(self, block_range: int = 100) -> List[Dict]:
        """Query recent blocks for broker transactions"""
        logger.info(f"🚀 Querying recent {block_range} blocks for ShapeShift broker activity...")
        
        # Get latest block number
        latest_block = self.get_latest_block_number()
        if not latest_block:
            logger.error("❌ Could not get latest block number")
            return []
        
        broker_addresses = [broker['address'] for broker in self.shapeshift_brokers]
        all_broker_activity = []
        
        # Check recent blocks for broker activity
        for block_num in range(latest_block, max(0, latest_block - block_range), -1):
            try:
                logger.info(f"🔍 Checking block {block_num}...")
                
                block_data = self.get_block_by_number(block_num)
                if block_data:
                    # Analyze block for broker activity
                    broker_activity = self.analyze_block_for_broker_activity(block_data, broker_addresses)
                    
                    if broker_activity['broker_transactions']:
                        logger.info(f"✅ Found broker activity in block {block_num}")
                        all_broker_activity.append(broker_activity)
                    else:
                        logger.info(f"📭 No broker activity in block {block_num}")
                
                # Rate limiting to avoid overwhelming the node
                import time
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error checking block {block_num}: {e}")
                continue
        
        return all_broker_activity
    
    def get_broker_summary(self) -> Dict:
        """Get summary of broker activity"""
        logger.info("📊 Getting broker activity summary...")
        
        summary = {
            'queried_at': datetime.now().isoformat(),
            'brokers': [],
            'total_transactions': 0,
            'recent_activity': []
        }
        
        for broker in self.shapeshift_brokers:
            logger.info(f"🔍 Getting summary for {broker['name']}: {broker['address']}")
            
            # Get account nonce
            nonce = self.get_account_nonce(broker['address'])
            
            broker_info = {
                'name': broker['name'],
                'address': broker['address'],
                'nonce': nonce,
                'total_transactions': nonce if nonce is not None else 0,
                'is_active': nonce > 0 if nonce is not None else False
            }
            
            summary['brokers'].append(broker_info)
            summary['total_transactions'] += broker_info['total_transactions']
            
            logger.info(f"✅ {broker['name']}: Nonce={nonce}, Active={broker_info['is_active']}")
        
        return summary
    
    def run_comprehensive_query(self, block_range: int = 100):
        """Run comprehensive query for ShapeShift broker transactions"""
        logger.info("🚀 Starting comprehensive ShapeShift broker transaction query...")
        
        # Get broker summary
        broker_summary = self.get_broker_summary()
        
        # Query recent transactions
        recent_transactions = self.query_recent_broker_transactions(block_range)
        
        # Compile results
        results = {
            'summary': broker_summary,
            'recent_transactions': recent_transactions,
            'query_metadata': {
                'block_range_queried': block_range,
                'blocks_checked': len(recent_transactions),
                'queried_at': datetime.now().isoformat()
            }
        }
        
        # Save results
        self._save_results(results)
        
        # Display summary
        self._display_results_summary(results)
        
        return results
    
    def _save_results(self, results: Dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"shapeshift_broker_transactions_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def _display_results_summary(self, results: Dict):
        """Display summary of results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 SHAPESHIFT BROKER TRANSACTION SUMMARY")
        logger.info(f"{'='*60}")
        
        summary = results['summary']
        logger.info(f"Query Time: {summary['queried_at']}")
        logger.info(f"Total Broker Transactions: {summary['total_transactions']}")
        
        for broker in summary['brokers']:
            status = "🟢 ACTIVE" if broker['is_active'] else "🔴 INACTIVE"
            logger.info(f"{broker['name']}: {status} (Nonce: {broker['nonce']})")
        
        recent_tx = results['recent_transactions']
        logger.info(f"\nRecent Activity:")
        logger.info(f"Blocks with broker activity: {len(recent_tx)}")
        
        if recent_tx:
            for activity in recent_tx:
                logger.info(f"  Block {activity['block_number']}: {len(activity['broker_transactions'])} broker transactions")
        else:
            logger.info("  No recent broker activity found in queried blocks")
        
        logger.info(f"{'='*60}")

def main():
    """Main function"""
    try:
        query_client = ShapeShiftTransactionQuery()
        
        # Query recent 200 blocks for broker activity
        results = query_client.run_comprehensive_query(block_range=200)
        
        print(f"\n🎯 ShapeShift Broker Transaction Query Complete!")
        print(f"   Brokers analyzed: {len(results['summary']['brokers'])}")
        print(f"   Total transactions: {results['summary']['total_transactions']}")
        print(f"   Blocks with activity: {len(results['recent_transactions'])}")
        
        if results['recent_transactions']:
            print(f"\n💡 Found broker activity in recent blocks!")
            print(f"   Check the JSON file for detailed transaction data")
        else:
            print(f"\n💡 No recent broker activity found")
            print(f"   This could mean:")
            print(f"   - Brokers haven't been active recently")
            print(f"   - Activity is in older blocks")
            print(f"   - Need to query more blocks")
        
    except Exception as e:
        logger.error(f"❌ Error running transaction query: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()


