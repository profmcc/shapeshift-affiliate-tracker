#!/usr/bin/env python3
"""
Chainflip Final Scraper

Final version that uses multiple techniques to extract full addresses from Chainflip broker pages.
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright, Page, ElementHandle


class ChainflipFinalScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        
    async def scrape_with_full_addresses(self):
        """Scrape the page with full address extraction."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print(f"Loading: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Navigate to swaps
            await self._click_swaps_tab(page)
            
            # Extract data with full addresses
            data = await self._extract_data_with_full_addresses(page)
            
            await browser.close()
            return data
    
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
    
    async def _extract_data_with_full_addresses(self, page: Page):
        """Extract table data with full address extraction."""
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} rows")
        
        data = []
        for i, row in enumerate(rows):
            print(f"\nProcessing row {i+1}/{len(rows)}")
            row_data = await self._extract_row_with_full_addresses(row, page)
            if row_data:
                data.append(row_data)
        
        return data
    
    async def _extract_row_with_full_addresses(self, row: ElementHandle, page: Page):
        """Extract row data with full address extraction."""
        cells = await row.query_selector_all('td')
        row_data = {}
        
        for j, cell in enumerate(cells):
            cell_text = await cell.inner_text()
            
            # Check for abbreviated addresses
            if self._has_abbreviated_address(cell_text):
                print(f"  Cell {j}: Found abbreviated address - {cell_text}")
                
                # Try multiple methods to get full addresses
                full_addresses = await self._get_full_addresses_multiple_methods(cell, page)
                if full_addresses:
                    row_data[f'cell_{j}_full_addresses'] = full_addresses
                    row_data[f'cell_{j}_display'] = cell_text
                    print(f"    ✅ Found {len(full_addresses)} full addresses: {full_addresses}")
                else:
                    row_data[f'cell_{j}'] = cell_text
                    print(f"    ⚠️ No full addresses found")
            else:
                row_data[f'cell_{j}'] = cell_text
        
        return row_data
    
    def _has_abbreviated_address(self, text: str) -> bool:
        """Check if text has abbreviated address."""
        patterns = [
            r'0x[a-fA-F0-9]{4}\.\.\.[a-fA-F0-9]{4}',
            r'bc1q[a-zA-Z0-9]{4}\.\.\.[a-zA-Z0-9]{4}',
            r'[13][a-km-zA-HJ-NP-Z1-9]{4}\.\.\.[a-km-zA-HJ-NP-Z1-9]{4}'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    async def _get_full_addresses_multiple_methods(self, element: ElementHandle, page: Page):
        """Get full addresses using multiple methods."""
        addresses = []
        
        # Method 1: JavaScript injection to get all data attributes
        try:
            js_result = await element.evaluate("""
                (element) => {
                    const addresses = [];
                    
                    // Get all elements with data attributes
                    const allElements = element.querySelectorAll('*');
                    allElements.forEach(el => {
                        // Check all data attributes
                        for (let attr of el.attributes) {
                            if (attr.name.startsWith('data-') && attr.value.includes('0x')) {
                                const matches = attr.value.match(/0x[a-fA-F0-9]{40}/g);
                                if (matches) addresses.push(...matches);
                            }
                        }
                        
                        // Check title attributes
                        if (el.title && el.title.includes('0x')) {
                            const matches = el.title.match(/0x[a-fA-F0-9]{40}/g);
                            if (matches) addresses.push(...matches);
                        }
                    });
                    
                    return addresses;
                }
            """)
            addresses.extend(js_result)
            print(f"      JS method found: {js_result}")
        except Exception as e:
            print(f"      JS method failed: {e}")
        
        # Method 2: Hover and check for tooltips
        try:
            await element.hover()
            await asyncio.sleep(1)
            
            # Look for tooltips
            tooltip_selectors = [
                '.tooltip', '[role="tooltip"]', '.ant-tooltip', '.MuiTooltip-popper',
                '.tooltip-content', '.tooltip-inner', '[class*="tooltip"]'
            ]
            
            for selector in tooltip_selectors:
                tooltip = await page.query_selector(selector)
                if tooltip:
                    tooltip_text = await tooltip.inner_text()
                    matches = re.findall(r'0x[a-fA-F0-9]{40}', tooltip_text)
                    addresses.extend(matches)
                    if matches:
                        print(f"      Tooltip method found: {matches}")
        except Exception as e:
            print(f"      Tooltip method failed: {e}")
        
        # Method 3: Check for hidden elements with full addresses
        try:
            hidden_elements = await element.query_selector_all('[style*="display: none"], [hidden], [aria-hidden="true"]')
            for hidden_elem in hidden_elements:
                hidden_text = await hidden_elem.inner_text()
                matches = re.findall(r'0x[a-fA-F0-9]{40}', hidden_text)
                addresses.extend(matches)
                if matches:
                    print(f"      Hidden elements found: {matches}")
        except Exception as e:
            print(f"      Hidden elements method failed: {e}")
        
        # Method 4: Check for elements with specific classes that might contain full addresses
        try:
            address_elements = await element.query_selector_all('[class*="address"], [class*="hash"], [class*="full"]')
            for addr_elem in address_elements:
                elem_text = await addr_elem.inner_text()
                matches = re.findall(r'0x[a-fA-F0-9]{40}', elem_text)
                addresses.extend(matches)
                if matches:
                    print(f"      Address class elements found: {matches}")
        except Exception as e:
            print(f"      Address class method failed: {e}")
        
        # Remove duplicates and return
        unique_addresses = list(set(addresses))
        return unique_addresses
    
    def save_data(self, data, filename_prefix="chainflip_final"):
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
    
    def analyze_results(self, data):
        """Analyze the scraping results."""
        if not data:
            print("No data to analyze")
            return
        
        print(f"\n=== ANALYSIS ===")
        print(f"Total rows: {len(data)}")
        
        # Count rows with full addresses
        rows_with_addresses = 0
        total_addresses = 0
        
        for row in data:
            for key, value in row.items():
                if key.endswith('_full_addresses') and value:
                    rows_with_addresses += 1
                    total_addresses += len(value)
        
        print(f"Rows with full addresses: {rows_with_addresses}")
        print(f"Total full addresses extracted: {total_addresses}")
        
        # Show sample of extracted addresses
        if total_addresses > 0:
            print(f"\nSample full addresses:")
            for row in data:
                for key, value in row.items():
                    if key.endswith('_full_addresses') and value:
                        print(f"  {key}: {value}")


async def main():
    """Main function."""
    url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipFinalScraper(url)
    data = await scraper.scrape_with_full_addresses()
    
    if data:
        scraper.analyze_results(data)
        scraper.save_data(data)
        print(f"\nExtracted {len(data)} rows")
    else:
        print("No data extracted")


if __name__ == "__main__":
    asyncio.run(main()) 