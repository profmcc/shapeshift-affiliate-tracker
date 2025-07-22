#!/usr/bin/env python3
"""
Manual Zapper Wallet Scraper with Human Cloudflare Bypass

This version requires manual human interaction to pass Cloudflare protection,
then automatically extracts the data once the page is loaded.
"""

import asyncio
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from playwright.async_api import async_playwright, Browser, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zapper_scraper_manual.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ManualZapperScraper:
    """Manual scraper that requires human interaction for Cloudflare bypass."""
    
    def __init__(self, headless: bool = False, timeout: int = 120000):
        self.headless = headless  # Always visible for manual interaction
        self.timeout = timeout
        self.data: List[Dict[str, str]] = []
        
    async def setup_browser(self) -> Tuple[Browser, Page]:
        """Initialize browser with human-like configuration."""
        playwright = await async_playwright().start()
        
        # Use realistic browser settings
        browser = await playwright.chromium.launch(
            headless=False,  # Always visible for manual interaction
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        page = await browser.new_page()
        
        # Set realistic viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Add human-like headers
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Remove automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        return browser, page
    
    async def navigate_with_manual_bypass(self, page: Page, url: str) -> bool:
        """Navigate to URL and wait for manual Cloudflare bypass."""
        try:
            logger.info(f"Navigating to: {url}")
            logger.info("⚠️  MANUAL INTERACTION REQUIRED")
            logger.info("1. Complete the Cloudflare challenge manually")
            logger.info("2. Wait for the page to fully load")
            logger.info("3. Ensure you're on the Wallet tab")
            logger.info("4. The scraper will automatically detect when ready")
            
            # Navigate to the page
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            
            # Wait for manual interaction
            logger.info("⏳ Waiting for manual Cloudflare bypass...")
            
            # Wait for either the table to appear or a timeout
            max_wait_time = 300  # 5 minutes for manual interaction
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
                try:
                    # Check for various table selectors
                    table_selectors = [
                        'table[data-testid="wallet-table"]',
                        '.wallet-table',
                        'table',
                        '[role="table"]',
                        '[class*="table"]',
                        '[class*="Table"]',
                        'div[class*="token"]',
                        'div[class*="Token"]'
                    ]
                    
                    for selector in table_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element and await element.is_visible():
                                logger.info(f"✅ Found table with selector: {selector}")
                                return True
                        except:
                            continue
                    
                    # Check if we're still on a Cloudflare page
                    cloudflare_indicators = [
                        'iframe[src*="cloudflare"]',
                        '#challenge-form',
                        '.cf-browser-verification',
                        'div[class*="cf-"]'
                    ]
                    
                    on_cloudflare_page = False
                    for indicator in cloudflare_indicators:
                        try:
                            element = await page.query_selector(indicator)
                            if element and await element.is_visible():
                                on_cloudflare_page = True
                                break
                        except:
                            continue
                    
                    if not on_cloudflare_page:
                        logger.info("✅ Cloudflare challenge appears to be resolved")
                    
                    # Wait a bit before checking again
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Error checking page state: {e}")
                    await asyncio.sleep(2)
            
            logger.error("⏰ Timeout waiting for manual interaction")
            return False
            
        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            return False
    
    async def extract_table_data(self, page: Page) -> List[Dict[str, str]]:
        """Extract all token data from the table."""
        try:
            # Try multiple approaches to find the data
            extraction_methods = [
                self._extract_from_table,
                self._extract_from_divs,
                self._extract_from_list
            ]
            
            for method in extraction_methods:
                try:
                    data = await method(page)
                    if data:
                        logger.info(f"✅ Successfully extracted {len(data)} tokens using {method.__name__}")
                        return data
                except Exception as e:
                    logger.warning(f"Method {method.__name__} failed: {e}")
                    continue
            
            logger.error("❌ All extraction methods failed")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []
    
    async def _extract_from_table(self, page: Page) -> List[Dict[str, str]]:
        """Extract data from traditional table structure."""
        table_selectors = [
            'table[data-testid="wallet-table"]',
            '.wallet-table',
            'table',
            '[role="table"]'
        ]
        
        for selector in table_selectors:
            try:
                table = await page.query_selector(selector)
                if not table:
                    continue
                
                rows = await table.query_selector_all('tr')
                if len(rows) < 2:  # Need at least header + 1 data row
                    continue
                
                data = []
                for i, row in enumerate(rows):
                    if i == 0:  # Skip header
                        continue
                    
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        token = await self._extract_text(cells[0])
                        price = await self._extract_text(cells[1])
                        balance = await self._extract_text(cells[2])
                        value = await self._extract_text(cells[3])
                        
                        if token and token.strip():
                            data.append({
                                'Token': token.strip(),
                                'Price': price.strip() if price else '',
                                'Balance': balance.strip() if balance else '',
                                'Value': value.strip() if value else ''
                            })
                
                if data:
                    return data
                    
            except Exception as e:
                logger.warning(f"Error with table selector {selector}: {e}")
                continue
        
        return []
    
    async def _extract_from_divs(self, page: Page) -> List[Dict[str, str]]:
        """Extract data from div-based layout."""
        # Look for common patterns in modern web apps
        container_selectors = [
            '[class*="token"]',
            '[class*="Token"]',
            '[class*="asset"]',
            '[class*="Asset"]',
            '[class*="portfolio"]',
            '[class*="Portfolio"]'
        ]
        
        for container_selector in container_selectors:
            try:
                containers = await page.query_selector_all(container_selector)
                data = []
                
                for container in containers:
                    try:
                        # Try to extract token info from the container
                        token_elem = await container.query_selector('[class*="name"], [class*="symbol"], [class*="token-name"]')
                        price_elem = await container.query_selector('[class*="price"]')
                        balance_elem = await container.query_selector('[class*="balance"], [class*="amount"]')
                        value_elem = await container.query_selector('[class*="value"], [class*="total"]')
                        
                        if token_elem:
                            token = await self._extract_text(token_elem)
                            price = await self._extract_text(price_elem) if price_elem else ''
                            balance = await self._extract_text(balance_elem) if balance_elem else ''
                            value = await self._extract_text(value_elem) if value_elem else ''
                            
                            if token and token.strip():
                                data.append({
                                    'Token': token.strip(),
                                    'Price': price.strip() if price else '',
                                    'Balance': balance.strip() if balance else '',
                                    'Value': value.strip() if value else ''
                                })
                    except:
                        continue
                
                if data:
                    return data
                    
            except Exception as e:
                logger.warning(f"Error with div selector {container_selector}: {e}")
                continue
        
        return []
    
    async def _extract_from_list(self, page: Page) -> List[Dict[str, str]]:
        """Extract data from list-based layout."""
        list_selectors = [
            '[role="list"]',
            '[class*="list"]',
            '[class*="List"]',
            'ul',
            'ol'
        ]
        
        for list_selector in list_selectors:
            try:
                lists = await page.query_selector_all(list_selector)
                data = []
                
                for list_elem in lists:
                    items = await list_elem.query_selector_all('li, [role="listitem"]')
                    
                    for item in items:
                        try:
                            # Try to extract data from list item
                            token_elem = await item.query_selector('[class*="name"], [class*="symbol"]')
                            price_elem = await item.query_selector('[class*="price"]')
                            balance_elem = await item.query_selector('[class*="balance"]')
                            value_elem = await item.query_selector('[class*="value"]')
                            
                            if token_elem:
                                token = await self._extract_text(token_elem)
                                price = await self._extract_text(price_elem) if price_elem else ''
                                balance = await self._extract_text(balance_elem) if balance_elem else ''
                                value = await self._extract_text(value_elem) if value_elem else ''
                                
                                if token and token.strip():
                                    data.append({
                                        'Token': token.strip(),
                                        'Price': price.strip() if price else '',
                                        'Balance': balance.strip() if balance else '',
                                        'Value': value.strip() if value else ''
                                    })
                        except:
                            continue
                
                if data:
                    return data
                    
            except Exception as e:
                logger.warning(f"Error with list selector {list_selector}: {e}")
                continue
        
        return []
    
    async def _extract_text(self, element) -> str:
        """Extract text content from an element."""
        try:
            text = await element.inner_text()
            return text.strip()
        except:
            return ""
    
    def save_data(self, data: List[Dict[str, str]], output_dir: str = "data") -> Tuple[str, str]:
        """Save extracted data to CSV and JSON files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save as CSV
        csv_filename = f"{output_dir}/zapper_wallet_data_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        # Save as JSON
        json_filename = f"{output_dir}/zapper_wallet_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to: {csv_filename} and {json_filename}")
        return csv_filename, json_filename
    
    async def scrape_wallet_data(self, url: str, output_dir: str = "data") -> Optional[Tuple[str, str]]:
        """Main method to scrape wallet data with manual Cloudflare bypass."""
        browser = None
        try:
            # Setup browser
            browser, page = await self.setup_browser()
            
            # Navigate with manual bypass
            if not await self.navigate_with_manual_bypass(page, url):
                return None
            
            # Extract data
            data = await self.extract_table_data(page)
            
            if not data:
                logger.error("❌ No data extracted")
                return None
            
            # Save data
            return self.save_data(data, output_dir)
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return None
        finally:
            if browser:
                await browser.close()


async def main():
    """Main function to run the manual scraper."""
    url = "https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet"
    
    logger.info("🚀 Starting Manual Zapper Wallet Scraper")
    logger.info("=" * 60)
    
    scraper = ManualZapperScraper()
    result = await scraper.scrape_wallet_data(url)
    
    if result:
        csv_file, json_file = result
        logger.info("=" * 60)
        logger.info("✅ SCRAPING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📁 CSV file: {csv_file}")
        logger.info(f"📁 JSON file: {json_file}")
        
        # Display summary
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"📊 Total tokens extracted: {len(df)}")
            if 'Value' in df.columns:
                df['Value_Numeric'] = pd.to_numeric(df['Value'].str.replace('$', '').str.replace(',', ''), errors='coerce')
                total_value = df['Value_Numeric'].sum()
                logger.info(f"💰 Total portfolio value: ${total_value:,.2f}")
        except Exception as e:
            logger.warning(f"Could not calculate total value: {e}")
    else:
        logger.error("❌ Scraping failed!")


if __name__ == "__main__":
    asyncio.run(main()) 