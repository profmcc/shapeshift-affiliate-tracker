#!/usr/bin/env python3
"""
Chainflip Advanced Scraper

Advanced scraper that uses multiple techniques to extract full 0x addresses:
1. Network interception to catch API responses
2. Tooltip extraction from UI elements
3. JSON parsing from script tags
4. Fallback methods for comprehensive address extraction
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, ElementHandle, Response
import base64


class ChainflipAdvancedScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.api_responses = []
        self.full_addresses = []
        
    async def scrape_with_full_addresses(self):
        """Main scraping function with full address extraction."""
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
            
            # Extract full addresses using multiple methods
            full_addresses = await self.get_full_addresses(page)
            
            # Extract table data
            table_data = await self._extract_table_data(page)
            
            # Combine data with full addresses
            combined_data = self._combine_data_with_addresses(table_data, full_addresses)
            
            await browser.close()
            return combined_data
    
    async def _setup_network_interception(self, page: Page):
        """Set up network response interception to catch API data."""
        print("Setting up network interception...")
        
        async def handle_response(response: Response):
            try:
                # Look for API responses that might contain swap data
                url = response.url
                if any(keyword in url.lower() for keyword in ['swap', 'broker', 'transaction', 'api']):
                    print(f"Intercepted API response: {url}")
                    
                    # Try to get JSON response
                    try:
                        json_data = await response.json()
                        self.api_responses.append({
                            'url': url,
                            'data': json_data
                        })
                        print(f"✅ Captured JSON response from {url}")
                    except:
                        # Try to get text response
                        try:
                            text_data = await response.text()
                            self.api_responses.append({
                                'url': url,
                                'data': text_data
                            })
                            print(f"✅ Captured text response from {url}")
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
        
        full_addresses = []
        methods_used = []
        
        # Method 1: Network interception (API responses)
        print("\n1. Trying network interception...")
        api_addresses = await self._extract_addresses_from_api_responses()
        if api_addresses:
            full_addresses.extend(api_addresses)
            methods_used.append("network_interception")
            print(f"✅ Network interception found {len(api_addresses)} addresses")
        else:
            print("⚠️ No addresses found in API responses")
        
        # Method 2: Tooltip extraction from UI elements
        print("\n2. Trying tooltip extraction...")
        tooltip_addresses = await self._extract_addresses_from_tooltips(page)
        if tooltip_addresses:
            full_addresses.extend(tooltip_addresses)
            methods_used.append("tooltip_extraction")
            print(f"✅ Tooltip extraction found {len(tooltip_addresses)} addresses")
        else:
            print("⚠️ No addresses found in tooltips")
        
        # Method 3: JSON parsing from script tags
        print("\n3. Trying JSON parsing from script tags...")
        script_addresses = await self._extract_addresses_from_script_tags(page)
        if script_addresses:
            full_addresses.extend(script_addresses)
            methods_used.append("script_parsing")
            print(f"✅ Script parsing found {len(script_addresses)} addresses")
        else:
            print("⚠️ No addresses found in script tags")
        
        # Method 4: Direct element inspection
        print("\n4. Trying direct element inspection...")
        element_addresses = await self._extract_addresses_from_elements(page)
        if element_addresses:
            full_addresses.extend(element_addresses)
            methods_used.append("element_inspection")
            print(f"✅ Element inspection found {len(element_addresses)} addresses")
        else:
            print("⚠️ No addresses found in elements")
        
        # Remove duplicates and log results
        unique_addresses = list(set(full_addresses))
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
                data = response['data']
                
                # If it's a string, try to parse as JSON
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        # Try to extract addresses from text using regex
                        matches = re.findall(r'0x[a-fA-F0-9]{40}', data)
                        addresses.extend(matches)
                        continue
                
                # If it's JSON, search recursively for addresses
                if isinstance(data, dict):
                    addresses.extend(self._find_addresses_in_json(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            addresses.extend(self._find_addresses_in_json(item))
                            
            except Exception as e:
                print(f"Error processing API response: {e}")
        
        return addresses
    
    def _find_addresses_in_json(self, data: Any) -> List[str]:
        """Recursively find addresses in JSON data."""
        addresses = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Look for common address field names
                if any(addr_key in key.lower() for addr_key in ['address', 'from', 'to', 'sender', 'recipient']):
                    if isinstance(value, str) and re.match(r'0x[a-fA-F0-9]{40}', value):
                        addresses.append(value)
                
                # Recursively search nested objects
                if isinstance(value, (dict, list)):
                    addresses.extend(self._find_addresses_in_json(value))
                    
        elif isinstance(data, list):
            for item in data:
                addresses.extend(self._find_addresses_in_json(item))
        
        return addresses
    
    async def _extract_addresses_from_tooltips(self, page: Page) -> List[str]:
        """Extract addresses from tooltips using multiple techniques."""
        addresses = []
        
        try:
            # Technique 1: Look for .swap-row elements with .address-cell
            swap_rows = await page.query_selector_all('.swap-row')
            if not swap_rows:
                # Try alternative selectors
                swap_rows = await page.query_selector_all('table tbody tr')
            
            print(f"Found {len(swap_rows)} swap rows to inspect")
            
            for i, row in enumerate(swap_rows[:5]):  # Check first 5 rows
                try:
                    # Look for address cells
                    address_cells = await row.query_selector_all('.address-cell, td:nth-child(2)')
                    
                    for cell in address_cells:
                        # Technique 1a: Check for tippy props
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
                        
                        # Technique 1b: Simulate hover and check tooltips
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
                        
                        # Technique 1c: Check all attributes for addresses
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
                        r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
                        r'var\s+initialData\s*=\s*({.*?});',
                        r'const\s+initialData\s*=\s*({.*?});',
                        r'let\s+initialData\s*=\s*({.*?});'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script_content, re.DOTALL)
                        for match in matches:
                            try:
                                json_data = json.loads(match)
                                script_addresses = self._find_addresses_in_json(json_data)
                                addresses.extend(script_addresses)
                                if script_addresses:
                                    print(f"    Found addresses in script tag: {script_addresses}")
                            except json.JSONDecodeError:
                                # Try to extract addresses directly from the text
                                direct_matches = re.findall(r'0x[a-fA-F0-9]{40}', match)
                                addresses.extend(direct_matches)
                                if direct_matches:
                                    print(f"    Found addresses in script text: {direct_matches}")
                    
                    # Also look for base64 encoded data
                    base64_patterns = [
                        r'data:application/json;base64,([A-Za-z0-9+/=]+)',
                        r'"data":"([A-Za-z0-9+/=]+)"'
                    ]
                    
                    for pattern in base64_patterns:
                        matches = re.findall(pattern, script_content)
                        for match in matches:
                            try:
                                decoded = base64.b64decode(match).decode('utf-8')
                                json_data = json.loads(decoded)
                                script_addresses = self._find_addresses_in_json(json_data)
                                addresses.extend(script_addresses)
                                if script_addresses:
                                    print(f"    Found addresses in base64 data: {script_addresses}")
                            except:
                                pass
                                
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error in script tag extraction: {e}")
        
        return addresses
    
    async def _extract_addresses_from_elements(self, page: Page) -> List[str]:
        """Extract addresses by inspecting all elements on the page."""
        addresses = []
        
        try:
            # Look for elements with address-related classes or IDs
            address_selectors = [
                '[class*="address"]', '[class*="hash"]', '[class*="full"]',
                '[id*="address"]', '[id*="hash"]', '[id*="full"]',
                '[data-address]', '[data-hash]', '[data-full]'
            ]
            
            for selector in address_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Check inner text
                        text = await element.inner_text()
                        matches = re.findall(r'0x[a-fA-F0-9]{40}', text)
                        addresses.extend(matches)
                        
                        # Check all attributes
                        attributes = ['title', 'data-tooltip', 'data-title', 'aria-label', 'data-original-title']
                        for attr in attributes:
                            value = await element.get_attribute(attr)
                            if value:
                                matches = re.findall(r'0x[a-fA-F0-9]{40}', value)
                                addresses.extend(matches)
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error in element inspection: {e}")
        
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
    
    def save_data(self, data, filename_prefix="chainflip_advanced"):
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
    
    scraper = ChainflipAdvancedScraper(url)
    data = await scraper.scrape_with_full_addresses()
    
    if data:
        scraper.analyze_results(data, scraper.full_addresses)
        scraper.save_data(data)
        print(f"\nExtracted {len(data)} rows with {len(scraper.full_addresses)} full addresses")
    else:
        print("No data extracted")


if __name__ == "__main__":
    asyncio.run(main()) 