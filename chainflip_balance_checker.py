#!/usr/bin/env python3
"""
Comprehensive Chainflip Balance Checker
Tries multiple approaches to query Chainflip broker information and accumulated amounts
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipBalanceChecker:
    def __init__(self):
        """Initialize the Chainflip balance checker"""
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
        
        # Multiple API endpoints to try
        self.api_endpoints = [
            "https://api.chainflip.io",
            "https://chainflip.io/api",
            "https://api.chainflip.network",
            "https://chainflip.network/api"
        ]
        
        # Alternative data sources
        self.alternative_sources = [
            "https://scan.chainflip.io",
            "https://explorer.chainflip.io",
            "https://chainflip.io/explorer"
        ]
    
    def check_chainflip_scan(self, broker_address: str) -> Optional[Dict]:
        """Check Chainflip scan/explorer for broker information"""
        try:
            logger.info(f"🔍 Checking Chainflip scan for broker: {broker_address}")
            
            # Try the scan endpoint
            scan_url = f"https://scan.chainflip.io/brokers/{broker_address}"
            response = requests.get(scan_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Found broker page at scan.chainflip.io")
                # This would be an HTML page, we'd need to parse it
                return {
                    'source': 'scan.chainflip.io',
                    'url': scan_url,
                    'status': 'found',
                    'content_length': len(response.text)
                }
            else:
                logger.warning(f"⚠️ Scan endpoint returned: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking scan: {e}")
            return None
    
    def check_chainflip_explorer(self, broker_address: str) -> Optional[Dict]:
        """Check Chainflip explorer for broker information"""
        try:
            logger.info(f"🔍 Checking Chainflip explorer for broker: {broker_address}")
            
            # Try the explorer endpoint
            explorer_url = f"https://explorer.chainflip.io/broker/{broker_address}"
            response = requests.get(explorer_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Found broker page at explorer.chainflip.io")
                return {
                    'source': 'explorer.chainflip.io',
                    'url': explorer_url,
                    'status': 'found',
                    'content_length': len(response.text)
                }
            else:
                logger.warning(f"⚠️ Explorer endpoint returned: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking explorer: {e}")
            return None
    
    def check_chainflip_website(self, broker_address: str) -> Optional[Dict]:
        """Check Chainflip main website for broker information"""
        try:
            logger.info(f"🔍 Checking Chainflip website for broker: {broker_address}")
            
            # Try the main website
            website_url = f"https://chainflip.io/broker/{broker_address}"
            response = requests.get(website_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Found broker page at chainflip.io")
                return {
                    'source': 'chainflip.io',
                    'url': website_url,
                    'status': 'found',
                    'content_length': len(response.text)
                }
            else:
                logger.warning(f"⚠️ Website endpoint returned: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking website: {e}")
            return None
    
    def check_public_apis(self) -> List[Dict]:
        """Check various public APIs for Chainflip data"""
        logger.info("🔧 Checking public APIs for Chainflip data...")
        
        api_results = []
        
        # Try different API patterns
        api_patterns = [
            "https://api.chainflip.io/health",
            "https://api.chainflip.io/status",
            "https://api.chainflip.io/brokers",
            "https://api.chainflip.io/swaps",
            "https://api.chainflip.io/transactions",
            "https://chainflip.io/api/health",
            "https://chainflip.io/api/status",
            "https://chainflip.io/api/brokers",
            "https://chainflip.io/api/swaps",
            "https://chainflip.io/api/transactions"
        ]
        
        for api_url in api_patterns:
            try:
                response = requests.get(api_url, timeout=10)
                api_results.append({
                    'url': api_url,
                    'status_code': response.status_code,
                    'working': response.status_code == 200
                })
                
                if response.status_code == 200:
                    logger.info(f"✅ {api_url} - Working")
                else:
                    logger.info(f"⚠️ {api_url} - Status: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ {api_url} - Error: {e}")
                api_results.append({
                    'url': api_url,
                    'status_code': None,
                    'working': False,
                    'error': str(e)
                })
        
        return api_results
    
    def check_github_repos(self) -> List[Dict]:
        """Check GitHub repositories for Chainflip API information"""
        logger.info("🔧 Checking GitHub repositories for Chainflip API info...")
        
        github_repos = [
            "https://api.github.com/repos/chainflip-io/chainflip-mainnet-apis",
            "https://api.github.com/repos/chainflip-io/chainflip",
            "https://api.github.com/repos/chainflip-io/chainflip-indexer"
        ]
        
        repo_results = []
        
        for repo_url in github_repos:
            try:
                response = requests.get(repo_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    repo_results.append({
                        'name': data.get('name', 'Unknown'),
                        'description': data.get('description', 'No description'),
                        'url': data.get('html_url', repo_url),
                        'stars': data.get('stargazers_count', 0),
                        'last_updated': data.get('updated_at', 'Unknown')
                    })
                    logger.info(f"✅ Found repo: {data.get('name', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ Repo check failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking repo {repo_url}: {e}")
        
        return repo_results
    
    def check_alternative_data_sources(self) -> List[Dict]:
        """Check alternative data sources for Chainflip information"""
        logger.info("🔧 Checking alternative data sources...")
        
        sources = [
            "https://defillama.com/protocol/chainflip",
            "https://dexscreener.com/chainflip",
            "https://dune.com/projects/chainflip"
        ]
        
        source_results = []
        
        for source_url in sources:
            try:
                response = requests.get(source_url, timeout=10)
                source_results.append({
                    'url': source_url,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200
                })
                
                if response.status_code == 200:
                    logger.info(f"✅ {source_url} - Accessible")
                else:
                    logger.info(f"⚠️ {source_url} - Status: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking {source_url}: {e}")
                source_results.append({
                    'url': source_url,
                    'status_code': None,
                    'accessible': False,
                    'error': str(e)
                })
        
        return source_results
    
    def run_comprehensive_check(self):
        """Run comprehensive check using all available methods"""
        logger.info("🚀 Starting comprehensive Chainflip balance check...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'brokers': [],
            'api_status': [],
            'github_repos': [],
            'alternative_sources': [],
            'scan_results': [],
            'explorer_results': [],
            'website_results': []
        }
        
        # Check each broker
        for broker in self.shapeshift_brokers:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Checking broker: {broker['name']}")
            logger.info(f"Address: {broker['address']}")
            logger.info(f"{'='*60}")
            
            broker_result = {
                'name': broker['name'],
                'address': broker['address'],
                'scan_result': None,
                'explorer_result': None,
                'website_result': None
            }
            
            # Check scan
            scan_result = self.check_chainflip_scan(broker['address'])
            if scan_result:
                broker_result['scan_result'] = scan_result
                results['scan_results'].append(scan_result)
            
            # Check explorer
            explorer_result = self.check_chainflip_explorer(broker['address'])
            if explorer_result:
                broker_result['explorer_result'] = explorer_result
                results['explorer_results'].append(explorer_result)
            
            # Check website
            website_result = self.check_chainflip_website(broker['address'])
            if website_result:
                broker_result['website_result'] = website_result
                results['website_results'].append(website_result)
            
            results['brokers'].append(broker_result)
            
            # Rate limiting
            time.sleep(2)
        
        # Check public APIs
        results['api_status'] = self.check_public_apis()
        
        # Check GitHub repositories
        results['github_repos'] = self.check_github_repos()
        
        # Check alternative data sources
        results['alternative_sources'] = self.check_alternative_data_sources()
        
        # Save results
        self._save_results(results)
        
        # Display summary
        self._display_summary(results)
        
        logger.info("\n✅ Comprehensive check completed!")
        return results
    
    def _save_results(self, results: Dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_comprehensive_check_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def _display_summary(self, results: Dict):
        """Display summary of results"""
        logger.info(f"\n📊 Chainflip Balance Check Summary:")
        logger.info(f"Timestamp: {results['timestamp']}")
        logger.info(f"Brokers checked: {len(results['brokers'])}")
        
        # Broker summary
        for broker in results['brokers']:
            logger.info(f"\n🔍 {broker['name']}:")
            logger.info(f"  Address: {broker['address']}")
            
            if broker['scan_result']:
                logger.info(f"  ✅ Scan: {broker['scan_result']['source']}")
            else:
                logger.info(f"  ❌ Scan: Not accessible")
            
            if broker['explorer_result']:
                logger.info(f"  ✅ Explorer: {broker['explorer_result']['source']}")
            else:
                logger.info(f"  ❌ Explorer: Not accessible")
            
            if broker['website_result']:
                logger.info(f"  ✅ Website: {broker['website_result']['source']}")
            else:
                logger.info(f"  ❌ Website: Not accessible")
        
        # API summary
        working_apis = [api for api in results['api_status'] if api.get('working')]
        logger.info(f"\n📡 API Status: {len(working_apis)}/{len(results['api_status'])} working")
        
        # GitHub summary
        if results['github_repos']:
            logger.info(f"\n📚 GitHub Repositories: {len(results['github_repos'])} found")
            for repo in results['github_repos']:
                logger.info(f"  📖 {repo['name']}: {repo['description']}")
                logger.info(f"     Stars: {repo['stars']}, Updated: {repo['last_updated']}")
        
        # Alternative sources summary
        accessible_sources = [src for src in results['alternative_sources'] if src.get('accessible')]
        logger.info(f"\n🌐 Alternative Sources: {len(accessible_sources)}/{len(results['alternative_sources'])} accessible")

def main():
    """Main function"""
    checker = ChainflipBalanceChecker()
    results = checker.run_comprehensive_check()
    
    print(f"\n🎯 Chainflip Balance Check Results:")
    print(f"   Check completed at: {results['timestamp']}")
    print(f"   Brokers checked: {len(results['brokers'])}")
    
    # Check if we found any accessible sources
    accessible_sources = []
    for broker in results['brokers']:
        if broker.get('scan_result') or broker.get('explorer_result') or broker.get('website_result'):
            accessible_sources.append(broker['name'])
    
    if accessible_sources:
        print(f"   ✅ Accessible sources found for: {', '.join(accessible_sources)}")
        print(f"\n💡 Next steps:")
        print(f"   1. Visit the accessible URLs to manually check broker balances")
        print(f"   2. Consider setting up local Chainflip API server")
        print(f"   3. Monitor these sources for regular balance updates")
    else:
        print(f"   ❌ No accessible sources found")
        print(f"\n💡 Recommendations:")
        print(f"   1. Set up local Chainflip API server using Docker")
        print(f"   2. Check if Chainflip has changed their API endpoints")
        print(f"   3. Contact Chainflip team for API access")

if __name__ == "__main__":
    main()


