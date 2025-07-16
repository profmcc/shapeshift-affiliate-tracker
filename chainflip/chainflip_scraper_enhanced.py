#!/usr/bin/env python3
"""
Enhanced Chainflip Broker Swaps Table Scraper

Advanced scraper that handles various table structures and extracts full 0x addresses
from tooltips, hover states, and other UI elements.
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, ElementHandle
from bs4 import BeautifulSoup
import pandas as pd


class EnhancedChainflipScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.swaps_data = []
        
    async def scrape_swaps_table(self) -> List[Dict[str, Any]]:
        """Scrape the swaps table from the Chainflip broker page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for production
            page = await browser.new_page()
            
            # Set viewport for better rendering
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            print(f"Loading page: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Try to find and navigate to swaps section
            await self._navigate_to_swaps_section(page)
            
            # Wait for table to load
            await self._wait_for_table(page)
            
            # Load all available data
            await self._load_all_data(page)
            
            # Extract table data
            swaps = await self._extract_table_data(page)
            
            await browser.close()
            return swaps
    
    async def _navigate_to_swaps_section(self, page: Page):
        """Navigate to the swaps section if needed."""
        try:
            # Look for tabs or navigation elements
            tab_selectors = [
                'button:has-text("Swaps")',
                'a:has-text("Swaps")',
                '[data-testid="swaps-tab"]',
                '.tab:has-text("Swaps")',
                'nav a:has-text("Swaps")'
            ]
            
            for selector in tab_selectors:
                try:
                    tab = await page.query_selector(selector)
                    if tab and await tab.is_visible():
                        print(f"Found swaps tab with selector: {selector}")
                        await tab.click()
                        await page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error navigating to swaps section: {e}")
    
    async def _wait_for_table(self, page: Page):
        """Wait for table to load with various selectors."""
        table_selectors = [
            'table',
            '[data-testid="swaps-table"]',
            '.swaps-table',
            '.table',
            'div[role="table"]'
        ]
        
        for selector in table_selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                print(f"Found table with selector: {selector}")
                break
            except Exception:
                continue
    
    async def _load_all_data(self, page: Page):
        """Load all available data by clicking pagination or load more buttons."""
        try:
            # Look for various load more patterns
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                'button:has-text("Load")',
                '[data-testid="load-more"]',
                '.load-more',
                '.pagination button:last-child',
                'button[aria-label*="load"]',
                'button[aria-label*="more"]'
            ]
            
            max_attempts = 10
            attempts = 0
            
            while attempts < max_attempts:
                loaded_more = False
                
                for selector in load_more_selectors:
                    try:
                        load_more_button = await page.query_selector(selector)
                        if load_more_button and await load_more_button.is_visible():
                            print(f"Loading more data with selector: {selector}")
                            await load_more_button.click()
                            await page.wait_for_timeout(3000)
                            loaded_more = True
                            break
                    except Exception as e:
                        continue
                
                if not loaded_more:
                    break
                    
                attempts += 1
                
        except Exception as e:
            print(f"Error loading additional data: {e}")
    
    async def _extract_table_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract data from table with enhanced address detection."""
        swaps = []
        
        # Try different table selectors
        table_selectors = [
            'table tbody tr',
            '[data-testid="swaps-table"] tbody tr',
            '.swaps-table tbody tr',
            '.table tbody tr',
            'div[role="table"] div[role="row"]'
        ]
        
        rows = []
        for selector in table_selectors:
            rows = await page.query_selector_all(selector)
            if rows:
                print(f"Found {len(rows)} rows with selector: {selector}")
                break
        
        if not rows:
            print("No table rows found")
            return swaps
        
        # Get header information for better column identification
        headers = await self._get_table_headers(page)
        
        for i, row in enumerate(rows):
            try:
                # Extract row data with enhanced address detection
                row_data = await self._extract_row_data(row, headers)
                
                if row_data:
                    swaps.append(row_data)
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1} rows...")
                    
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue
        
        return swaps
    
    async def _get_table_headers(self, page: Page) -> List[str]:
        """Extract table headers for better column identification."""
        headers = []
        
        header_selectors = [
            'table thead th',
            'table thead tr th',
            '[data-testid="swaps-table"] thead th',
            '.table thead th'
        ]
        
        for selector in header_selectors:
            try:
                header_elements = await page.query_selector_all(selector)
                if header_elements:
                    for header in header_elements:
                        text = await header.inner_text()
                        if text.strip():
                            headers.append(text.strip())
                    break
            except Exception:
                continue
        
        print(f"Found headers: {headers}")
        return headers
    
    async def _extract_row_data(self, row: ElementHandle, headers: List[str]) -> Dict[str, Any]:
        """Extract data from a single row with enhanced address detection."""
        row_data = {}
        
        # Get all cells
        cells = await row.query_selector_all('td, th')
        if len(cells) < 2:
            return {}
        
        for j, cell in enumerate(cells):
            try:
                cell_text = await cell.inner_text()
                cell_html = await cell.inner_html()
                
                # Enhanced address detection
                address_info = await self._extract_address_info(cell)
                
                if address_info:
                    # Use header name if available, otherwise use generic name
                    column_name = headers[j] if j < len(headers) else f'column_{j}'
                    row_data[f'{column_name}_full_address'] = address_info['full_address']
                    row_data[f'{column_name}_display'] = address_info['display']
                    row_data[f'{column_name}_type'] = address_info['type']
                else:
                    column_name = headers[j] if j < len(headers) else f'column_{j}'
                    row_data[column_name] = cell_text.strip()
                
            except Exception as e:
                print(f"Error extracting cell {j}: {e}")
                continue
        
        return row_data
    
    async def _extract_address_info(self, element: ElementHandle) -> Optional[Dict[str, str]]:
        """Extract full address information from an element."""
        try:
            # Get the display text
            display_text = await element.inner_text()
            
            # Check if this looks like an abbreviated address
            if not ('0x' in display_text and len(display_text) < 42):
                return None
            
            # Try multiple methods to get the full address
            full_address = None
            
            # Method 1: Check title attribute
            title = await element.get_attribute('title')
            if title and '0x' in title and len(title) >= 42:
                full_address = title.strip()
            
            # Method 2: Check other tooltip attributes
            if not full_address:
                tooltip_attrs = ['data-tooltip', 'data-title', 'aria-label', 'data-original-title']
                for attr in tooltip_attrs:
                    value = await element.get_attribute(attr)
                    if value and '0x' in value and len(value) >= 42:
                        full_address = value.strip()
                        break
            
            # Method 3: Look for child elements with tooltips
            if not full_address:
                tooltip_selectors = [
                    '[title*="0x"]',
                    '[data-tooltip*="0x"]',
                    '[data-title*="0x"]',
                    '.tooltip[title*="0x"]',
                    'span[title*="0x"]'
                ]
                
                for selector in tooltip_selectors:
                    tooltip_elements = await element.query_selector_all(selector)
                    for tooltip_elem in tooltip_elements:
                        title = await tooltip_elem.get_attribute('title')
                        if title and '0x' in title and len(title) >= 42:
                            full_address = title.strip()
                            break
                    if full_address:
                        break
            
            # Method 4: Hover and check for dynamic tooltips
            if not full_address:
                try:
                    await element.hover()
                    await asyncio.sleep(0.5)
                    
                    # Look for tooltip that appeared
                    tooltip = await element.page.query_selector('.tooltip, [role="tooltip"], .ant-tooltip')
                    if tooltip:
                        tooltip_text = await tooltip.inner_text()
                        if '0x' in tooltip_text and len(tooltip_text) >= 42:
                            full_address = tooltip_text.strip()
                except Exception:
                    pass
            
            if full_address:
                # Determine address type based on context
                address_type = self._determine_address_type(display_text, full_address)
                
                return {
                    'full_address': full_address,
                    'display': display_text.strip(),
                    'type': address_type
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting address info: {e}")
            return None
    
    def _determine_address_type(self, display_text: str, full_address: str) -> str:
        """Determine the type of address based on context."""
        display_lower = display_text.lower()
        full_lower = full_address.lower()
        
        if 'tx' in display_lower or 'hash' in display_lower:
            return 'transaction_hash'
        elif 'from' in display_lower or 'sender' in display_lower:
            return 'from_address'
        elif 'to' in display_lower or 'recipient' in display_lower:
            return 'to_address'
        elif 'contract' in display_lower:
            return 'contract_address'
        else:
            return 'address'
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """Save scraped data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_swaps_enhanced_{timestamp}.csv"
        
        if not data:
            print("No data to save")
            return
        
        # Get all unique keys from all rows
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = sorted(all_keys)
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Fill missing values with empty strings
                row_with_all_fields = {key: row.get(key, '') for key in fieldnames}
                writer.writerow(row_with_all_fields)
        
        print(f"Saved {len(data)} swaps to {filename}")
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None):
        """Save scraped data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_swaps_enhanced_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(data)} swaps to {filename}")
    
    def analyze_data(self, data: List[Dict[str, Any]]):
        """Analyze the scraped data and provide insights."""
        if not data:
            print("No data to analyze")
            return
        
        print(f"\n=== Data Analysis ===")
        print(f"Total swaps: {len(data)}")
        
        # Count address types
        address_types = {}
        for row in data:
            for key, value in row.items():
                if key.endswith('_type') and value:
                    address_types[value] = address_types.get(value, 0) + 1
        
        if address_types:
            print(f"\nAddress types found:")
            for addr_type, count in address_types.items():
                print(f"  {addr_type}: {count}")
        
        # Show sample data
        print(f"\nSample data structure:")
        sample_row = data[0]
        for key, value in sample_row.items():
            print(f"  {key}: {value}")


async def main():
    """Main function to run the enhanced scraper."""
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = EnhancedChainflipScraper(broker_url)
    
    print("Starting Enhanced Chainflip swaps table scraper...")
    print(f"Target URL: {broker_url}")
    
    try:
        swaps_data = await scraper.scrape_swaps_table()
        
        if swaps_data:
            print(f"\nSuccessfully scraped {len(swaps_data)} swaps")
            
            # Analyze the data
            scraper.analyze_data(swaps_data)
            
            # Save to both CSV and JSON
            scraper.save_to_csv(swaps_data)
            scraper.save_to_json(swaps_data)
            
        else:
            print("No swaps data found")
            
    except Exception as e:
        print(f"Error during scraping: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 