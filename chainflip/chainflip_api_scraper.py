#!/usr/bin/env python3
"""
Chainflip API Scraper

Specialized scraper that targets Chainflip's API endpoints and implements
aggressive techniques to extract full 0x addresses from the broker data.
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, ElementHandle, Response


class ChainflipAPIScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.api_responses = []
        self.swap_data = []
        
    async def scrape_with_api_interception(self):
        """Main scraping function with API interception."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Set up targeted network interception
            await self._setup_targeted_interception(page)
            
            print(f"Loading: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Navigate to swaps and wait for data
            await self._navigate_and_wait(page)
            
            # Extract data using multiple techniques
            swap_data = await self._extract_swap_data_comprehensive(page)
            
            await browser.close()
            return swap_data
    
    async def _setup_targeted_interception(self, page: Page):
        """Set up targeted network interception for Chainflip APIs."""
        print("Setting up targeted API interception...")
        
        async def handle_response(response: Response):
            try:
                url = response.url
                
                # Target specific Chainflip API endpoints
                chainflip_patterns = [
                    'chainflip.io/api',
                    'chainflip.io/graphql',
                    'chainflip.io/rest',
                    'chainflip.io/v1',
                    'chainflip.io/v2',
                    'broker',
                    'swap',
                    'transaction'
                ]
                
                # Also capture any JSON responses
                content_type = response.headers.get('content-type', '')
                is_json = 'application/json' in content_type
                
                if any(pattern in url.lower() for pattern in chainflip_patterns) or is_json:
                    print(f"🎯 Intercepted potential API: {url}")
                    
                    try:
                        # Try JSON first
                        json_data = await response.json()
                        self.api_responses.append({
                            'url': url,
                            'type': 'json',
                            'data': json_data
                        })
                        print(f"✅ Captured JSON from {url}")
                        
                        # Immediately try to extract addresses
                        addresses = self._extract_addresses_from_json(json_data)
                        if addresses:
                            print(f"🎉 Found {len(addresses)} addresses in {url}: {addresses}")
                            
                    except:
                        try:
                            # Try text response
                            text_data = await response.text()
                            self.api_responses.append({
                                'url': url,
                                'type': 'text',
                                'data': text_data
                            })
                            print(f"✅ Captured text from {url}")
                            
                            # Extract addresses from text
                            addresses = re.findall(r'0x[a-fA-F0-9]{40}', text_data)
                            if addresses:
                                print(f"🎉 Found {len(addresses)} addresses in text: {addresses}")
                                
                        except Exception as e:
                            print(f"⚠️ Could not capture response from {url}: {e}")
                            
            except Exception as e:
                print(f"Error handling response: {e}")
        
        page.on('response', handle_response)
    
    async def _navigate_and_wait(self, page: Page):
        """Navigate to swaps and wait for data to load."""
        try:
            # Click swaps tab
            swaps_button = await page.query_selector('button:has-text("Swaps")')
            if swaps_button:
                await swaps_button.click()
                print("Clicked Swaps tab")
            
            # Wait for data to load
            await page.wait_for_timeout(3000)
            
            # Try to trigger more data loading
            await self._trigger_data_loading(page)
            
        except Exception as e:
            print(f"Error navigating: {e}")
    
    async def _trigger_data_loading(self, page: Page):
        """Trigger additional data loading to capture more API calls."""
        try:
            # Look for load more buttons
            load_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                '[data-testid="load-more"]',
                '.load-more'
            ]
            
            for selector in load_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        print(f"Clicking load more button: {selector}")
                        await button.click()
                        await page.wait_for_timeout(2000)
                except:
                    continue
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"Error triggering data loading: {e}")
    
    async def _extract_swap_data_comprehensive(self, page: Page) -> List[Dict[str, Any]]:
        """Extract swap data using comprehensive techniques."""
        print("\n=== COMPREHENSIVE DATA EXTRACTION ===")
        
        # Method 1: Extract from API responses
        api_data = await self._extract_from_api_responses()
        
        # Method 2: Extract from table
        table_data = await self._extract_from_table(page)
        
        # Method 3: Extract from page source
        source_data = await self._extract_from_page_source(page)
        
        # Method 4: Extract from JavaScript variables
        js_data = await self._extract_from_javascript(page)
        
        # Combine all data
        combined_data = self._combine_all_data(api_data, table_data, source_data, js_data)
        
        return combined_data
    
    async def _extract_from_api_responses(self) -> List[Dict[str, Any]]:
        """Extract data from captured API responses."""
        print("\n1. Extracting from API responses...")
        data = []
        
        for response in self.api_responses:
            try:
                if response['type'] == 'json':
                    json_data = response['data']
                    extracted = self._extract_swap_objects_from_json(json_data)
                    if extracted:
                        data.extend(extracted)
                        print(f"✅ Extracted {len(extracted)} swap objects from API")
                        
            except Exception as e:
                print(f"Error processing API response: {e}")
        
        return data
    
    def _extract_swap_objects_from_json(self, data: Any) -> List[Dict[str, Any]]:
        """Extract swap objects from JSON data."""
        swaps = []
        
        def search_for_swaps(obj, path=""):
            if isinstance(obj, dict):
                # Look for swap-like objects
                if any(key in str(obj).lower() for key in ['swap', 'transaction', 'broker']):
                    # Check if it has address fields
                    has_addresses = any(
                        any(addr_key in str(value).lower() for addr_key in ['0x', 'address', 'from', 'to'])
                        for value in obj.values()
                    )
                    
                    if has_addresses:
                        swaps.append({
                            'source': f'api_{path}',
                            'data': obj
                        })
                
                # Recursively search
                for key, value in obj.items():
                    search_for_swaps(value, f"{path}.{key}")
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_for_swaps(item, f"{path}[{i}]")
        
        search_for_swaps(data)
        return swaps
    
    async def _extract_from_table(self, page: Page) -> List[Dict[str, Any]]:
        """Extract data from the visible table."""
        print("\n2. Extracting from table...")
        data = []
        
        try:
            rows = await page.query_selector_all('table tbody tr')
            print(f"Found {len(rows)} table rows")
            
            for i, row in enumerate(rows):
                try:
                    cells = await row.query_selector_all('td')
                    row_data = {
                        'source': 'table',
                        'row_index': i,
                        'data': {}
                    }
                    
                    for j, cell in enumerate(cells):
                        cell_text = await cell.inner_text()
                        row_data['data'][f'cell_{j}'] = cell_text.strip()
                    
                    data.append(row_data)
                    
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    
        except Exception as e:
            print(f"Error extracting from table: {e}")
        
        return data
    
    async def _extract_from_page_source(self, page: Page) -> List[Dict[str, Any]]:
        """Extract data from page source and script tags."""
        print("\n3. Extracting from page source...")
        data = []
        
        try:
            # Get page content
            content = await page.content()
            
            # Look for JSON data in script tags
            script_patterns = [
                r'<script[^>]*>.*?window\.__INITIAL_STATE__\s*=\s*({.*?});.*?</script>',
                r'<script[^>]*>.*?window\.__NEXT_DATA__\s*=\s*({.*?});.*?</script>',
                r'<script[^>]*>.*?var\s+initialData\s*=\s*({.*?});.*?</script>',
                r'<script[^>]*>.*?const\s+initialData\s*=\s*({.*?});.*?</script>'
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        json_data = json.loads(match)
                        extracted = self._extract_swap_objects_from_json(json_data)
                        if extracted:
                            data.extend(extracted)
                            print(f"✅ Extracted {len(extracted)} objects from script tag")
                    except json.JSONDecodeError:
                        # Try to extract addresses directly
                        addresses = re.findall(r'0x[a-fA-F0-9]{40}', match)
                        if addresses:
                            data.append({
                                'source': 'script_tag',
                                'addresses': addresses
                            })
                            print(f"✅ Found {len(addresses)} addresses in script tag")
            
            # Look for any JSON-like data in the page
            json_patterns = [
                r'\{[^{}]*"swap"[^{}]*\}',
                r'\{[^{}]*"transaction"[^{}]*\}',
                r'\{[^{}]*"broker"[^{}]*\}'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    try:
                        json_data = json.loads(match)
                        extracted = self._extract_swap_objects_from_json(json_data)
                        if extracted:
                            data.extend(extracted)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error extracting from page source: {e}")
        
        return data
    
    async def _extract_from_javascript(self, page: Page) -> List[Dict[str, Any]]:
        """Extract data from JavaScript variables and objects."""
        print("\n4. Extracting from JavaScript...")
        data = []
        
        try:
            # Try to access common JavaScript variables
            js_variables = [
                'window.__INITIAL_STATE__',
                'window.__NEXT_DATA__',
                'window.__PRELOADED_STATE__',
                'window.initialData',
                'window.swapData',
                'window.brokerData',
                'window.transactionData'
            ]
            
            for var in js_variables:
                try:
                    value = await page.evaluate(f"() => {var}")
                    if value:
                        extracted = self._extract_swap_objects_from_json(value)
                        if extracted:
                            data.extend(extracted)
                            print(f"✅ Extracted from {var}")
                except:
                    continue
            
            # Try to find any objects with address data
            try:
                address_objects = await page.evaluate("""
                    () => {
                        const results = [];
                        
                        // Search window object
                        for (let key in window) {
                            try {
                                const value = window[key];
                                if (typeof value === 'object' && value !== null) {
                                    const jsonStr = JSON.stringify(value);
                                    if (jsonStr.includes('0x') && jsonStr.length > 100) {
                                        results.push({
                                            source: `window.${key}`,
                                            data: value
                                        });
                                    }
                                }
                            } catch (e) {
                                // Ignore errors
                            }
                        }
                        
                        return results;
                    }
                """)
                
                if address_objects:
                    data.extend(address_objects)
                    print(f"✅ Found {len(address_objects)} objects with address data")
                    
            except Exception as e:
                print(f"Error in JavaScript extraction: {e}")
                
        except Exception as e:
            print(f"Error extracting from JavaScript: {e}")
        
        return data
    
    def _combine_all_data(self, api_data, table_data, source_data, js_data) -> List[Dict[str, Any]]:
        """Combine all extracted data sources."""
        print("\n=== COMBINING DATA SOURCES ===")
        
        all_data = []
        
        # Add table data as the primary source
        for item in table_data:
            all_data.append({
                'type': 'table_row',
                'source': item['source'],
                'row_index': item.get('row_index'),
                'swap_details': item['data'].get('cell_0', ''),
                'addresses': item['data'].get('cell_1', ''),
                'status': item['data'].get('cell_2', ''),
                'commission': item['data'].get('cell_3', ''),
                'age': item['data'].get('cell_4', ''),
                'full_addresses': []
            })
        
        # Add API data
        for item in api_data:
            all_data.append({
                'type': 'api_data',
                'source': item['source'],
                'raw_data': item['data']
            })
        
        # Add source data
        for item in source_data:
            all_data.append({
                'type': 'source_data',
                'source': item['source'],
                'raw_data': item.get('data', item.get('addresses', []))
            })
        
        # Add JavaScript data
        for item in js_data:
            all_data.append({
                'type': 'javascript_data',
                'source': item['source'],
                'raw_data': item.get('data', [])
            })
        
        print(f"Combined {len(all_data)} data items from all sources")
        return all_data
    
    def _extract_addresses_from_json(self, data: Any) -> List[str]:
        """Extract all addresses from JSON data."""
        addresses = []
        
        def search_addresses(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and re.match(r'0x[a-fA-F0-9]{40}', value):
                        addresses.append(value)
                    elif isinstance(value, (dict, list)):
                        search_addresses(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_addresses(item)
        
        search_addresses(data)
        return list(set(addresses))
    
    def save_data(self, data, filename_prefix="chainflip_api"):
        """Save data to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved JSON: {json_file}")
        
        # Save CSV (for table data only)
        table_data = [item for item in data if item['type'] == 'table_row']
        if table_data:
            csv_file = f"{filename_prefix}_{timestamp}.csv"
            with open(csv_file, 'w', newline='') as f:
                if table_data:
                    writer = csv.DictWriter(f, fieldnames=table_data[0].keys())
                    writer.writeheader()
                    writer.writerows(table_data)
            print(f"Saved CSV: {csv_file}")
    
    def analyze_results(self, data):
        """Analyze the scraping results."""
        print(f"\n=== FINAL ANALYSIS ===")
        print(f"Total data items: {len(data)}")
        
        # Count by type
        type_counts = {}
        for item in data:
            item_type = item['type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        print(f"Data by type:")
        for item_type, count in type_counts.items():
            print(f"  {item_type}: {count}")
        
        # Show sample data
        if data:
            print(f"\nSample data:")
            sample = data[0]
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")


async def main():
    """Main function."""
    url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipAPIScraper(url)
    data = await scraper.scrape_with_api_interception()
    
    if data:
        scraper.analyze_results(data)
        scraper.save_data(data)
        print(f"\nExtracted {len(data)} data items")
    else:
        print("No data extracted")


if __name__ == "__main__":
    asyncio.run(main()) 