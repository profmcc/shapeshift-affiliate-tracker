#!/usr/bin/env python3
"""
Chainflip Debug Scraper

Debug version to understand page structure and find full addresses.
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, ElementHandle


class ChainflipDebugScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        
    async def debug_page_structure(self):
        """Debug the page structure to find full addresses."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print(f"Loading: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Navigate to swaps
            await self._click_swaps_tab(page)
            
            # Debug the page structure
            await self._debug_page_structure(page)
            
            await browser.close()
    
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
    
    async def _debug_page_structure(self, page: Page):
        """Debug the page structure."""
        print("\n=== DEBUGGING PAGE STRUCTURE ===")
        
        # Get the first row with addresses
        rows = await page.query_selector_all('table tbody tr')
        if not rows:
            print("No rows found")
            return
        
        first_row = rows[0]
        cells = await first_row.query_selector_all('td')
        
        print(f"Found {len(cells)} cells in first row")
        
        # Focus on the addresses cell (usually cell 1)
        if len(cells) > 1:
            address_cell = cells[1]
            await self._debug_address_cell(address_cell, page)
    
    async def _debug_address_cell(self, cell: ElementHandle, page: Page):
        """Debug the address cell specifically."""
        print("\n=== DEBUGGING ADDRESS CELL ===")
        
        # Get cell text
        cell_text = await cell.inner_text()
        print(f"Cell text: {cell_text}")
        
        # Get cell HTML
        cell_html = await cell.inner_html()
        print(f"Cell HTML: {cell_html[:500]}...")
        
        # Check all attributes
        print("\n--- Checking all attributes ---")
        attributes = ['title', 'data-tooltip', 'data-title', 'aria-label', 'data-original-title']
        for attr in attributes:
            value = await cell.get_attribute(attr)
            if value:
                print(f"{attr}: {value}")
        
        # Check child elements
        print("\n--- Checking child elements ---")
        children = await cell.query_selector_all('*')
        print(f"Found {len(children)} child elements")
        
        for i, child in enumerate(children[:5]):  # Check first 5 children
            tag_name = await child.evaluate('el => el.tagName')
            child_text = await child.inner_text()
            child_html = await child.inner_html()
            
            print(f"\nChild {i+1} ({tag_name}):")
            print(f"  Text: {child_text}")
            print(f"  HTML: {child_html[:200]}...")
            
            # Check child attributes
            for attr in attributes:
                value = await child.get_attribute(attr)
                if value:
                    print(f"  {attr}: {value}")
        
        # Try hovering
        print("\n--- Trying hover ---")
        try:
            await cell.hover()
            await asyncio.sleep(2)
            
            # Look for tooltips
            tooltip_selectors = [
                '.tooltip', '[role="tooltip"]', '.ant-tooltip', '.MuiTooltip-popper',
                '.tooltip-content', '.tooltip-inner', '[class*="tooltip"]',
                '.popover', '.popover-content', '.dropdown-menu'
            ]
            
            for selector in tooltip_selectors:
                tooltip = await page.query_selector(selector)
                if tooltip:
                    tooltip_text = await tooltip.inner_text()
                    print(f"Found tooltip with selector '{selector}': {tooltip_text}")
        except Exception as e:
            print(f"Hover failed: {e}")
        
        # Check for any elements with full addresses
        print("\n--- Searching for full addresses in page ---")
        full_address_elements = await page.query_selector_all('[title*="0x"], [data-tooltip*="0x"]')
        print(f"Found {len(full_address_elements)} elements with 0x in tooltip")
        
        for i, elem in enumerate(full_address_elements[:3]):
            title = await elem.get_attribute('title')
            print(f"Element {i+1}: {title}")


async def main():
    """Main function."""
    url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipDebugScraper(url)
    await scraper.debug_page_structure()


if __name__ == "__main__":
    asyncio.run(main()) 