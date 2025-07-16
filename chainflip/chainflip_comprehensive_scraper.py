#!/usr/bin/env python3
"""
Chainflip Comprehensive Scraper

Implements all requested techniques to extract full 0x addresses:
1. Network interception for API responses
2. Tooltip extraction from UI elements
3. JSON parsing from script tags
4. JavaScript variable extraction
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, ElementHandle, Response


class ChainflipComprehensiveScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.api_responses = []
        self.full_addresses = []
        
    async def scrape_with_full_addresses(self):
        """Main scraping function implementing all extraction techniques."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Set up network interception
            await self._setup_network_interception(page)
            
            print(f"Loading: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Navigate to swaps
            await self._click_swaps_tab(page)
            
            # Wait for data to load
            await page.wait_for_timeout(2000)
            
            # Extract full addresses using all methods
            full_addresses = await self.get_full_addresses(page)
            
            # Extract table data from all pages
            table_data = await self._scrape_all_pages_table_data(page)
            
            # Combine data
            combined_data = self._combine_data_with_addresses(table_data, full_addresses)
            
            await browser.close()
            return combined_data
    
    async def _setup_network_interception(self, page: Page):
        """Set up network response interception to catch API data."""
        print("Setting up network interception...")
        
        async def handle_response(response: Response):
            try:
                url = response.url
                
                # Target Chainflip API endpoints
                if any(keyword in url.lower() for keyword in ['chainflip.io', 'broker', 'swap', 'api']):
                    print(f"🎯 Intercepted: {url}")
                    
                    try:
                        # Try JSON response
                        json_data = await response.json()
                        self.api_responses.append({
                            'url': url,
                            'type': 'json',
                            'data': json_data
                        })
                        print(f"✅ Captured JSON from {url}")
                        
                        # Extract addresses immediately
                        addresses = self._extract_addresses_from_json(json_data)
                        if addresses:
                            print(f"🎉 Found {len(addresses)} addresses: {addresses}")
                            
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
                                print(f"🎉 Found {len(addresses)} addresses in text")
                                
                        except Exception as e:
                            print(f"⚠️ Could not capture response from {url}: {e}")
                            
            except Exception as e:
                print(f"Error handling response: {e}")
        
        page.on('response', handle_response)
    
    async def _click_swaps_tab(self, page: Page):
        """Click the swaps tab."""
        try:
            swaps_button = await page.query_selector('button:has-text("Swaps")')
            if swaps_button:
                await swaps_button.click()
                await page.wait_for_timeout(2000)
                print("Clicked Swaps tab")
        except Exception as e:
            print(f"Error clicking swaps tab: {e}")
    
    async def get_full_addresses(self, page: Page) -> List[str]:
        """Extract full addresses using multiple methods in order."""
        print("\n=== EXTRACTING FULL ADDRESSES ===")
        
        all_addresses = []
        methods_used = []
        
        # Method 1: Network interception (API responses)
        print("\n1. Trying network interception...")
        api_addresses = await self._extract_addresses_from_api_responses()
        if api_addresses:
            all_addresses.extend(api_addresses)
            methods_used.append("network_interception")
            print(f"✅ Network interception found {len(api_addresses)} addresses")
        else:
            print("⚠️ No addresses found in API responses")
        
        # Method 2: Tooltip extraction from UI elements
        print("\n2. Trying tooltip extraction...")
        tooltip_addresses = await self._extract_addresses_from_tooltips(page)
        if tooltip_addresses:
            all_addresses.extend(tooltip_addresses)
            methods_used.append("tooltip_extraction")
            print(f"✅ Tooltip extraction found {len(tooltip_addresses)} addresses")
        else:
            print("⚠️ No addresses found in tooltips")
        
        # Method 3: JSON parsing from script tags
        print("\n3. Trying JSON parsing from script tags...")
        script_addresses = await self._extract_addresses_from_script_tags(page)
        if script_addresses:
            all_addresses.extend(script_addresses)
            methods_used.append("script_parsing")
            print(f"✅ Script parsing found {len(script_addresses)} addresses")
        else:
            print("⚠️ No addresses found in script tags")
        
        # Method 4: JavaScript variable extraction
        print("\n4. Trying JavaScript variable extraction...")
        js_addresses = await self._extract_addresses_from_javascript(page)
        if js_addresses:
            all_addresses.extend(js_addresses)
            methods_used.append("javascript_extraction")
            print(f"✅ JavaScript extraction found {len(js_addresses)} addresses")
        else:
            print("⚠️ No addresses found in JavaScript")
        
        # Remove duplicates and log results
        unique_addresses = list(set(all_addresses))
        print(f"\n=== ADDRESS EXTRACTION SUMMARY ===")
        print(f"Total unique addresses found: {len(unique_addresses)}")
        print(f"Methods used: {', '.join(methods_used) if methods_used else 'None'}")
        
        if unique_addresses:
            print(f"Sample addresses: {unique_addresses[:3]}")
        
        return unique_addresses
    
    async def _extract_addresses_from_api_responses(self) -> List[str]:
        """Extract addresses from captured API responses."""
        addresses = []
        
        for response in self.api_responses:
            try:
                if response['type'] == 'json':
                    addresses.extend(self._extract_addresses_from_json(response['data']))
                elif response['type'] == 'text':
                    addresses.extend(re.findall(r'0x[a-fA-F0-9]{40}', response['data']))
            except Exception as e:
                print(f"Error processing API response: {e}")
        
        return addresses
    
    def _extract_addresses_from_json(self, data: Any) -> List[str]:
        """Recursively extract addresses from JSON data."""
        addresses = []
        
        def search_addresses(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Look for address fields
                    if any(addr_key in key.lower() for addr_key in ['address', 'from', 'to', 'sender', 'recipient']):
                        if isinstance(value, str) and re.match(r'0x[a-fA-F0-9]{40}', value):
                            addresses.append(value)
                    elif isinstance(value, (dict, list)):
                        search_addresses(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_addresses(item)
        
        search_addresses(data)
        return list(set(addresses))
    
    async def _extract_addresses_from_tooltips(self, page: Page) -> List[str]:
        """Extract addresses from tooltips using multiple techniques."""
        addresses = []
        
        try:
            # Get all swap rows
            swap_rows = await page.query_selector_all('.swap-row, table tbody tr')
            print(f"Found {len(swap_rows)} swap rows to inspect")
            
            for i, row in enumerate(swap_rows[:10]):  # Check first 10 rows
                try:
                    # Look for address cells
                    address_cells = await row.query_selector_all('.address-cell, td:nth-child(2)')
                    
                    for cell in address_cells:
                        # Technique 1: Check for tippy props
                        try:
                            tippy_content = await cell.evaluate("""
                                (element) => {
                                    if (element._tippy && element._tippy.props && element._tippy.props.content) {
                                        return element._tippy.props.content;
                                    }
                                    return null;
                                }
                            """)
                            
                            if tippy_content:
                                matches = re.findall(r'0x[a-fA-F0-9]{40}', tippy_content)
                                addresses.extend(matches)
                                print(f"    Found addresses via tippy: {matches}")
                        except Exception as e:
                            pass
                        
                        # Technique 2: Simulate hover and check tooltips
                        try:
                            await cell.hover()
                            await asyncio.sleep(0.5)
                            
                            tooltip_selectors = [
                                '.tooltip', '[role="tooltip"]', '.ant-tooltip', '.MuiTooltip-popper',
                                '.tooltip-content', '.tooltip-inner', '[class*="tooltip"]',
                                '.tippy-box', '.tippy-content'
                            ]
                            
                            for selector in tooltip_selectors:
                                tooltip = await page.query_selector(selector)
                                if tooltip:
                                    tooltip_text = await tooltip.inner_text()
                                    matches = re.findall(r'0x[a-fA-F0-9]{40}', tooltip_text)
                                    if matches:
                                        addresses.extend(matches)
                                        print(f"    Found addresses via hover tooltip: {matches}")
                                        break
                        except Exception as e:
                            pass
                        
                        # Technique 3: Check all attributes
                        try:
                            attributes = ['title', 'data-tooltip', 'data-title', 'aria-label', 'data-original-title']
                            for attr in attributes:
                                value = await cell.get_attribute(attr)
                                if value:
                                    matches = re.findall(r'0x[a-fA-F0-9]{40}', value)
                                    if matches:
                                        addresses.extend(matches)
                                        print(f"    Found addresses via {attr}: {matches}")
                        except Exception as e:
                            pass
                            
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    
        except Exception as e:
            print(f"Error in tooltip extraction: {e}")
        
        return addresses
    
    async def _extract_addresses_from_script_tags(self, page: Page) -> List[str]:
        """Extract addresses from script tags containing JSON data."""
        addresses = []
        
        try:
            # Get all script tags
            script_tags = await page.query_selector_all('script')
            
            for script in script_tags:
                try:
                    script_content = await script.inner_text()
                    
                    # Look for common patterns
                    patterns = [
                        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                        r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                        r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                        r'var\s+initialData\s*=\s*({.*?});',
                        r'const\s+initialData\s*=\s*({.*?});',
                        r'let\s+initialData\s*=\s*({.*?});'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script_content, re.DOTALL)
                        for match in matches:
                            try:
                                json_data = json.loads(match)
                                script_addresses = self._extract_addresses_from_json(json_data)
                                addresses.extend(script_addresses)
                                if script_addresses:
                                    print(f"    Found addresses in script tag: {script_addresses}")
                            except json.JSONDecodeError:
                                # Try to extract addresses directly
                                direct_matches = re.findall(r'0x[a-fA-F0-9]{40}', match)
                                addresses.extend(direct_matches)
                                if direct_matches:
                                    print(f"    Found addresses in script text: {direct_matches}")
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error in script tag extraction: {e}")
        
        return addresses
    
    async def _extract_addresses_from_javascript(self, page: Page) -> List[str]:
        """Extract addresses from JavaScript variables."""
        addresses = []
        
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
                        var_addresses = self._extract_addresses_from_json(value)
                        addresses.extend(var_addresses)
                        if var_addresses:
                            print(f"    Found addresses in {var}: {var_addresses}")
                except:
                    continue
            
            # Search for any objects with address data
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
                    for obj in address_objects:
                        obj_addresses = self._extract_addresses_from_json(obj['data'])
                        addresses.extend(obj_addresses)
                        if obj_addresses:
                            print(f"    Found addresses in {obj['source']}: {obj_addresses}")
                    
            except Exception as e:
                print(f"Error in JavaScript extraction: {e}")
                
        except Exception as e:
            print(f"Error extracting from JavaScript: {e}")
        
        return addresses
    
    async def _extract_table_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract the main table data."""
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} table rows")
        
        data = []
        for i, row in enumerate(rows):
            try:
                cells = await row.query_selector_all('td')
                row_data = {}
                
                for j, cell in enumerate(cells):
                    cell_text = await cell.inner_text()
                    row_data[f'cell_{j}'] = cell_text.strip()
                
                data.append(row_data)
                
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue
        
        return data
    
    def _combine_data_with_addresses(self, table_data: List[Dict[str, Any]], full_addresses: List[str]) -> List[Dict[str, Any]]:
        """Combine table data with extracted full addresses."""
        combined_data = []
        
        for i, row in enumerate(table_data):
            combined_row = row.copy()
            
            # Add full addresses if available
            if i < len(full_addresses):
                combined_row['full_addresses'] = full_addresses[i:i+2]  # Assume 2 addresses per row
            
            combined_data.append(combined_row)
        
        return combined_data
    
    async def _scrape_all_pages_table_data(self, page: Page) -> List[Dict[str, Any]]:
        """Scrape all table rows across all paginated pages using the SVG arrow button."""
        all_data = []
        page_num = 1
        while True:
            print(f"Scraping page {page_num}...")
            rows = await self._extract_table_data(page)
            all_data.extend(rows)
            
            # Find all buttons with an SVG child (pagination arrows)
            arrow_buttons = await page.query_selector_all('button:has(svg)')
            next_button = None
            if len(arrow_buttons) >= 2:
                # Usually: [left arrow, right arrow], so pick the second one
                next_button = arrow_buttons[-1]
            elif len(arrow_buttons) == 1:
                next_button = arrow_buttons[0]
            
            if next_button:
                is_disabled = await next_button.get_attribute('disabled')
                if is_disabled is not None:
                    print("Reached last page.")
                    break
                try:
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_num += 1
                except Exception as e:
                    print(f"Error clicking next page: {e}")
                    break
            else:
                print("No next page arrow button found. Done.")
                break
        print(f"Total rows scraped from all pages: {len(all_data)}")
        return all_data
    
    def save_data(self, data, filename_prefix="chainflip_comprehensive"):
        """Save data to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved JSON: {json_file}")
        
        # Save CSV
        csv_file = f"{filename_prefix}_{timestamp}.csv"
        if data:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            print(f"Saved CSV: {csv_file}")
    
    def analyze_results(self, data, full_addresses):
        """Analyze the scraping results."""
        print(f"\n=== FINAL ANALYSIS ===")
        print(f"Total table rows: {len(data)}")
        print(f"Total full addresses extracted: {len(full_addresses)}")
        
        if full_addresses:
            print(f"Sample full addresses: {full_addresses[:5]}")
        
        # Show sample data
        if data:
            print(f"\nSample table data:")
            sample_row = data[0]
            for key, value in sample_row.items():
                print(f"  {key}: {str(value)[:100]}...")


async def main():
    """Main function."""
    url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipComprehensiveScraper(url)
    data = await scraper.scrape_with_full_addresses()
    
    if data:
        scraper.analyze_results(data, scraper.full_addresses)
        scraper.save_data(data)
        print(f"\nExtracted {len(data)} rows with {len(scraper.full_addresses)} full addresses")
    else:
        print("No data extracted")


if __name__ == "__main__":
    asyncio.run(main())
