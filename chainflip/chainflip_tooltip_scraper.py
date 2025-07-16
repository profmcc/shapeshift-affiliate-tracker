#!/usr/bin/env python3
"""
Chainflip Tooltip Scraper

Focused scraper that extracts full 0x addresses from tooltips on Chainflip broker pages.
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright, Page, ElementHandle


class ChainflipTooltipScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        
    async def scrape_with_tooltips(self):
        """Scrape the page with focus on tooltip extraction."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print(f"Loading: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Navigate to swaps
            await self._click_swaps_tab(page)
            
            # Extract data with tooltips
            data = await self._extract_data_with_tooltips(page)
            
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
    
    async def _extract_data_with_tooltips(self, page: Page):
        """Extract table data with tooltip focus."""
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} rows")
        
        data = []
        for i, row in enumerate(rows[:5]):  # Process first 5 rows for testing
            print(f"\nProcessing row {i+1}")
            row_data = await self._extract_row_with_tooltips(row, page)
            if row_data:
                data.append(row_data)
        
        return data
    
    async def _extract_row_with_tooltips(self, row: ElementHandle, page: Page):
        """Extract row data with tooltip extraction."""
        cells = await row.query_selector_all('td')
        row_data = {}
        
        for j, cell in enumerate(cells):
            cell_text = await cell.inner_text()
            
            # Check for abbreviated addresses
            if self._has_abbreviated_address(cell_text):
                print(f"  Cell {j}: Found abbreviated address - {cell_text}")
                
                # Try to get full address from tooltip
                full_address = await self._get_tooltip_address(cell, page)
                if full_address:
                    row_data[f'cell_{j}_full'] = full_address
                    row_data[f'cell_{j}_display'] = cell_text
                    print(f"    ✅ Found full address: {full_address}")
                else:
                    row_data[f'cell_{j}'] = cell_text
                    print(f"    ⚠️ No tooltip found")
            else:
                row_data[f'cell_{j}'] = cell_text
        
        return row_data
    
    def _has_abbreviated_address(self, text: str) -> bool:
        """Check if text has abbreviated address."""
        return bool(re.search(r'0x[a-fA-F0-9]{4}\.\.\.[a-fA-F0-9]{4}', text))
    
    async def _get_tooltip_address(self, element: ElementHandle, page: Page):
        """Get full address from tooltip."""
        # Method 1: Check title attribute
        title = await element.get_attribute('title')
        if title and re.search(r'0x[a-fA-F0-9]{40}', title):
            return title
        
        # Method 2: Hover and check for tooltip
        try:
            await element.hover()
            await asyncio.sleep(1)
            
            tooltip = await page.query_selector('.tooltip, [role="tooltip"]')
            if tooltip:
                tooltip_text = await tooltip.inner_text()
                if re.search(r'0x[a-fA-F0-9]{40}', tooltip_text):
                    return tooltip_text
        except Exception:
            pass
        
        return None
    
    def save_data(self, data, filename_prefix="chainflip_tooltip"):
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


async def main():
    """Main function."""
    url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipTooltipScraper(url)
    data = await scraper.scrape_with_tooltips()
    
    if data:
        scraper.save_data(data)
        print(f"\nExtracted {len(data)} rows")
    else:
        print("No data extracted")


if __name__ == "__main__":
    asyncio.run(main()) 