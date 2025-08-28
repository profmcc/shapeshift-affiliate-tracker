#!/usr/bin/env python3
"""
Chainflip Balance Query Script
Queries the Chainflip API to check accumulated amounts on the ShapeShift affiliate address
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipBalanceChecker:
    def __init__(self):
        """Initialize the Chainflip balance checker"""
        self.api_base_url = "https://api.chainflip.io"
        
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
    
    def test_api_connection(self) -> bool:
        """Test connection to Chainflip API"""
        try:
            logger.info("🔧 Testing Chainflip API connection...")
            
            # Try the health endpoint
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Successfully connected to Chainflip API")
                logger.info(f"API Status: {json.dumps(data, indent=2)}")
                return True
            
            logger.warning("⚠️ Chainflip API connection test inconclusive")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Chainflip API: {e}")
            return False
    
    def get_broker_info(self, broker_address: str) -> Optional[Dict]:
        """Get broker information from Chainflip API"""
        try:
            logger.info(f"🔍 Querying broker info for: {broker_address}")
            
            # Try to get broker information
            response = requests.get(
                f"{self.api_base_url}/brokers/{broker_address}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Found broker info for {broker_address}")
                return data
            elif response.status_code == 404:
                logger.warning(f"⚠️ Broker {broker_address} not found")
                return None
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error querying broker {broker_address}: {e}")
            return None
    
    def get_broker_transactions(self, broker_address: str, limit: int = 50) -> List[Dict]:
        """Get recent transactions for a broker"""
        try:
            logger.info(f"🔍 Querying recent transactions for broker: {broker_address}")
            
            # Try to get broker transactions
            response = requests.get(
                f"{self.api_base_url}/brokers/{broker_address}/transactions",
                params={'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                logger.info(f"✅ Found {len(transactions)} transactions for {broker_address}")
                return transactions
            else:
                logger.warning(f"⚠️ Failed to get transactions: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error querying transactions for {broker_address}: {e}")
            return []
    
    def get_broker_swaps(self, broker_address: str, limit: int = 50) -> List[Dict]:
        """Get recent swaps for a broker"""
        try:
            logger.info(f"🔍 Querying recent swaps for broker: {broker_address}")
            
            # Try to get broker swaps
            response = requests.get(
                f"{self.api_base_url}/brokers/{broker_address}/swaps",
                params={'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                swaps = data.get('swaps', [])
                logger.info(f"✅ Found {len(swaps)} swaps for {broker_address}")
                return swaps
            else:
                logger.warning(f"⚠️ Failed to get swaps: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error querying swaps for {broker_address}: {e}")
            return []
    
    def get_broker_balance(self, broker_address: str) -> Optional[Dict]:
        """Get broker balance information"""
        try:
            logger.info(f"🔍 Querying balance for broker: {broker_address}")
            
            # Try to get broker balance
            response = requests.get(
                f"{self.api_base_url}/brokers/{broker_address}/balance",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Found balance info for {broker_address}")
                return data
            else:
                logger.warning(f"⚠️ Failed to get balance: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error querying balance for {broker_address}: {e}")
            return None
    
    def get_available_endpoints(self) -> List[str]:
        """Discover available API endpoints"""
        try:
            logger.info("🔍 Discovering available API endpoints...")
            
            # Common endpoints to test
            endpoints = [
                "/health",
                "/status",
                "/brokers",
                "/swaps",
                "/transactions",
                "/assets",
                "/chains"
            ]
            
            available = []
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        available.append(endpoint)
                        logger.info(f"✅ {endpoint} - Available")
                    else:
                        logger.info(f"⚠️ {endpoint} - Status: {response.status_code}")
                except Exception as e:
                    logger.info(f"❌ {endpoint} - Error: {e}")
            
            return available
            
        except Exception as e:
            logger.error(f"❌ Error discovering endpoints: {e}")
            return []
    
    def analyze_broker_activity(self, broker_address: str) -> Dict:
        """Analyze broker activity and accumulated amounts"""
        logger.info(f"🔍 Analyzing broker activity for: {broker_address}")
        
        results = {
            'broker_address': broker_address,
            'timestamp': datetime.now().isoformat(),
            'broker_info': None,
            'balance': None,
            'recent_transactions': [],
            'recent_swaps': [],
            'total_volume': 0,
            'total_fees': 0
        }
        
        # Get broker information
        broker_info = self.get_broker_info(broker_address)
        if broker_info:
            results['broker_info'] = broker_info
        
        # Get balance information
        balance = self.get_broker_balance(broker_address)
        if balance:
            results['balance'] = balance
        
        # Get recent transactions
        transactions = self.get_broker_transactions(broker_address, limit=20)
        if transactions:
            results['recent_transactions'] = transactions
        
        # Get recent swaps
        swaps = self.get_broker_swaps(broker_address, limit=20)
        if swaps:
            results['recent_swaps'] = swaps
        
        # Calculate totals if we have data
        if swaps:
            for swap in swaps:
                # Extract volume and fees
                deposit_amount = float(swap.get('depositAmount', 0))
                broker_fee = float(swap.get('brokerFee', {}).get('amount', 0))
                
                results['total_volume'] += deposit_amount
                results['total_fees'] += broker_fee
        
        return results
    
    def run_comprehensive_check(self):
        """Run comprehensive check on all ShapeShift brokers"""
        logger.info("🚀 Starting comprehensive Chainflip broker check...")
        
        # Test API connection first
        if not self.test_api_connection():
            logger.error("❌ Cannot proceed without API connection")
            return
        
        # Discover available endpoints
        available_endpoints = self.get_available_endpoints()
        logger.info(f"📋 Available endpoints: {len(available_endpoints)}")
        
        # Check each broker
        all_results = []
        for broker in self.shapeshift_brokers:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Checking broker: {broker['name']}")
            logger.info(f"Address: {broker['address']}")
            logger.info(f"{'='*60}")
            
            results = self.analyze_broker_activity(broker['address'])
            all_results.append(results)
            
            # Display results
            self._display_broker_results(results)
            
            # Rate limiting
            time.sleep(1)
        
        # Save comprehensive results
        self._save_results(all_results)
        
        logger.info("\n✅ Comprehensive check completed!")
    
    def _display_broker_results(self, results: Dict):
        """Display broker analysis results"""
        logger.info(f"\n📊 Broker Analysis Results:")
        logger.info(f"Address: {results['broker_address']}")
        logger.info(f"Timestamp: {results['timestamp']}")
        
        if results['broker_info']:
            logger.info(f"✅ Broker info found")
            info = results['broker_info']
            logger.info(f"   Name: {info.get('name', 'N/A')}")
            logger.info(f"   Status: {info.get('status', 'N/A')}")
            logger.info(f"   Created: {info.get('createdAt', 'N/A')}")
        
        if results['balance']:
            logger.info(f"✅ Balance info found")
            balance = results['balance']
            logger.info(f"   Total Balance: {balance.get('total', 'N/A')}")
            logger.info(f"   Available: {balance.get('available', 'N/A')}")
            logger.info(f"   Locked: {balance.get('locked', 'N/A')}")
        
        if results['recent_transactions']:
            logger.info(f"✅ Recent transactions: {len(results['recent_transactions'])}")
        
        if results['recent_swaps']:
            logger.info(f"✅ Recent swaps: {len(results['recent_swaps'])}")
            logger.info(f"   Total volume: {results['total_volume']}")
            logger.info(f"   Total fees: {results['total_fees']}")
        
        if not any([results['broker_info'], results['balance'], results['recent_transactions'], results['recent_swaps']]):
            logger.warning("⚠️ No data found for this broker")
    
    def _save_results(self, results: List[Dict]):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_broker_analysis_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

def main():
    """Main function"""
    checker = ChainflipBalanceChecker()
    checker.run_comprehensive_check()

if __name__ == "__main__":
    main()


