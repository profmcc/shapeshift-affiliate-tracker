#!/usr/bin/env python3
"""
Chainflip Broker API Client
Queries the working Chainflip broker API endpoints to get accumulated amounts
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipBrokerAPI:
    def __init__(self):
        """Initialize the Chainflip broker API client"""
        self.base_url = "https://scan.chainflip.io"
        self.session = requests.Session()
        
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://scan.chainflip.io/',
        })
        
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
        
        # Working API endpoints discovered
        self.api_endpoints = [
            '/api',
            '/data',
            '/swaps',
            '/transactions'
        ]
    
    def get_broker_api(self, broker_address: str, endpoint: str) -> Optional[Dict]:
        """Get data from a broker API endpoint"""
        try:
            url = f"{self.base_url}/brokers/{broker_address}{endpoint}"
            logger.info(f"🔍 Querying: {url}")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully queried {endpoint} for {broker_address}")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    return {
                        'endpoint': endpoint,
                        'url': url,
                        'status_code': response.status_code,
                        'data': data,
                        'is_json': True,
                        'content_length': len(response.text)
                    }
                except json.JSONDecodeError:
                    # Return as text if not JSON
                    return {
                        'endpoint': endpoint,
                        'url': url,
                        'status_code': response.status_code,
                        'data': response.text,
                        'is_json': False,
                        'content_length': len(response.text)
                    }
            else:
                logger.warning(f"⚠️ {endpoint} returned: {response.status_code}")
                return {
                    'endpoint': endpoint,
                    'url': url,
                    'status_code': response.status_code,
                    'data': None,
                    'is_json': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Error querying {endpoint} for {broker_address}: {e}")
            return {
                'endpoint': endpoint,
                'url': url if 'url' in locals() else f"{self.base_url}/brokers/{broker_address}{endpoint}",
                'status_code': None,
                'data': None,
                'is_json': False,
                'error': str(e)
            }
    
    def get_broker_info(self, broker_address: str) -> Dict:
        """Get comprehensive broker information from all endpoints"""
        logger.info(f"🔍 Getting comprehensive info for broker: {broker_address}")
        
        broker_info = {
            'address': broker_address,
            'queried_at': datetime.now().isoformat(),
            'endpoints': {}
        }
        
        for endpoint in self.api_endpoints:
            endpoint_data = self.get_broker_api(broker_address, endpoint)
            if endpoint_data:
                broker_info['endpoints'][endpoint] = endpoint_data
            
            # Rate limiting
            time.sleep(1)
        
        return broker_info
    
    def analyze_broker_data(self, broker_info: Dict) -> Dict:
        """Analyze broker data to extract key metrics"""
        logger.info(f"📊 Analyzing data for broker: {broker_info['address']}")
        
        analysis = {
            'address': broker_info['address'],
            'queried_at': broker_info['queried_at'],
            'total_volume': None,
            'total_fees': None,
            'swap_count': None,
            'last_activity': None,
            'status': None,
            'data_summary': {}
        }
        
        for endpoint, data in broker_info['endpoints'].items():
            if data.get('is_json') and data.get('data'):
                json_data = data['data']
                
                # Extract key metrics based on endpoint
                if endpoint == '/data':
                    analysis['data_summary']['data_endpoint'] = self._extract_data_metrics(json_data)
                elif endpoint == '/swaps':
                    analysis['data_summary']['swaps_endpoint'] = self._extract_swaps_metrics(json_data)
                elif endpoint == '/transactions':
                    analysis['data_summary']['transactions_endpoint'] = self._extract_transactions_metrics(json_data)
                elif endpoint == '/api':
                    analysis['data_summary']['api_endpoint'] = self._extract_api_metrics(json_data)
        
        # Try to extract overall metrics from all data
        analysis.update(self._extract_overall_metrics(broker_info))
        
        return analysis
    
    def _extract_data_metrics(self, data: Dict) -> Dict:
        """Extract metrics from the data endpoint"""
        metrics = {}
        
        # Look for common data patterns
        if isinstance(data, dict):
            # Volume metrics
            volume_fields = ['totalVolume', 'volume', 'tvl', 'total_value']
            for field in volume_fields:
                if field in data:
                    metrics['volume'] = data[field]
                    break
            
            # Fee metrics
            fee_fields = ['totalFees', 'fees', 'brokerFees', 'affiliateFees']
            for field in fee_fields:
                if field in data:
                    metrics['fees'] = data[field]
                    break
            
            # Status metrics
            status_fields = ['status', 'state', 'active', 'verified']
            for field in status_fields:
                if field in data:
                    metrics['status'] = data[field]
                    break
        
        return metrics
    
    def _extract_swaps_metrics(self, data: Dict) -> Dict:
        """Extract metrics from the swaps endpoint"""
        metrics = {}
        
        if isinstance(data, dict):
            # Count metrics
            if 'swaps' in data and isinstance(data['swaps'], list):
                metrics['swap_count'] = len(data['swaps'])
                metrics['swaps'] = data['swaps']
            
            # Look for aggregated data
            if 'totalSwaps' in data:
                metrics['total_swaps'] = data['totalSwaps']
            if 'totalVolume' in data:
                metrics['total_volume'] = data['totalVolume']
        
        return metrics
    
    def _extract_transactions_metrics(self, data: Dict) -> Dict:
        """Extract metrics from the transactions endpoint"""
        metrics = {}
        
        if isinstance(data, dict):
            # Count metrics
            if 'transactions' in data and isinstance(data['transactions'], list):
                metrics['transaction_count'] = len(data['transactions'])
                metrics['transactions'] = data['transactions']
            
            # Look for aggregated data
            if 'totalTransactions' in data:
                metrics['total_transactions'] = data['totalTransactions']
            if 'totalVolume' in data:
                metrics['total_volume'] = data['totalVolume']
        
        return metrics
    
    def _extract_api_metrics(self, data: Dict) -> Dict:
        """Extract metrics from the API endpoint"""
        metrics = {}
        
        if isinstance(data, dict):
            # General API response data
            for key, value in data.items():
                if isinstance(value, (int, float)) and key.lower() in ['volume', 'fees', 'swaps', 'transactions']:
                    metrics[key] = value
        
        return metrics
    
    def _extract_overall_metrics(self, broker_info: Dict) -> Dict:
        """Extract overall metrics from all endpoint data"""
        overall = {
            'total_volume': None,
            'total_fees': None,
            'swap_count': None,
            'last_activity': None,
            'status': None
        }
        
        # Aggregate data from all endpoints
        all_data = []
        for endpoint, data in broker_info['endpoints'].items():
            if data.get('is_json') and data.get('data'):
                all_data.append(data['data'])
        
        # Look for volume across all data
        for data in all_data:
            if isinstance(data, dict):
                # Volume
                if not overall['total_volume']:
                    for field in ['totalVolume', 'volume', 'tvl', 'total_value']:
                        if field in data and data[field]:
                            overall['total_volume'] = data[field]
                            break
                
                # Fees
                if not overall['total_fees']:
                    for field in ['totalFees', 'fees', 'brokerFees', 'affiliateFees']:
                        if field in data and data[field]:
                            overall['total_fees'] = data[field]
                            break
                
                # Swap count
                if not overall['swap_count']:
                    if 'swaps' in data and isinstance(data['swaps'], list):
                        overall['swap_count'] = len(data['swaps'])
                    elif 'totalSwaps' in data:
                        overall['swap_count'] = data['totalSwaps']
        
        return overall
    
    def run_broker_queries(self):
        """Run queries for all brokers"""
        logger.info("🚀 Starting Chainflip broker API queries...")
        
        all_results = []
        
        for broker in self.shapeshift_brokers:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Querying: {broker['name']}")
            logger.info(f"Address: {broker['address']}")
            logger.info(f"{'='*60}")
            
            # Get broker information
            broker_info = self.get_broker_info(broker['address'])
            
            # Analyze the data
            analysis = self.analyze_broker_data(broker_info)
            
            # Add broker metadata
            analysis['broker_name'] = broker['name']
            analysis['broker_address'] = broker['address']
            
            all_results.append({
                'broker_info': broker_info,
                'analysis': analysis
            })
            
            # Display summary
            self._display_broker_summary(analysis)
            
            # Rate limiting between brokers
            time.sleep(2)
        
        # Save results
        self._save_results(all_results)
        
        logger.info("\n✅ Broker queries completed!")
        return all_results
    
    def _display_broker_summary(self, analysis: Dict):
        """Display summary for a single broker"""
        logger.info(f"\n📊 Broker Analysis Summary:")
        logger.info(f"Address: {analysis['address']}")
        logger.info(f"Name: {analysis.get('broker_name', 'N/A')}")
        logger.info(f"Queried at: {analysis['queried_at']}")
        
        if analysis.get('total_volume'):
            logger.info(f"💰 Total Volume: {analysis['total_volume']}")
        if analysis.get('total_fees'):
            logger.info(f"💸 Total Fees: {analysis['total_fees']}")
        if analysis.get('swap_count'):
            logger.info(f"🔄 Swap Count: {analysis['swap_count']}")
        if analysis.get('status'):
            logger.info(f"📊 Status: {analysis['status']}")
        
        # Data summary
        if analysis.get('data_summary'):
            logger.info(f"📋 Data Summary:")
            for endpoint, data in analysis['data_summary'].items():
                if data:
                    logger.info(f"  {endpoint}: {len(data)} fields")
    
    def _save_results(self, results: List[Dict]):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_broker_api_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

def main():
    """Main function"""
    try:
        api_client = ChainflipBrokerAPI()
        results = api_client.run_broker_queries()
        
        print(f"\n🎯 Chainflip Broker API Results:")
        print(f"   Brokers queried: {len(results)}")
        
        if results:
            print(f"   ✅ Successfully queried broker APIs")
            print(f"\n💡 Next steps:")
            print(f"   1. Review the detailed results in the JSON file")
            print(f"   2. Extract accumulated amounts from the API responses")
            print(f"   3. Set up regular monitoring using these endpoints")
        else:
            print(f"   ❌ No broker data retrieved")
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Check if the API endpoints are still accessible")
            print(f"   2. Verify broker addresses are correct")
            print(f"   3. Check for rate limiting or authentication requirements")
        
    except Exception as e:
        logger.error(f"❌ Error running broker API queries: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()


