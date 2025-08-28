#!/usr/bin/env python3
"""
Chainflip Scan Scraper
Scrapes broker information from scan.chainflip.io to get accumulated amounts
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipScanScraper:
    def __init__(self):
        """Initialize the Chainflip scan scraper"""
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
    
    def get_broker_page(self, broker_address: str) -> Optional[str]:
        """Get the broker page HTML content"""
        try:
            url = f"{self.base_url}/brokers/{broker_address}"
            logger.info(f"🔍 Fetching broker page: {url}")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully fetched broker page for {broker_address}")
                return response.text
            else:
                logger.warning(f"⚠️ Failed to fetch broker page: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching broker page: {e}")
            return None
    
    def parse_broker_page(self, html_content: str, broker_address: str) -> Optional[Dict]:
        """Parse the broker page HTML to extract information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            broker_info = {
                'address': broker_address,
                'scraped_at': datetime.now().isoformat(),
                'page_title': '',
                'broker_name': '',
                'total_volume': '',
                'total_fees': '',
                'swap_count': '',
                'last_activity': '',
                'status': '',
                'raw_html': html_content[:1000] + '...' if len(html_content) > 1000 else html_content
            }
            
            # Extract page title
            title_tag = soup.find('title')
            if title_tag:
                broker_info['page_title'] = title_tag.get_text().strip()
                logger.info(f"📄 Page title: {broker_info['page_title']}")
            
            # Look for broker name
            name_selectors = [
                'h1', 'h2', 'h3', '.broker-name', '.name', '.title',
                '[data-testid="broker-name"]', '[class*="name"]', '[class*="title"]'
            ]
            
            for selector in name_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) < 100:  # Reasonable name length
                        broker_info['broker_name'] = text
                        logger.info(f"🏷️ Broker name: {text}")
                        break
                if broker_info['broker_name']:
                    break
            
            # Look for volume information
            volume_patterns = [
                r'total.*volume.*?([\d,]+\.?\d*)',
                r'volume.*?([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*).*volume',
                r'([\d,]+\.?\d*).*tvl',
                r'tvl.*?([\d,]+\.?\d*)'
            ]
            
            page_text = soup.get_text().lower()
            for pattern in volume_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    broker_info['total_volume'] = matches[0]
                    logger.info(f"💰 Total volume: {matches[0]}")
                    break
            
            # Look for fee information
            fee_patterns = [
                r'total.*fee.*?([\d,]+\.?\d*)',
                r'fee.*?([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*).*fee',
                r'broker.*fee.*?([\d,]+\.?\d*)'
            ]
            
            for pattern in fee_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    broker_info['total_fees'] = matches[0]
                    logger.info(f"💸 Total fees: {matches[0]}")
                    break
            
            # Look for swap count
            swap_patterns = [
                r'(\d+).*swap',
                r'swap.*(\d+)',
                r'total.*swap.*(\d+)',
                r'(\d+).*transaction'
            ]
            
            for pattern in swap_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    broker_info['swap_count'] = matches[0]
                    logger.info(f"🔄 Swap count: {matches[0]}")
                    break
            
            # Look for status information
            status_indicators = ['active', 'inactive', 'suspended', 'verified', 'unverified']
            for status in status_indicators:
                if status in page_text:
                    broker_info['status'] = status
                    logger.info(f"📊 Status: {status}")
                    break
            
            # Look for last activity
            activity_patterns = [
                r'last.*activity.*?(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2}).*last',
                r'updated.*?(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2}).*updated'
            ]
            
            for pattern in activity_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    broker_info['last_activity'] = matches[0]
                    logger.info(f"🕒 Last activity: {matches[0]}")
                    break
            
            return broker_info
            
        except Exception as e:
            logger.error(f"❌ Error parsing broker page: {e}")
            return None
    
    def extract_structured_data(self, html_content: str) -> Optional[Dict]:
        """Try to extract structured data from the page"""
        try:
            # Look for JSON-LD structured data
            soup = BeautifulSoup(html_content, 'html.parser')
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Organization':
                        logger.info("✅ Found structured data")
                        return data
                except json.JSONDecodeError:
                    continue
            
            # Look for other JSON data in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'broker' in script.string.lower():
                    # Try to extract JSON-like data
                    json_matches = re.findall(r'\{[^}]*"broker"[^}]*\}', script.string)
                    if json_matches:
                        logger.info("✅ Found broker-related JSON data")
                        return {'raw_json': json_matches[0]}
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting structured data: {e}")
            return None
    
    def scrape_broker_info(self, broker_address: str) -> Optional[Dict]:
        """Scrape comprehensive broker information"""
        try:
            logger.info(f"🔍 Scraping broker: {broker_address}")
            
            # Get the broker page
            html_content = self.get_broker_page(broker_address)
            if not html_content:
                return None
            
            # Parse the page content
            broker_info = self.parse_broker_page(html_content, broker_address)
            if not broker_info:
                return None
            
            # Try to extract structured data
            structured_data = self.extract_structured_data(html_content)
            if structured_data:
                broker_info['structured_data'] = structured_data
            
            return broker_info
            
        except Exception as e:
            logger.error(f"❌ Error scraping broker {broker_address}: {e}")
            return None
    
    def run_scraping(self):
        """Run the scraping for all brokers"""
        logger.info("🚀 Starting Chainflip broker scraping...")
        
        all_results = []
        
        for broker in self.shapeshift_brokers:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Scraping: {broker['name']}")
            logger.info(f"Address: {broker['address']}")
            logger.info(f"{'='*60}")
            
            broker_result = self.scrape_broker_info(broker['address'])
            
            if broker_result:
                broker_result['broker_name_from_config'] = broker['name']
                all_results.append(broker_result)
                logger.info(f"✅ Successfully scraped {broker['name']}")
            else:
                logger.warning(f"⚠️ Failed to scrape {broker['name']}")
            
            # Rate limiting
            time.sleep(3)
        
        # Save results
        self._save_results(all_results)
        
        # Display summary
        self._display_summary(all_results)
        
        logger.info("\n✅ Scraping completed!")
        return all_results
    
    def _save_results(self, results: List[Dict]):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_broker_scraping_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
    
    def _display_summary(self, results: List[Dict]):
        """Display summary of scraping results"""
        logger.info(f"\n📊 Chainflip Broker Scraping Summary:")
        logger.info(f"Brokers scraped: {len(results)}")
        
        for result in results:
            logger.info(f"\n🔍 {result.get('broker_name_from_config', 'Unknown Broker')}:")
            logger.info(f"  Address: {result.get('address', 'N/A')}")
            logger.info(f"  Page Title: {result.get('page_title', 'N/A')}")
            logger.info(f"  Broker Name: {result.get('broker_name', 'N/A')}")
            logger.info(f"  Total Volume: {result.get('total_volume', 'N/A')}")
            logger.info(f"  Total Fees: {result.get('total_fees', 'N/A')}")
            logger.info(f"  Swap Count: {result.get('swap_count', 'N/A')}")
            logger.info(f"  Status: {result.get('status', 'N/A')}")
            logger.info(f"  Last Activity: {result.get('last_activity', 'N/A')}")
            
            if result.get('structured_data'):
                logger.info(f"  ✅ Structured data found")

def main():
    """Main function"""
    try:
        scraper = ChainflipScanScraper()
        results = scraper.run_scraping()
        
        print(f"\n🎯 Chainflip Broker Scraping Results:")
        print(f"   Brokers scraped: {len(results)}")
        
        if results:
            print(f"   ✅ Successfully scraped broker information")
            print(f"\n💡 Next steps:")
            print(f"   1. Review the scraped data in the JSON file")
            print(f"   2. Extract accumulated amounts from the data")
            print(f"   3. Set up regular scraping for monitoring")
        else:
            print(f"   ❌ No broker information scraped")
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Check if scan.chainflip.io is still accessible")
            print(f"   2. Verify broker addresses are correct")
            print(f"   3. Check for rate limiting or blocking")
        
    except Exception as e:
        logger.error(f"❌ Error running scraper: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()


