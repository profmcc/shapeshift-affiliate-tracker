#!/usr/bin/env python3
"""
Chainflip Broker Scraper - Tooltip Focused

Specialized scraper that aggressively extracts full 0x addresses from tooltips
and hover states on the Chainflip broker page.
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


class TooltipFocusedChainflipScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.swaps_data = []
        
    async def scrape_swaps_table(self) -> List[Dict[str, Any]]:
        """Scrape the swaps table with aggressive tooltip extraction."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Keep visible for debugging
            page = await browser.new_page()
            
            # Set viewport for better rendering
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            print(f"Loading page: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Navigate to swaps section
            await self._navigate_to_swaps_section(page)
            
            # Wait for table to load
            await self._wait_for_table(page)
            
            # Load all available data
            await self._load_all_data(page)
            
            # Extract table data with aggressive tooltip extraction
            swaps = await self._extract_table_data_with_tooltips(page)
            
            await browser.close()
            return swaps
    
    async def _navigate_to_swaps_section(self, page: Page):
        """Navigate to the swaps section if needed."""
        try:
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
        """Wait for table to load."""
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
        """Load all available data."""
        try:
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
    
    async def _extract_table_data_with_tooltips(self, page: Page) -> List[Dict[str, Any]]:
        """Extract table data with aggressive tooltip extraction."""
        swaps = []
        
        # Get table rows
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} rows")
        
        if not rows:
            print("No table rows found")
            return swaps
        
        # Get headers
        headers = await self._get_table_headers(page)
        
        for i, row in enumerate(rows):
            try:
                print(f"\nProcessing row {i+1}/{len(rows)}")
                
                # Extract row data with aggressive tooltip extraction
                row_data = await self._extract_row_data_with_tooltips(row, headers, page)
                
                if row_data:
                    swaps.append(row_data)
                    print(f"✅ Row {i+1} processed successfully")
                else:
                    print(f"⚠️ Row {i+1} had no data")
                    
            except Exception as e:
                print(f"❌ Error processing row {i+1}: {e}")
                continue
        
        return swaps
    
    async def _get_table_headers(self, page: Page) -> List[str]:
        """Extract table headers."""
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
    
    async def _extract_row_data_with_tooltips(self, row: ElementHandle, headers: List[str], page: Page) -> Dict[str, Any]:
        """Extract row data with aggressive tooltip extraction."""
        row_data = {}
        
        # Get all cells
        cells = await row.query_selector_all('td, th')
        if len(cells) < 2:
            return {}
        
        for j, cell in enumerate(cells):
            try:
                cell_text = await cell.inner_text()
                column_name = headers[j] if j < len(headers) else f'column_{j}'
                
                print(f"  Processing column '{column_name}': {cell_text[:50]}...")
                
                # Check if this cell contains abbreviated addresses
                if self._contains_abbreviated_address(cell_text):
                    print(f"    Found abbreviated address, extracting tooltip...")
                    
                    # Try multiple tooltip extraction methods
                    tooltip_data = await self._extract_tooltip_data(cell, page)
                    
                    if tooltip_data:
                        row_data[f'{column_name}_full_addresses'] = tooltip_data['full_addresses']
                        row_data[f'{column_name}_display'] = tooltip_data['display']
                        row_data[f'{column_name}_tooltip_method'] = tooltip_data['method']
                        print(f"    ✅ Extracted {len(tooltip_data['full_addresses'])} full addresses")
                    else:
                        row_data[column_name] = cell_text.strip()
                        print(f"    ⚠️ No tooltip found, using display text")
                else:
                    row_data[column_name] = cell_text.strip()
                
            except Exception as e:
                print(f"    ❌ Error extracting cell {j}: {e}")
                continue
        
        return row_data
    
    def _contains_abbreviated_address(self, text: str) -> bool:
        """Check if text contains abbreviated addresses."""
        # Look for patterns like "0x1234...abcd" or "bc1q...abcd"
        patterns = [
            r'0x[a-fA-F0-9]{4}\.\.\.[a-fA-F0-9]{4}',
            r'bc1q[a-zA-Z0-9]{4}\.\.\.[a-zA-Z0-9]{4}',
            r'[13][a-km-zA-HJ-NP-Z1-9]{4}\.\.\.[a-km-zA-HJ-NP-Z1-9]{4}',
            r'[A-Za-z0-9]{4}\.\.\.[A-Za-z0-9]{4}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    async def _extract_tooltip_data(self, element: ElementHandle, page: Page) -> Optional[Dict[str, Any]]:
        """Extract tooltip data using multiple aggressive methods."""
        display_text = await element.inner_text()
        full_addresses = []
        method_used = None
        
        # Method 1: Check all possible tooltip attributes
        tooltip_attrs = [
            'title', 'data-tooltip', 'data-title', 'aria-label', 
            'data-original-title', 'data-toggle', 'data-content'
        ]
        
        for attr in tooltip_attrs:
            try:
                value = await element.get_attribute(attr)
                if value and self._contains_full_address(value):
                    addresses = self._extract_addresses_from_text(value)
                    full_addresses.extend(addresses)
                    method_used = f"attribute_{attr}"
                    print(f"      Found addresses via {attr}: {addresses}")
            except Exception:
                continue
        
        # Method 2: Look for child elements with tooltips
        if not full_addresses:
            tooltip_selectors = [
                '[title*="0x"]', '[title*="bc1q"]', '[title*="1"]', '[title*="3"]',
                '[data-tooltip*="0x"]', '[data-title*="0x"]',
                '.tooltip[title*="0x"]', 'span[title*="0x"]',
                'a[title*="0x"]', 'div[title*="0x"]'
            ]
            
            for selector in tooltip_selectors:
                try:
                    tooltip_elements = await element.query_selector_all(selector)
                    for tooltip_elem in tooltip_elements:
                        title = await tooltip_elem.get_attribute('title')
                        if title and self._contains_full_address(title):
                            addresses = self._extract_addresses_from_text(title)
                            full_addresses.extend(addresses)
                            method_used = f"child_element_{selector}"
                            print(f"      Found addresses via child element {selector}: {addresses}")
                except Exception:
                    continue
        
        # Method 3: Hover and wait for dynamic tooltips
        if not full_addresses:
            try:
                print(f"      Trying hover method...")
                await element.hover()
                await asyncio.sleep(1)  # Wait for tooltip to appear
                
                # Look for various tooltip selectors
                tooltip_selectors = [
                    '.tooltip', '[role="tooltip"]', '.ant-tooltip', '.MuiTooltip-popper',
                    '.tooltip-content', '.tooltip-inner', '[class*="tooltip"]',
                    '.popover', '.popover-content', '.dropdown-menu'
                ]
                
                for selector in tooltip_selectors:
                    try:
                        tooltip = await page.query_selector(selector)
                        if tooltip:
                            tooltip_text = await tooltip.inner_text()
                            if self._contains_full_address(tooltip_text):
                                addresses = self._extract_addresses_from_text(tooltip_text)
                                full_addresses.extend(addresses)
                                method_used = f"hover_{selector}"
                                print(f"      Found addresses via hover {selector}: {addresses}")
                                break
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"      Hover method failed: {e}")
        
        # Method 4: Check for data attributes in parent elements
        if not full_addresses:
            try:
                parent = await element.query_selector('..')
                if parent:
                    for attr in tooltip_attrs:
                        value = await parent.get_attribute(attr)
                        if value and self._contains_full_address(value):
                            addresses = self._extract_addresses_from_text(value)
                            full_addresses.extend(addresses)
                            method_used = f"parent_{attr}"
                            print(f"      Found addresses via parent {attr}: {addresses}")
            except Exception:
                pass
        
        # Remove duplicates and return
        unique_addresses = list(set(full_addresses))
        
        if unique_addresses:
            return {
                'full_addresses': unique_addresses,
                'display': display_text.strip(),
                'method': method_used
            }
        
        return None
    
    def _contains_full_address(self, text: str) -> bool:
        """Check if text contains full addresses."""
        # Look for full address patterns
        patterns = [
            r'0x[a-fA-F0-9]{40}',  # Full Ethereum address
            r'bc1q[a-zA-Z0-9]{39}',  # Full Bitcoin address
            r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Full Bitcoin address
            r'[A-Za-z0-9]{32,44}'  # Other crypto addresses
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _extract_addresses_from_text(self, text: str) -> List[str]:
        """Extract all addresses from text."""
        addresses = []
        
        # Ethereum addresses
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        eth_matches = re.findall(eth_pattern, text)
        addresses.extend(eth_matches)
        
        # Bitcoin addresses
        btc_pattern = r'bc1q[a-zA-Z0-9]{39}'
        btc_matches = re.findall(btc_pattern, text)
        addresses.extend(btc_matches)
        
        # Legacy Bitcoin addresses
        legacy_btc_pattern = r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'
        legacy_btc_matches = re.findall(legacy_btc_pattern, text)
        addresses.extend(legacy_btc_matches)
        
        # Other crypto addresses (32-44 chars)
        other_pattern = r'[A-Za-z0-9]{32,44}'
        other_matches = re.findall(other_pattern, text)
        addresses.extend(other_matches)
        
        return addresses
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """Save scraped data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_swaps_tooltip_focused_{timestamp}.csv"
        
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
            filename = f"chainflip_swaps_tooltip_focused_{timestamp}.json"
        
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
        
        # Count tooltip extraction methods
        tooltip_methods = {}
        total_addresses_extracted = 0
        
        for row in data:
            for key, value in row.items():
                if key.endswith('_tooltip_method') and value:
                    tooltip_methods[value] = tooltip_methods.get(value, 0) + 1
                elif key.endswith('_full_addresses') and value:
                    total_addresses_extracted += len(value)
        
        if tooltip_methods:
            print(f"\nTooltip extraction methods used:")
            for method, count in tooltip_methods.items():
                print(f"  {method}: {count}")
        
        print(f"\nTotal full addresses extracted: {total_addresses_extracted}")
        
        # Show sample data
        if data:
            print(f"\nSample data structure:")
            sample_row = data[0]
            for key, value in sample_row.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items - {value[:3]}...")
                else:
                    print(f"  {key}: {str(value)[:100]}...")


async def main():
    """Main function to run the tooltip-focused scraper."""
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = TooltipFocusedChainflipScraper(broker_url)
    
    print("Starting Tooltip-Focused Chainflip swaps table scraper...")
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