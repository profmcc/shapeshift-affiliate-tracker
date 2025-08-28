#!/usr/bin/env python3
"""
Chainflip API Discovery
Discovers the actual API endpoints used by the Chainflip scan frontend
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipAPIDiscovery:
    def __init__(self):
        """Initialize the API discovery tool"""
        self.base_url = "https://scan.chainflip.io"
        self.session = requests.Session()
        
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def discover_api_endpoints(self) -> List[str]:
        """Discover API endpoints by analyzing the frontend code"""
        logger.info("🔍 Discovering API endpoints from frontend code...")
        
        discovered_endpoints = []
        
        try:
            # Get the main page to find JavaScript bundles
            response = self.session.get(f"{self.base_url}/brokers", timeout=15)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Look for JavaScript bundle URLs
                js_patterns = [
                    r'/_next/static/chunks/[^"]+\.js',
                    r'/_next/static/js/[^"]+\.js',
                    r'/_next/static/[^"]+\.js'
                ]
                
                for pattern in js_patterns:
                    matches = re.findall(pattern, html_content)
                    for match in matches:
                        js_url = f"{self.base_url}{match}"
                        discovered_endpoints.append(js_url)
                        logger.info(f"📦 Found JS bundle: {js_url}")
                
                # Look for API endpoint patterns in the HTML
                api_patterns = [
                    r'api/[^"\s]+',
                    r'graphql',
                    r'v\d+/[^"\s]+',
                    r'brokers/[^"\s]+',
                    r'swaps/[^"\s]+'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, html_content)
                    for match in matches:
                        if match not in discovered_endpoints:
                            discovered_endpoints.append(match)
                            logger.info(f"🔗 Found API pattern: {match}")
            
        except Exception as e:
            logger.error(f"❌ Error discovering endpoints: {e}")
        
        return discovered_endpoints
    
    def analyze_js_bundles(self, js_urls: List[str]) -> List[str]:
        """Analyze JavaScript bundles to find API endpoints"""
        logger.info("🔍 Analyzing JavaScript bundles for API endpoints...")
        
        api_endpoints = []
        
        for js_url in js_urls[:5]:  # Limit to first 5 to avoid too many requests
            try:
                logger.info(f"📦 Analyzing: {js_url}")
                response = self.session.get(js_url, timeout=15)
                
                if response.status_code == 200:
                    js_content = response.text
                    
                    # Look for API endpoint patterns in JavaScript
                    api_patterns = [
                        r'https?://[^"\s]+/api/[^"\s]+',
                        r'https?://[^"\s]+/v\d+/[^"\s]+',
                        r'https?://[^"\s]+/graphql',
                        r'https?://[^"\s]+/brokers/[^"\s]+',
                        r'https?://[^"\s]+/swaps/[^"\s]+',
                        r'"/api/[^"]+"',
                        r'"/v\d+/[^"]+"',
                        r'"/brokers/[^"]+"',
                        r'"/swaps/[^"]+"'
                    ]
                    
                    for pattern in api_patterns:
                        matches = re.findall(pattern, js_content)
                        for match in matches:
                            # Clean up the match
                            clean_match = match.strip('"\'')
                            if clean_match not in api_endpoints:
                                api_endpoints.append(clean_match)
                                logger.info(f"🔗 Found API endpoint: {clean_match}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {js_url}: {e}")
        
        return api_endpoints
    
    def test_api_endpoints(self, endpoints: List[str]) -> List[Dict]:
        """Test discovered API endpoints"""
        logger.info("🔧 Testing discovered API endpoints...")
        
        test_results = []
        
        for endpoint in endpoints:
            try:
                # Handle relative and absolute URLs
                if endpoint.startswith('http'):
                    test_url = endpoint
                else:
                    test_url = f"{self.base_url}{endpoint}"
                
                logger.info(f"🧪 Testing: {test_url}")
                
                response = self.session.get(test_url, timeout=10)
                
                result = {
                    'endpoint': endpoint,
                    'url': test_url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text),
                    'working': response.status_code == 200
                }
                
                if response.status_code == 200:
                    logger.info(f"✅ {endpoint} - Working")
                    
                    # Try to parse as JSON
                    try:
                        json_data = response.json()
                        result['is_json'] = True
                        result['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                        logger.info(f"   📊 JSON keys: {result['json_keys']}")
                    except:
                        result['is_json'] = False
                        result['is_json'] = False
                        # Look for useful text content
                        text_content = response.text[:200]
                        if 'broker' in text_content.lower() or 'swap' in text_content.lower():
                            result['relevant_content'] = True
                            logger.info(f"   📝 Relevant content found")
                        else:
                            result['relevant_content'] = False
                else:
                    logger.info(f"⚠️ {endpoint} - Status: {response.status_code}")
                
                test_results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {e}")
                test_results.append({
                    'endpoint': endpoint,
                    'url': test_url if 'test_url' in locals() else endpoint,
                    'status_code': None,
                    'error': str(e),
                    'working': False
                })
            
            time.sleep(1)  # Rate limiting
        
        return test_results
    
    def try_common_api_patterns(self) -> List[Dict]:
        """Try common API patterns that might be used"""
        logger.info("🔧 Trying common API patterns...")
        
        common_patterns = [
            "/api/brokers",
            "/api/brokers/{id}",
            "/api/swaps",
            "/api/transactions",
            "/api/v1/brokers",
            "/api/v1/brokers/{id}",
            "/api/v1/swaps",
            "/api/v1/transactions",
            "/v1/brokers",
            "/v1/brokers/{id}",
            "/v1/swaps",
            "/v1/transactions",
            "/graphql",
            "/brokers/{id}/api",
            "/brokers/{id}/data",
            "/brokers/{id}/swaps",
            "/brokers/{id}/transactions"
        ]
        
        test_results = []
        
        for pattern in common_patterns:
            try:
                # Test with a sample broker ID
                test_url = f"{self.base_url}{pattern.replace('{id}', 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi')}"
                logger.info(f"🧪 Testing pattern: {test_url}")
                
                response = self.session.get(test_url, timeout=10)
                
                result = {
                    'pattern': pattern,
                    'url': test_url,
                    'status_code': response.status_code,
                    'working': response.status_code == 200
                }
                
                if response.status_code == 200:
                    logger.info(f"✅ Pattern working: {pattern}")
                    try:
                        json_data = response.json()
                        result['is_json'] = True
                        result['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                    except:
                        result['is_json'] = False
                else:
                    logger.info(f"⚠️ Pattern failed: {pattern} - {response.status_code}")
                
                test_results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Error testing pattern {pattern}: {e}")
                test_results.append({
                    'pattern': pattern,
                    'url': test_url if 'test_url' in locals() else pattern,
                    'status_code': None,
                    'error': str(e),
                    'working': False
                })
            
            time.sleep(1)  # Rate limiting
        
        return test_results
    
    def run_discovery(self):
        """Run the complete API discovery process"""
        logger.info("🚀 Starting Chainflip API discovery...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'discovered_endpoints': [],
            'js_bundle_analysis': [],
            'api_test_results': [],
            'common_pattern_tests': []
        }
        
        # Discover endpoints from frontend code
        discovered_endpoints = self.discover_api_endpoints()
        results['discovered_endpoints'] = discovered_endpoints
        
        # Analyze JavaScript bundles
        js_analysis = self.analyze_js_bundles(discovered_endpoints)
        results['js_bundle_analysis'] = js_analysis
        
        # Test discovered endpoints
        all_endpoints = list(set(discovered_endpoints + js_analysis))
        api_test_results = self.test_api_endpoints(all_endpoints)
        results['api_test_results'] = api_test_results
        
        # Try common API patterns
        common_pattern_tests = self.try_common_api_patterns()
        results['common_pattern_tests'] = common_pattern_tests
        
        # Save results
        self._save_results(results)
        
        # Display summary
        self._display_summary(results)
        
        logger.info("\n✅ API discovery completed!")
        return results
    
    def _save_results(self, results: Dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_api_discovery_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def _display_summary(self, results: Dict):
        """Display summary of discovery results"""
        logger.info(f"\n📊 Chainflip API Discovery Summary:")
        logger.info(f"Timestamp: {results['timestamp']}")
        logger.info(f"Discovered endpoints: {len(results['discovered_endpoints'])}")
        logger.info(f"JS bundle analysis: {len(results['js_bundle_analysis'])}")
        
        # API test results
        working_apis = [api for api in results['api_test_results'] if api.get('working')]
        logger.info(f"Working APIs: {len(working_apis)}/{len(results['api_test_results'])}")
        
        for api in working_apis:
            logger.info(f"  ✅ {api['endpoint']}")
            if api.get('is_json'):
                logger.info(f"     JSON keys: {api.get('json_keys', [])}")
            if api.get('relevant_content'):
                logger.info(f"     Relevant content found")
        
        # Common pattern tests
        working_patterns = [p for p in results['common_pattern_tests'] if p.get('working')]
        logger.info(f"Working patterns: {len(working_patterns)}/{len(results['common_pattern_tests'])}")
        
        for pattern in working_patterns:
            logger.info(f"  ✅ {pattern['pattern']}")
            if pattern.get('is_json'):
                logger.info(f"     JSON keys: {pattern.get('json_keys', [])}")

def main():
    """Main function"""
    try:
        discovery = ChainflipAPIDiscovery()
        results = discovery.run_discovery()
        
        print(f"\n🎯 Chainflip API Discovery Results:")
        print(f"   Discovery completed at: {results['timestamp']}")
        
        working_apis = [api for api in results['api_test_results'] if api.get('working')]
        working_patterns = [p for p in results['common_pattern_tests'] if p.get('working')]
        
        if working_apis or working_patterns:
            print(f"   ✅ Found {len(working_apis)} working APIs and {len(working_patterns)} working patterns")
            print(f"\n💡 Next steps:")
            print(f"   1. Use the working API endpoints to query broker data")
            print(f"   2. Implement data collection using the discovered APIs")
            print(f"   3. Set up regular monitoring of broker balances")
        else:
            print(f"   ❌ No working APIs found")
            print(f"\n💡 Recommendations:")
            print(f"   1. The frontend may use WebSocket or other dynamic loading")
            print(f"   2. Consider using browser automation tools (Selenium)")
            print(f"   3. Check if there are authentication requirements")
        
    except Exception as e:
        logger.error(f"❌ Error running discovery: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()


