#!/usr/bin/env python3
"""
Chainflip Broker Swaps Table Scraper

Scrapes the swaps table from a Chainflip broker page and extracts full 0x addresses
from tooltips that show abbreviated addresses in the UI.
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd


class ChainflipScraper:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.swaps_data = []
        
    async def scrape_swaps_table(self) -> List[Dict[str, Any]]:
        """Scrape the swaps table from the Chainflip broker page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print(f"Loading page: {self.broker_url}")
            await page.goto(self.broker_url, wait_until="networkidle")
            
            # Wait for the swaps table to load
            await page.wait_for_selector('table', timeout=30000)
            
            # Look for pagination and load more data if available
            await self._load_all_data(page)
            
            # Extract the swaps table
            swaps = await self._extract_swaps_data(page)
            
            await browser.close()
            return swaps
    
    async def _load_all_data(self, page):
        """Load all available data by clicking pagination or load more buttons."""
        try:
            # Look for "Load More" buttons or pagination
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                '[data-testid="load-more"]',
                '.load-more',
                '.pagination button:last-child'
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more_button = await page.query_selector(selector)
                    if load_more_button:
                        print(f"Found load more button with selector: {selector}")
                        while await load_more_button.is_visible():
                            await load_more_button.click()
                            await page.wait_for_timeout(2000)  # Wait for data to load
                            print("Loaded more data...")
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error loading additional data: {e}")
    
    async def _extract_swaps_data(self, page) -> List[Dict[str, Any]]:
        """Extract swaps data from the table, including full addresses from tooltips."""
        swaps = []
        
        # Get all table rows
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} swap rows")
        
        for i, row in enumerate(rows):
            try:
                # Get all cells in the row
                cells = await row.query_selector_all('td')
                if len(cells) < 3:  # Skip rows without enough data
                    continue
                
                swap_data = {}
                
                # Extract data from each cell
                for j, cell in enumerate(cells):
                    cell_text = await cell.inner_text()
                    cell_html = await cell.inner_html()
                    
                    # Check if this cell contains an address (look for abbreviated format)
                    if '0x' in cell_text and len(cell_text) < 42:
                        # This might be an abbreviated address, look for tooltip
                        full_address = await self._get_full_address_from_tooltip(cell)
                        if full_address:
                            swap_data[f'column_{j}_full_address'] = full_address
                            swap_data[f'column_{j}_display'] = cell_text.strip()
                        else:
                            swap_data[f'column_{j}'] = cell_text.strip()
                    else:
                        swap_data[f'column_{j}'] = cell_text.strip()
                
                # Try to identify common columns based on content patterns
                swap_data = self._identify_columns(swap_data)
                
                swaps.append(swap_data)
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1} rows...")
                    
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue
        
        return swaps
    
    async def _get_full_address_from_tooltip(self, element) -> Optional[str]:
        """Extract full address from tooltip or title attribute."""
        try:
            # Check for title attribute
            title = await element.get_attribute('title')
            if title and '0x' in title and len(title) >= 42:
                return title.strip()
            
            # Check for data-tooltip or similar attributes
            tooltip_attrs = ['data-tooltip', 'data-title', 'aria-label']
            for attr in tooltip_attrs:
                value = await element.get_attribute(attr)
                if value and '0x' in value and len(value) >= 42:
                    return value.strip()
            
            # Look for child elements with tooltips
            tooltip_elements = await element.query_selector_all('[title*="0x"], [data-tooltip*="0x"]')
            for tooltip_elem in tooltip_elements:
                title = await tooltip_elem.get_attribute('title')
                if title and '0x' in title and len(title) >= 42:
                    return title.strip()
            
            return None
            
        except Exception as e:
            print(f"Error extracting tooltip: {e}")
            return None
    
    def _identify_columns(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try to identify common column types based on content patterns."""
        identified_data = {}
        
        for key, value in row_data.items():
            if not value:
                continue
                
            # Try to identify column types
            if '0x' in value and len(value) >= 42:
                if 'tx' in key.lower() or 'hash' in key.lower():
                    identified_data['transaction_hash'] = value
                elif 'from' in key.lower() or 'sender' in key.lower():
                    identified_data['from_address'] = value
                elif 'to' in key.lower() or 'recipient' in key.lower():
                    identified_data['to_address'] = value
                else:
                    identified_data['address'] = value
            elif any(char.isdigit() for char in value) and any(char == '.' for char in value):
                # Likely a number/amount
                identified_data['amount'] = value
            elif any(char.isdigit() for char in value) and len(value) < 20:
                # Likely a block number or timestamp
                identified_data['block_number'] = value
            else:
                # Keep original key for unknown columns
                identified_data[key] = value
        
        return identified_data
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """Save scraped data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chainflip_swaps_{timestamp}.csv"
        
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
            filename = f"chainflip_swaps_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(data)} swaps to {filename}")


async def main():
    """Main function to run the scraper."""
    broker_url = "https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
    
    scraper = ChainflipScraper(broker_url)
    
    print("Starting Chainflip swaps table scraper...")
    print(f"Target URL: {broker_url}")
    
    try:
        swaps_data = await scraper.scrape_swaps_table()
        
        if swaps_data:
            print(f"\nSuccessfully scraped {len(swaps_data)} swaps")
            
            # Save to both CSV and JSON
            scraper.save_to_csv(swaps_data)
            scraper.save_to_json(swaps_data)
            
            # Display sample data
            print("\nSample data:")
            for i, swap in enumerate(swaps_data[:3]):
                print(f"\nSwap {i+1}:")
                for key, value in swap.items():
                    print(f"  {key}: {value}")
        else:
            print("No swaps data found")
            
    except Exception as e:
        print(f"Error during scraping: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 